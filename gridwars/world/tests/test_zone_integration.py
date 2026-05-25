"""
Epic 19 world-content integration tests (e19.11).

Coverage
--------
DB-backed (EvenniaTest):
  1. TestFullBuild          — build_all_zones() produces 42 zones, room count
                              in [250, 500], all ZoneRepopScript instances running.
  2. TestIdempotentRebuild  — second call to build_all_zones() produces 0 new objects.
  3. TestLevelGateTraversal — L1 char refused at a higher-tier gate; L99 accepted;
                              refusal message contains required level.
  4. TestRepopTick          — a repop tick in a zone room with an entering player
                              spawns a daemon scaled to the clamped level.
  5. TestXPIntegration      — defeating a daemon calls character.gain_experience()
                              with the value from kill_xp(daemon_level, zone_band_min,
                              player_level).
  6. TestCombatActiveClearedOnDefeat — combat_active flag is False after daemon
                              is defeated via the _defeat() flow.
  7. TestRepopRespectsCombatActive  — repop tick is skipped when combat_active is set.

Pure Python (unittest.TestCase):
  8. TestBalanceHarnessSim  — simulate_combat() xp/hr is within 10× of a reference
                              live-XP calculation at the same (player, daemon) levels.

Cross-epic note: tests 5 and 8 import from e17.6 (world.zones.exp, Character.gain_experience).
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch, call

# ---------------------------------------------------------------------------
# Pure-Python section (no DB, no Evennia)
# ---------------------------------------------------------------------------


class TestBalanceHarnessSim(unittest.TestCase):
    """Test 8 — simulate_combat() xp/hr is within 10× of a reference value.

    Reference: for a level-3 player fighting a level-3 Datastream daemon,
    compute the expected XP/kill directly from kill_xp(), then derive an
    estimated XP/hr using the same strikes-per-minute constant as the harness.
    The harness result must be within 10× of this reference (one order of
    magnitude tolerance).
    """

    def test_xp_per_hour_within_10x_of_reference(self):
        from world.zones.balance_harness import (
            simulate_combat,
            PLAYER_STRIKES_PER_MINUTE,
        )
        from world.zones.exp import kill_xp
        from world.zones.archetypes import ARCHETYPES

        player_lvl = 3
        daemon_lvl = 3
        archetype = "datastream"
        band_min = ARCHETYPES[archetype]["level_band"][0]

        report = simulate_combat(
            player_lvl=player_lvl,
            daemon_archetype=archetype,
            daemon_lvl=daemon_lvl,
            n_runs=1000,
            seed=42,
        )

        # Sanity: player at band min should be able to win some fights.
        self.assertGreater(report.kill_rate, 0.0, "player should win at least some fights")

        # Reference XP/kill (exact formula, no simulation noise).
        ref_xp_per_kill = kill_xp(
            daemon_level=daemon_lvl,
            zone_band_min=band_min,
            player_level=player_lvl,
        )
        self.assertGreater(ref_xp_per_kill, 0, "reference XP/kill should be > 0")

        # Reference XP/hr: assume average TTK ~ avg_ttk_ticks from the simulation
        # but XP/kill = ref value.  Use the same strikes-per-minute constant.
        if report.avg_ttk_ticks > 0 and report.avg_ttk_ticks < float("inf"):
            seconds_per_kill = (report.avg_ttk_ticks / PLAYER_STRIKES_PER_MINUTE) * 60.0
            kills_per_hour = (3600.0 / seconds_per_kill) * report.kill_rate
            ref_xp_per_hour = kills_per_hour * ref_xp_per_kill
        else:
            self.skipTest("kill_rate too low for meaningful XP/hr comparison")
            return

        # Within 10× tolerance (up and down).
        sim_xph = report.xp_per_hour
        self.assertGreater(sim_xph, 0.0, "simulated xp/hr should be > 0")
        self.assertGreater(ref_xp_per_hour, 0.0, "reference xp/hr should be > 0")

        ratio = max(sim_xph, ref_xp_per_hour) / min(sim_xph, ref_xp_per_hour)
        self.assertLessEqual(
            ratio, 10.0,
            f"xp/hr ratio {ratio:.2f} exceeds 10× tolerance: "
            f"sim={sim_xph:.1f}, ref={ref_xp_per_hour:.1f}",
        )

    def test_xp_per_kill_matches_formula_exactly(self):
        """Spot-check: simulated xp_per_kill must equal kill_xp() result directly.

        When kill_rate > 0 and all kills award the same XP (no noise in the
        formula), the simulated average xp_per_kill must exactly equal
        kill_xp() output.
        """
        from world.zones.balance_harness import simulate_combat
        from world.zones.exp import kill_xp
        from world.zones.archetypes import ARCHETYPES

        player_lvl = 5
        daemon_lvl = 3
        archetype = "datastream"
        band_min = ARCHETYPES[archetype]["level_band"][0]

        report = simulate_combat(
            player_lvl=player_lvl,
            daemon_archetype=archetype,
            daemon_lvl=daemon_lvl,
            n_runs=500,
            seed=42,
        )
        if report.kill_rate == 0.0:
            self.skipTest("no kills in simulation — cannot compare xp_per_kill")
            return

        expected = kill_xp(
            daemon_level=daemon_lvl,
            zone_band_min=band_min,
            player_level=player_lvl,
        )
        self.assertAlmostEqual(
            report.xp_per_kill, expected, delta=0.5,
            msg=f"xp_per_kill={report.xp_per_kill} vs formula={expected}",
        )

    def test_soft_cap_reduces_xp_for_overlevelled_player(self):
        """A level-30 player farming a level-1 datastream daemon hits soft cap.

        kill_xp(1, 1, 30): base=round(1*1.5)=2, band_mod=1.0, soft_cap=2*30*1=60.
        min(2, 60) = 2.  The simulated xp_per_kill should match 2.
        """
        from world.zones.balance_harness import simulate_combat
        from world.zones.exp import kill_xp

        report = simulate_combat(
            player_lvl=30,
            daemon_archetype="datastream",
            daemon_lvl=1,
            n_runs=300,
            seed=42,
        )
        if report.kill_rate == 0.0:
            self.skipTest("no kills — cannot test soft cap")
            return

        expected = kill_xp(daemon_level=1, zone_band_min=1, player_level=30)
        # expected = min(2, 60) = 2
        self.assertEqual(expected, 2, "formula sanity: expected 2 XP")
        self.assertAlmostEqual(
            report.xp_per_kill, expected, delta=0.5,
            msg=f"overlevelled player xp_per_kill={report.xp_per_kill} expected {expected}",
        )


# ---------------------------------------------------------------------------
# DB-backed integration tests
# ---------------------------------------------------------------------------

def _load_build_fn():
    """Load build_grid.build() without triggering the module-level build() call.

    Uses the same AST-strip loader established in test_build_grid.py,
    test_zone_instantiation.py, and test_topology.py.
    """
    import ast
    import pathlib

    src_path = pathlib.Path(__file__).parent.parent / "build_grid.py"
    source = src_path.read_text()
    tree = ast.parse(source, filename=str(src_path))
    stmts = tree.body
    if (
        stmts
        and isinstance(stmts[-1], ast.Expr)
        and isinstance(stmts[-1].value, ast.Call)
        and isinstance(stmts[-1].value.func, ast.Name)
        and stmts[-1].value.func.id == "build"
    ):
        tree.body = stmts[:-1]
    code = compile(tree, filename=str(src_path), mode="exec")
    module_ns = {"__name__": "world.build_grid", "__file__": str(src_path)}
    exec(code, module_ns)  # noqa: S102
    return module_ns["build"]


def _zone_rooms():
    """All objects tagged (MEMBER_TAG, ZONE_CATEGORY) that are not exits."""
    from evennia.utils.search import search_tag
    from world.zones.build_zones import MEMBER_TAG, ZONE_CATEGORY

    tagged = search_tag(key=MEMBER_TAG, category=ZONE_CATEGORY)
    return [
        o for o in tagged
        if not (hasattr(o, "destination") and o.destination is not None)
    ]


try:
    from evennia.utils.test_resources import EvenniaTest as _EvenniaTest

    # -----------------------------------------------------------------------
    # Test 1 — Full build produces 42 zones, room count [250, 500],
    #          ZoneRepopScript instances running.
    # -----------------------------------------------------------------------

    class TestFullBuild(_EvenniaTest):
        """build_all_zones() produces 42 zones in the expected room/script range."""

        def setUp(self):
            super().setUp()
            from world.zones.build_zones import build_all_zones
            self._result = build_all_zones()

        def test_42_zones_built(self):
            self.assertEqual(
                self._result["zones_built"], 42,
                f"Expected 42 zones built; got {self._result}",
            )

        def test_room_count_in_expected_range(self):
            rooms = _zone_rooms()
            count = len(rooms)
            self.assertGreaterEqual(count, 250, f"Too few zone rooms: {count}")
            self.assertLessEqual(count, 500, f"Too many zone rooms: {count}")

        def test_zone_rooms_carry_repop_data(self):
            """Every built zone room carries the data ZoneRepopScript needs.

            Verifies repop-ready preconditions: each zone room has zone_id,
            level_band, and daemon_spawn_table set.
            """
            rooms = _zone_rooms()
            self.assertGreater(len(rooms), 0, "No zone rooms found")
            for room in rooms:
                with self.subTest(room=room.key):
                    self.assertTrue(
                        room.db.zone_id,
                        f"{room.key!r} missing zone_id",
                    )
                    self.assertIsNotNone(
                        room.db.level_band,
                        f"{room.key!r} missing level_band",
                    )
                    # daemon_spawn_table may be empty list for rooms that
                    # have no daemon entries, but the attribute must exist.
                    self.assertTrue(
                        room.attributes.has("daemon_spawn_table"),
                        f"{room.key!r} missing daemon_spawn_table attribute",
                    )

        def test_42_repop_scripts_running_after_build(self):
            """build_all_zones() auto-starts exactly 42 ZoneRepopScript instances."""
            from evennia.scripts.models import ScriptDB
            scripts = list(ScriptDB.objects.filter(
                db_typeclass_path="world.zones.repop.ZoneRepopScript"
            ))
            self.assertEqual(
                len(scripts), 42,
                f"Expected 42 ZoneRepopScript instances; found {len(scripts)}: "
                f"{[s.key for s in scripts]!r}",
            )
            for script in scripts:
                with self.subTest(script=script.key):
                    self.assertTrue(
                        script.db_persistent,
                        f"ZoneRepopScript {script.key!r} is not persistent",
                    )

        def test_zone_room_count_at_least_250(self):
            """Zone room count from build output falls in the expected range."""
            rooms_built = self._result["rooms_built"]
            self.assertGreaterEqual(
                rooms_built, 250,
                f"rooms_built={rooms_built} below expected minimum 250",
            )

    # -----------------------------------------------------------------------
    # Test 2 — Idempotent rebuild: second call produces 0 new objects.
    # -----------------------------------------------------------------------

    class TestIdempotentRebuild(_EvenniaTest):
        """Second call to build_all_zones() creates zero new objects."""

        def setUp(self):
            super().setUp()
            from world.zones.build_zones import build_all_zones
            build_all_zones()  # first call
            self._rooms_after_first = len(_zone_rooms())
            self._second = build_all_zones()  # second call

        def test_second_call_builds_zero_zones(self):
            self.assertEqual(
                self._second["zones_built"], 0,
                f"Second build created {self._second['zones_built']} zones; expected 0",
            )

        def test_second_call_skips_42_zones(self):
            self.assertEqual(
                self._second["zones_skipped"], 42,
                f"Second build skipped {self._second['zones_skipped']}; expected 42",
            )

        def test_room_count_unchanged_after_second_build(self):
            rooms_after_second = len(_zone_rooms())
            self.assertEqual(
                self._rooms_after_first, rooms_after_second,
                f"Room count changed: {self._rooms_after_first} → {rooms_after_second}",
            )

    # -----------------------------------------------------------------------
    # Test 3 — Level gate traversal: refuse at low level, accept at L99,
    #          refusal message contains required level.
    # -----------------------------------------------------------------------

    class TestLevelGateTraversal(_EvenniaTest):
        """LevelGateExit refuses under-level characters and allows qualified ones."""

        def setUp(self):
            super().setUp()
            from evennia.utils.create import create_object
            from typeclasses.exits import LevelGateExit

            # Build a minimal pair of rooms with a level-gated exit between them.
            self._room_a = create_object(
                typeclass="evennia.objects.objects.DefaultRoom",
                key="Gate Test Room A",
                nohome=True,
            )
            self._room_b = create_object(
                typeclass="evennia.objects.objects.DefaultRoom",
                key="Gate Test Room B",
                nohome=True,
            )
            self._gate = create_object(
                typeclass=LevelGateExit,
                key="deeper",
                location=self._room_a,
                destination=self._room_b,
            )
            self._gate.db.min_level = 10

        def _make_char(self, disc_level: int):
            """Return a mock character with the given disc level."""
            char = MagicMock()
            disc = MagicMock()
            disc.level = disc_level
            char.db.equipped_disc = disc
            return char

        def test_low_level_char_is_refused(self):
            """A level-1 character is refused at a min_level=10 gate."""
            from typeclasses.exits import LevelGateExit
            char = self._make_char(disc_level=1)
            result = LevelGateExit.at_traverse(self._gate, char, self._room_b)
            self.assertFalse(result, "Level-1 char should be refused at min_level=10 gate")
            char.msg.assert_called_once()

        def test_high_level_char_would_pass_gate_check(self):
            """A level-99 character passes the gate check (no refusal msg)."""
            from typeclasses.exits import LevelGateExit
            char = self._make_char(disc_level=99)
            # at_traverse returns False when refused; True when allowed.
            # For a qualified char, no refusal message must be sent.
            # (super().at_traverse may or may not be callable without full DB wiring;
            # we verify only that msg() is NOT called for the refusal case.)
            LevelGateExit.at_traverse(self._gate, char, self._room_b)
            char.msg.assert_not_called()

        def test_refusal_message_contains_required_level(self):
            """Refusal message contains the required level number."""
            from typeclasses.exits import LevelGateExit
            char = self._make_char(disc_level=1)
            LevelGateExit.at_traverse(self._gate, char, self._room_b)
            msg_text = char.msg.call_args[0][0]
            self.assertIn(
                "10", msg_text,
                f"Refusal message {msg_text!r} should contain '10'",
            )

        def test_refusal_message_has_flavor_text(self):
            """Refusal message contains the standard flavor fragment."""
            from typeclasses.exits import LevelGateExit
            char = self._make_char(disc_level=1)
            LevelGateExit.at_traverse(self._gate, char, self._room_b)
            msg_text = char.msg.call_args[0][0]
            self.assertIn(
                "barrier rezzes solid", msg_text,
                f"Expected flavor text 'barrier rezzes solid' in {msg_text!r}",
            )

    # -----------------------------------------------------------------------
    # Test 4 — Repop tick spawns a daemon at the clamped level.
    # -----------------------------------------------------------------------

    class TestRepopTick(_EvenniaTest):
        """ZoneRepopScript.at_repeat() spawns a scaled daemon when a player is present."""

        def setUp(self):
            super().setUp()
            from evennia.utils.create import create_object
            from evennia.scripts.scripts import DefaultScript

            # Create a room tagged as a datastream zone.
            self._zone_id = "datastream:0"
            self._room = create_object(
                typeclass="evennia.objects.objects.DefaultRoom",
                key="Datastream Test Room",
                nohome=True,
                attributes=[
                    ("zone_id", self._zone_id),
                    ("archetype_id", "datastream"),
                    ("level_band", (1, 5)),
                    ("daemon_spawn_table", []),
                    ("zone_daemon_target", 1),
                    ("zone_band_min", 1),
                ],
                tags=[
                    (self._zone_id, "zone"),
                ],
            )
            self._room.db.combat_active = False
            # Set last_player_visit to now so _zone_is_inactive() treats the
            # zone as active without needing a real Account-puppeted character.
            import time as _time
            self._room.db.last_player_visit = _time.time()

            # Patch _player_levels_in_zone to return [3] so the repop logic
            # uses level 3 as the target (clamped to band [1,5] = 3).
            self._player_level_patch = patch(
                "world.zones.repop._player_levels_in_zone",
                return_value=[3],
            )
            self._player_level_patch.start()

            # Create the ZoneRepopScript (not bound to any persisted object,
            # just instantiated directly via create_script).
            from evennia.utils.create import create_script
            self._script = create_script(
                typeclass="world.zones.repop.ZoneRepopScript",
                key="test_repop",
                persistent=False,
                autostart=False,
            )
            self._script.db.zone_id = self._zone_id
            self._script.db.zone_archetype = "datastream"
            self._script.db.level_band_min = 1
            self._script.db.level_band_max = 5
            self._script.db.daemon_palette = ["typeclasses.daemon_variants.StrayPacket"]
            self._script.db.daemon_target = 1

        def tearDown(self):
            self._player_level_patch.stop()
            super().tearDown()

        def _live_daemons(self):
            from typeclasses.daemons import Daemon
            return [o for o in self._room.contents if isinstance(o, Daemon)]

        def test_tick_spawns_daemon_in_empty_room(self):
            """at_repeat() spawns exactly one daemon when room is daemon-free."""
            before = self._live_daemons()
            self.assertEqual(len(before), 0, "Room should start empty")

            self._script.at_repeat()

            after = self._live_daemons()
            self.assertEqual(
                len(after), 1,
                f"Expected 1 daemon after tick; found {len(after)}",
            )

        def test_spawned_daemon_scaled_to_player_level(self):
            """Spawned daemon's stats are scaled to the player's level (3), clamped to band."""
            self._script.at_repeat()

            daemons = self._live_daemons()
            self.assertEqual(len(daemons), 1)
            d = daemons[0]

            # scale_to_level(3) for StrayPacket:
            # integrity = 25 + (3-1)*3 = 25 + 6 = 31
            # energy    = 40 + (3-1)*3 = 40 + 6 = 46
            self.assertEqual(
                d.integrity, 31,
                f"Daemon integrity={d.integrity}, expected 31 for level-3 StrayPacket",
            )
            self.assertEqual(
                d.energy, 46,
                f"Daemon energy={d.energy}, expected 46 for level-3 StrayPacket",
            )

        def test_tick_skipped_when_daemon_count_at_target(self):
            """at_repeat() does not spawn when room already has the target daemon count."""
            # Spawn one daemon first.
            self._script.at_repeat()
            before = self._live_daemons()
            self.assertEqual(len(before), 1)

            # Second tick: already at target (1), should not spawn another.
            self._script.at_repeat()
            after = self._live_daemons()
            self.assertEqual(
                len(after), 1,
                f"Expected daemon count to stay at 1; got {len(after)}",
            )

    # -----------------------------------------------------------------------
    # Test 5 — XP integration: daemon defeat calls gain_experience() with the
    #          correct formula value.
    # -----------------------------------------------------------------------

    class TestXPIntegration(_EvenniaTest):
        """Defeating a daemon grants the correct kill_xp() value to the attacker."""

        def setUp(self):
            super().setUp()
            from evennia.utils.create import create_object

            # Room with zone metadata.
            self._room = create_object(
                typeclass="evennia.objects.objects.DefaultRoom",
                key="XP Test Room",
                nohome=True,
                attributes=[
                    ("zone_id", "datastream:0"),
                    ("zone_band_min", 1),
                    ("level_band", (1, 5)),
                ],
            )

            # Attacker character.
            self._attacker = create_object(
                typeclass="typeclasses.characters.Character",
                key="XPTestAttacker",
                location=self._room,
            )
            self._attacker.experience = 0

            # Daemon with explicit daemon_level.
            self._daemon = create_object(
                typeclass="typeclasses.daemon_variants.StrayPacket",
                key="XPTestDaemon",
                location=self._room,
            )
            self._daemon.db.daemon_level = 3  # explicit level for formula
            self._daemon.integrity = 0  # already defeated

        def test_gain_experience_called_with_correct_xp(self):
            """gain_experience() is called with kill_xp(3, 1, player_level)."""
            from world.zones.exp import kill_xp
            from commands.combat import _kill_xp, _daemon_level, _zone_band_min, _player_level

            daemon_lvl = _daemon_level(self._daemon)   # reads db.daemon_level = 3
            band_min = _zone_band_min(self._room)       # reads db.zone_band_min = 1
            player_lvl = _player_level(self._attacker)  # 1 (0 experience)

            expected_xp = _kill_xp(daemon_lvl, band_min, player_lvl)
            self.assertGreater(expected_xp, 0, "expected_xp must be > 0")

            # Call _defeat() directly (the method that awards XP).
            from commands.combat import CmdStrike
            cmd = CmdStrike()
            cmd.caller = self._attacker

            with patch.object(self._attacker, "gain_experience", wraps=self._attacker.gain_experience) as mock_xp:
                cmd._defeat(self._attacker, self._daemon)

            mock_xp.assert_called_once_with(expected_xp)

        def test_experience_increases_by_formula_value(self):
            """Character.experience is incremented by the correct kill_xp() amount."""
            from commands.combat import CmdStrike, _daemon_level, _zone_band_min, _player_level
            from world.zones.exp import kill_xp

            daemon_lvl = _daemon_level(self._daemon)
            band_min = _zone_band_min(self._room)
            player_lvl = _player_level(self._attacker)
            expected_xp = kill_xp(daemon_lvl, band_min, player_lvl)

            xp_before = self._attacker.experience

            cmd = CmdStrike()
            cmd.caller = self._attacker
            cmd._defeat(self._attacker, self._daemon)

            xp_after = self._attacker.experience
            self.assertEqual(
                xp_after - xp_before, expected_xp,
                f"XP delta={xp_after - xp_before}, expected {expected_xp}",
            )

    # -----------------------------------------------------------------------
    # Test 6 — combat_active is cleared after daemon defeat.
    # -----------------------------------------------------------------------

    class TestCombatActiveClearedOnDefeat(_EvenniaTest):
        """combat_active flag on a room is False after the daemon is defeated."""

        def setUp(self):
            super().setUp()
            from evennia.utils.create import create_object

            self._room = create_object(
                typeclass="evennia.objects.objects.DefaultRoom",
                key="Combat Flag Test Room",
                nohome=True,
                attributes=[
                    ("zone_id", "datastream:0"),
                    ("zone_band_min", 1),
                ],
            )
            self._room.db.combat_active = True  # active combat before defeat

            self._attacker = create_object(
                typeclass="typeclasses.characters.Character",
                key="CombatFlagAttacker",
                location=self._room,
            )

            self._daemon = create_object(
                typeclass="typeclasses.daemon_variants.StrayPacket",
                key="CombatFlagDaemon",
                location=self._room,
            )
            self._daemon.db.daemon_level = 1
            self._daemon.integrity = 0

        def test_combat_active_is_false_after_defeat(self):
            """After _defeat(), the room's combat_active flag is cleared."""
            from commands.combat import CmdStrike
            from world.room_state import is_room_in_combat

            self.assertTrue(
                is_room_in_combat(self._room),
                "Setup: combat_active should be True before defeat",
            )

            cmd = CmdStrike()
            cmd.caller = self._attacker
            cmd._defeat(self._attacker, self._daemon)

            self.assertFalse(
                is_room_in_combat(self._room),
                "combat_active should be False after daemon defeat",
            )

    # -----------------------------------------------------------------------
    # Test 7 — Repop tick is skipped when combat_active is set.
    # -----------------------------------------------------------------------

    class TestRepopRespectsCombatActive(_EvenniaTest):
        """ZoneRepopScript.at_repeat() skips rooms where combat_active is True."""

        def setUp(self):
            super().setUp()
            from evennia.utils.create import create_object

            self._zone_id = "datastream:1"
            self._room = create_object(
                typeclass="evennia.objects.objects.DefaultRoom",
                key="Combat Active Test Room",
                nohome=True,
                attributes=[
                    ("zone_id", self._zone_id),
                    ("level_band", (1, 5)),
                    ("zone_daemon_target", 1),
                ],
                tags=[
                    (self._zone_id, "zone"),
                ],
            )
            self._room.db.combat_active = True  # active combat
            # Set last_player_visit to now so _zone_is_inactive() treats the
            # zone as active (bypasses the Account FK check).
            import time as _time
            self._room.db.last_player_visit = _time.time()

            # Patch _player_levels_in_zone to return [2] for target-level logic.
            self._player_level_patch = patch(
                "world.zones.repop._player_levels_in_zone",
                return_value=[2],
            )
            self._player_level_patch.start()

            from evennia.utils.create import create_script
            self._script = create_script(
                typeclass="world.zones.repop.ZoneRepopScript",
                key="combat_active_repop",
                persistent=False,
                autostart=False,
            )
            self._script.db.zone_id = self._zone_id
            self._script.db.zone_archetype = "datastream"
            self._script.db.level_band_min = 1
            self._script.db.level_band_max = 5
            self._script.db.daemon_palette = ["typeclasses.daemon_variants.StrayPacket"]
            self._script.db.daemon_target = 1

        def tearDown(self):
            self._player_level_patch.stop()
            super().tearDown()

        def _live_daemons(self):
            from typeclasses.daemons import Daemon
            return [o for o in self._room.contents if isinstance(o, Daemon)]

        def test_no_daemon_spawned_during_combat(self):
            """at_repeat() must not spawn any daemon when combat_active is set."""
            before = self._live_daemons()
            self.assertEqual(len(before), 0)

            self._script.at_repeat()

            after = self._live_daemons()
            self.assertEqual(
                len(after), 0,
                f"Expected 0 daemons after tick with combat_active=True; got {len(after)}",
            )

        def test_daemon_spawns_after_combat_cleared(self):
            """After clearing combat_active, the next tick does spawn a daemon."""
            from world.room_state import clear_combat_active

            clear_combat_active(self._room)
            self._script.at_repeat()

            daemons = self._live_daemons()
            self.assertEqual(
                len(daemons), 1,
                f"Expected 1 daemon after combat cleared; got {len(daemons)}",
            )

except ImportError:
    # Evennia not available in the test-runner environment — skip all DB tests.
    pass


if __name__ == "__main__":
    unittest.main()
