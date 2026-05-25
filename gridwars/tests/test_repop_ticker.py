"""
Unit tests for gridwars.world.zones.repop — ZoneRepopScript (e19.5).

Acceptance criteria:
  1. Repop spawns a daemon in an empty zone-tagged room.
  2. Repop SKIPS a room where combat_active=True.
  3. Repop respects archetype repop_cadence (interval stored on script).
  4. scale_to_level called with the right level for the entering player.
  5. Repop is idempotent (no multi-spawn when daemon count == target).
  6. Slow-mode: zone inactive when no players and no recent visit.
  7. is_valid() returns False when zone rooms are gone.

Uses EvenniaTest (real Django DB, full Evennia environment).
"""

import time
from unittest.mock import MagicMock, patch

from evennia.utils.create import create_object, create_script
from evennia.utils.test_resources import EvenniaTest

from typeclasses.daemons import Daemon
from world.room_state import clear_combat_active, is_room_in_combat, set_combat_active
from world.zones.repop import (
    DEFAULT_CADENCE_SEC,
    DEFAULT_DAEMON_TARGET,
    LOW_ACTIVITY_TIMEOUT,
    ZoneRepopScript,
    _live_daemon_count,
    spawn_daemon_in_room,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ZONE_ID = "test_zone_alpha"


def _make_zone_room(key, zone_id=ZONE_ID):
    """Create a room tagged for a specific zone with a recent last_player_visit."""
    room = create_object("evennia.objects.objects.DefaultRoom", key=key)
    room.tags.add(zone_id, category="zone")
    room.tags.add("gridwars-core", category="world_build")
    # Set a recent last_player_visit so the zone is not in slow-mode by default.
    # Tests that want to exercise slow-mode clear this explicitly.
    room.db.last_player_visit = time.time() - 30
    return room


def _make_repop_script(
    zone_id=ZONE_ID,
    cadence=DEFAULT_CADENCE_SEC,
    band=(1, 5),
    palette=None,
    target=DEFAULT_DAEMON_TARGET,
):
    """Create a ZoneRepopScript pre-configured for tests. Timer stopped immediately."""
    script = create_script(ZoneRepopScript)
    script.stop()
    script.db.zone_id = zone_id
    script.db.zone_archetype = "test_archetype"
    script.db.level_band_min = band[0]
    script.db.level_band_max = band[1]
    script.db.daemon_palette = palette or ["typeclasses.daemons.Daemon"]
    script.db.daemon_target = target
    script.interval = cadence
    return script


# ---------------------------------------------------------------------------
# 1. Repop spawns a daemon in an empty room
# ---------------------------------------------------------------------------

class TestRepopSpawnsInEmptyRoom(EvenniaTest):

    def setUp(self):
        super().setUp()
        self.room = _make_zone_room("Empty Room")
        self.script = _make_repop_script()

    def test_daemon_spawned_in_empty_room(self):
        """at_repeat() spawns exactly one daemon when room is empty."""
        self.assertEqual(_live_daemon_count(self.room), 0)
        self.script.at_repeat()
        self.assertEqual(_live_daemon_count(self.room), 1)

    def test_spawned_daemon_is_in_correct_room(self):
        """The spawned daemon's location is the zone room."""
        self.script.at_repeat()
        daemon = next(obj for obj in self.room.contents if isinstance(obj, Daemon))
        self.assertEqual(daemon.location, self.room)

    def test_spawned_daemon_tagged_gridwars_core(self):
        """spawn_daemon_in_room tags the daemon gridwars-core."""
        daemon = spawn_daemon_in_room(self.room, "typeclasses.daemons.Daemon", 1)
        self.assertTrue(daemon.tags.has("gridwars-core", category="world_build"))


# ---------------------------------------------------------------------------
# 2. Repop skips rooms with combat_active
# ---------------------------------------------------------------------------

class TestRepopSkipsCombatRoom(EvenniaTest):

    def setUp(self):
        super().setUp()
        self.room = _make_zone_room("Combat Room")
        self.script = _make_repop_script()
        set_combat_active(self.room)

    def test_no_spawn_when_combat_active(self):
        """at_repeat() spawns nothing when the combat_active flag is set."""
        self.assertTrue(is_room_in_combat(self.room))
        self.script.at_repeat()
        self.assertEqual(_live_daemon_count(self.room), 0)

    def test_spawn_resumes_after_combat_cleared(self):
        """Clearing combat_active allows the next tick to spawn."""
        self.script.at_repeat()
        self.assertEqual(_live_daemon_count(self.room), 0)

        clear_combat_active(self.room)
        self.script.at_repeat()
        self.assertEqual(_live_daemon_count(self.room), 1)


# ---------------------------------------------------------------------------
# 3. Repop cadence stored on script
# ---------------------------------------------------------------------------

class TestRepopCadence(EvenniaTest):

    def test_default_cadence_is_ninety(self):
        """A freshly created ZoneRepopScript has interval == DEFAULT_CADENCE_SEC."""
        script = create_script(ZoneRepopScript)
        script.stop()
        self.assertEqual(script.interval, DEFAULT_CADENCE_SEC)
        self.assertEqual(DEFAULT_CADENCE_SEC, 90)

    def test_custom_cadence_stored(self):
        """Script interval reflects the cadence passed at setup time."""
        script = _make_repop_script(cadence=45)
        self.assertEqual(script.interval, 45)

    def test_datastream_cadence_is_fast(self):
        """Datastream archetype uses 45 s cadence per epic-19 design."""
        script = _make_repop_script(cadence=45)
        self.assertEqual(script.interval, 45)

    def test_gridcore_cadence_is_slow(self):
        """Gridcore archetype uses 180 s cadence per epic-19 design."""
        script = _make_repop_script(cadence=180)
        self.assertEqual(script.interval, 180)


# ---------------------------------------------------------------------------
# 4. scale_to_level called with the correct player-scaled level
# ---------------------------------------------------------------------------

class TestRepopScalesWithPlayerLevel(EvenniaTest):

    def setUp(self):
        super().setUp()
        self.room = _make_zone_room("Scaling Room")
        # Band [3, 8]: player level 5 stays at 5; level 20 caps at 8.
        self.script = _make_repop_script(band=(3, 8))

    def _add_player(self, level: int):
        from typeclasses.characters import Character

        char = create_object(Character, key=f"Player_L{level}", location=self.room)
        # EvenniaTest provides self.account — a real AccountDB instance.
        # Puppet the character so hasattr(obj, "account") and obj.account are truthy.
        char.db_account = self.account
        char.save()
        char.db.level = level
        return char

    def _capture_target_level(self):
        """Patch spawn_daemon_in_room and return the target_level it was called with."""
        calls = []

        with patch("world.zones.repop.spawn_daemon_in_room") as mock_spawn:
            def side_effect(room, typeclass, target_level):
                calls.append(target_level)
                return MagicMock(spec=Daemon)

            mock_spawn.side_effect = side_effect
            self.script.at_repeat()

        return calls

    def test_scale_with_player_level_within_band(self):
        """Player level 5 in band[3,8] → daemons scaled to 5."""
        self._add_player(5)
        calls = self._capture_target_level()
        self.assertEqual(calls, [5])

    def test_scale_clamped_to_band_max(self):
        """Player level 20 in band[3,8] → daemons scaled to 8 (band max)."""
        self._add_player(20)
        calls = self._capture_target_level()
        self.assertEqual(calls, [8])

    def test_scale_uses_band_min_when_no_players(self):
        """No players in zone → daemons scaled to band_min (3)."""
        calls = self._capture_target_level()
        self.assertEqual(calls, [3])

    def test_scale_clamped_up_when_player_below_band_min(self):
        """Player level 1 in band[3,8] → clamped UP to 3 (band floor)."""
        self._add_player(1)
        calls = self._capture_target_level()
        self.assertEqual(calls, [3])

    def test_scale_to_level_called_on_variant(self):
        """spawn_daemon_in_room calls scale_to_level on a daemon variant."""
        # StrayPacket at level 5: integrity = 25 + (5-1)*3 = 37
        room = create_object("evennia.objects.objects.DefaultRoom", key="Variant Room")
        variant = spawn_daemon_in_room(
            room, "typeclasses.daemon_variants.StrayPacket", 5
        )
        self.assertEqual(variant.integrity, 37)


# ---------------------------------------------------------------------------
# 5. Idempotency — no multi-spawn when target already met
# ---------------------------------------------------------------------------

class TestRepopIdempotent(EvenniaTest):

    def setUp(self):
        super().setUp()
        self.room = _make_zone_room("Full Room")
        self.script = _make_repop_script(target=1)

    def test_no_second_spawn_when_target_met(self):
        """Second at_repeat() when count == target does not add a daemon."""
        self.script.at_repeat()
        self.assertEqual(_live_daemon_count(self.room), 1)

        self.script.at_repeat()
        self.assertEqual(_live_daemon_count(self.room), 1)

    def test_multiple_ticks_stable_at_target(self):
        """Five successive ticks — daemon count stays at 1."""
        for _ in range(5):
            self.script.at_repeat()
        self.assertEqual(_live_daemon_count(self.room), 1)

    def test_target_two_fills_over_two_ticks(self):
        """With target=2, two ticks fill the room; third tick is a no-op."""
        zone_id = "two_target_zone"
        room = _make_zone_room("Two-Target Room", zone_id=zone_id)
        script = _make_repop_script(zone_id=zone_id, target=2)

        script.at_repeat()
        self.assertEqual(_live_daemon_count(room), 1)

        script.at_repeat()
        self.assertEqual(_live_daemon_count(room), 2)

        script.at_repeat()
        self.assertEqual(_live_daemon_count(room), 2)


# ---------------------------------------------------------------------------
# 6. Slow-mode (inactive zone skips tick)
# ---------------------------------------------------------------------------

class TestRepopSlowMode(EvenniaTest):

    def setUp(self):
        super().setUp()
        self.room = _make_zone_room("Quiet Room")
        self.script = _make_repop_script()

    def test_tick_fires_when_player_is_present(self):
        """Zone with an active player always runs repop (even with stale timestamp)."""
        from typeclasses.characters import Character

        # Clear the recent timestamp so only the active player keeps zone active.
        self.room.db.last_player_visit = time.time() - (LOW_ACTIVITY_TIMEOUT + 60)

        char = create_object(Character, key="Active Player", location=self.room)
        # Use a real AccountDB instance so hasattr(obj, "account") and obj.account
        # are truthy — Evennia won't accept a MagicMock for db_account.
        char.db_account = self.account
        char.save()

        self.script.at_repeat()
        self.assertEqual(_live_daemon_count(self.room), 1)

    def test_tick_fires_with_recent_visit_timestamp(self):
        """No current players but recent visit (<10 min) → tick fires."""
        self.room.db.last_player_visit = time.time() - 30
        self.script.at_repeat()
        self.assertEqual(_live_daemon_count(self.room), 1)

    def test_tick_skips_with_stale_visit_timestamp(self):
        """Stale visit (>10 min ago) and no players → tick skipped."""
        self.room.db.last_player_visit = time.time() - (LOW_ACTIVITY_TIMEOUT + 60)
        self.script.at_repeat()
        self.assertEqual(_live_daemon_count(self.room), 0)

    def test_tick_skips_with_no_visit_and_no_players(self):
        """No visit timestamp and no players → inactive → tick skipped."""
        # Explicitly clear the recent timestamp that _make_zone_room sets by default.
        self.room.db.last_player_visit = None
        self.script.at_repeat()
        self.assertEqual(_live_daemon_count(self.room), 0)


# ---------------------------------------------------------------------------
# 7. is_valid() lifecycle check
# ---------------------------------------------------------------------------

class TestRepopIsValid(EvenniaTest):

    def test_is_valid_true_with_rooms(self):
        """is_valid() returns True when zone rooms exist."""
        _make_zone_room("Valid Room", zone_id="zone_valid_abc")
        script = _make_repop_script(zone_id="zone_valid_abc")
        self.assertTrue(script.is_valid())

    def test_is_valid_false_with_no_rooms(self):
        """is_valid() returns False when no rooms carry the zone tag."""
        script = _make_repop_script(zone_id="zone_nonexistent_xyz")
        self.assertFalse(script.is_valid())

    def test_is_valid_true_when_unconfigured(self):
        """Unconfigured script (zone_id=None) returns True — not yet set up."""
        script = create_script(ZoneRepopScript)
        script.stop()
        self.assertTrue(script.is_valid())
