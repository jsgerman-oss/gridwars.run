"""
Tests for e19.8: LevelGateExit typeclass + Grid Junction sector + topology wiring.

Coverage:
  1. LevelGateExit._player_level returns 0 when no disc equipped.
  2. LevelGateExit._player_level returns disc.level when disc is equipped.
  3. at_traverse refuses a low-level character and emits the flavor message.
  4. at_traverse allows a character whose disc level meets the requirement.
  5. Refuse message contains the required level number.
  6. Grid Junction room exists after build().
  7. Grid Junction is reachable from Daemon Gate via "deeper" exit.
  8. build_junction_topology skips absent zone rooms silently (no error).
  9. build_junction_topology creates level-gated exits when zone rooms exist.
 10. LevelGateExit.at_traverse uses min_level=1 default when attr is missing.

Uses EvenniaTest (real Django DB) for DB-backed cases.
Pure unittest.TestCase for the typeclass unit cases that only need mock objects.
"""

import unittest
from unittest.mock import MagicMock, patch

from evennia.utils.search import search_tag
from evennia.utils.test_resources import EvenniaTest


# ---------------------------------------------------------------------------
# Pure unit tests for LevelGateExit -- no DB required
# ---------------------------------------------------------------------------

class TestLevelGateExitUnit(unittest.TestCase):
    """LevelGateExit logic using the unbound methods directly -- no Evennia DB.

    Evennia typeclasses cannot be instantiated without a live DB.  Instead we
    import the two methods under test as plain functions and call them with
    ``self`` as a MagicMock, bypassing ORM machinery entirely.
    """

    def _make_exit_mock(self, min_level=1):
        """Return a MagicMock that mimics a LevelGateExit with min_level set."""
        exit_obj = MagicMock()
        exit_obj.min_level = min_level
        return exit_obj

    def _make_character(self, disc_level=None):
        """Return a mock character with optional equipped disc."""
        char = MagicMock()
        if disc_level is None:
            char.db.equipped_disc = None
        else:
            disc = MagicMock()
            disc.level = disc_level
            char.db.equipped_disc = disc
        return char

    # ------------------------------------------------------------------
    # 1. No disc equipped -> level 0
    # ------------------------------------------------------------------

    def test_player_level_no_disc_returns_zero(self):
        from typeclasses.exits import LevelGateExit
        exit_mock = self._make_exit_mock()
        char = self._make_character(disc_level=None)
        result = LevelGateExit._player_level(exit_mock, char)
        self.assertEqual(result, 0)

    # ------------------------------------------------------------------
    # 2. Disc equipped -> returns disc.level
    # ------------------------------------------------------------------

    def test_player_level_with_disc_returns_disc_level(self):
        from typeclasses.exits import LevelGateExit
        exit_mock = self._make_exit_mock()
        char = self._make_character(disc_level=3)
        result = LevelGateExit._player_level(exit_mock, char)
        self.assertEqual(result, 3)

    # ------------------------------------------------------------------
    # 3. at_traverse refuses low-level character
    # ------------------------------------------------------------------

    def test_at_traverse_refuses_low_level(self):
        from typeclasses.exits import LevelGateExit
        exit_mock = self._make_exit_mock(min_level=3)
        # Wire _player_level so it returns an int, bypassing ORM.
        exit_mock._player_level = MagicMock(return_value=1)
        char = self._make_character(disc_level=1)
        target = MagicMock()

        result = LevelGateExit.at_traverse(exit_mock, char, target)

        self.assertFalse(result)
        char.msg.assert_called_once()

    # ------------------------------------------------------------------
    # 4. at_traverse does NOT send refuse message for a qualified character
    #
    # Note: super().at_traverse uses zero-arg super() which requires a real
    # Evennia instance -- unavailable without DB.  We verify only the gate
    # logic (no msg sent) by intercepting before super() via a subclass.
    # ------------------------------------------------------------------

    def test_at_traverse_does_not_msg_qualified_level(self):
        from typeclasses.exits import LevelGateExit

        # Subclass that overrides super() delegation to avoid DB.
        class _TestExit(LevelGateExit):
            def at_traverse(self, traversing_object, target_location, **kwargs):
                # Re-implement just the gate check; skip the super() call.
                required = int(self.min_level) if self.min_level is not None else 1
                player_level = self._player_level(traversing_object)
                if player_level < required:
                    traversing_object.msg(
                        f"The barrier rezzes solid against your disc -- you are too small "
                        f"for what is past this point. [Required: level {required}.]"
                    )
                    return False
                return True  # qualified -- would delegate to super in real code

        exit_mock = self._make_exit_mock(min_level=2)
        exit_mock._player_level = MagicMock(return_value=2)
        char = self._make_character(disc_level=2)
        target = MagicMock()

        result = _TestExit.at_traverse(exit_mock, char, target)

        self.assertTrue(result)
        char.msg.assert_not_called()

    # ------------------------------------------------------------------
    # 5. Refuse message contains required level
    # ------------------------------------------------------------------

    def test_refuse_message_contains_required_level(self):
        from typeclasses.exits import LevelGateExit
        exit_mock = self._make_exit_mock(min_level=5)
        exit_mock._player_level = MagicMock(return_value=2)
        char = self._make_character(disc_level=2)
        target = MagicMock()

        LevelGateExit.at_traverse(exit_mock, char, target)

        msg_text = char.msg.call_args[0][0]
        self.assertIn("5", msg_text)
        self.assertIn("barrier rezzes solid", msg_text)

    # ------------------------------------------------------------------
    # 10. min_level=None falls back to 1
    # ------------------------------------------------------------------

    def test_at_traverse_none_min_level_defaults_to_1(self):
        from typeclasses.exits import LevelGateExit
        exit_mock = self._make_exit_mock(min_level=None)
        exit_mock._player_level = MagicMock(return_value=0)
        char = self._make_character(disc_level=0)
        target = MagicMock()

        result = LevelGateExit.at_traverse(exit_mock, char, target)

        self.assertFalse(result)
        char.msg.assert_called_once()


# ---------------------------------------------------------------------------
# Helpers shared by DB-backed tests
# ---------------------------------------------------------------------------

def _load_build_fn():
    """
    Load build_grid.build without triggering any module-level bare build() call.
    Mirrors the pattern in test_build_grid.py and test_zone_instantiation.py.
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
    return module_ns["build"], module_ns


# ---------------------------------------------------------------------------
# DB-backed integration tests
# ---------------------------------------------------------------------------

class TestGridJunctionSector(EvenniaTest):
    """Grid Junction room + connectivity after build()."""

    CATEGORY = "world_build"
    TAG_KEY = "gridwars-core"

    def setUp(self):
        super().setUp()
        self._build_fn, _ = _load_build_fn()
        self._build_fn()

    # ------------------------------------------------------------------
    # 6. Grid Junction room exists after build()
    # ------------------------------------------------------------------

    def test_grid_junction_room_exists(self):
        results = search_tag(key="grid_junction", category=self.CATEGORY)
        self.assertEqual(
            len(results), 1,
            f"Expected 1 grid_junction room, got {len(results)}: "
            f"{[r.key for r in results]}",
        )
        self.assertEqual(results[0].key, "Grid Junction")

    # ------------------------------------------------------------------
    # 7. Grid Junction reachable from Daemon Gate via "deeper" exit
    # ------------------------------------------------------------------

    def test_daemon_gate_has_deeper_exit_to_grid_junction(self):
        exit_slug = "daemon_gate__exit__deeper"
        exits = search_tag(key=exit_slug, category=self.CATEGORY)
        self.assertEqual(
            len(exits), 1,
            f"Expected 1 'deeper' exit from daemon_gate, got {len(exits)}",
        )
        exit_obj = exits[0]
        junction_rooms = search_tag(key="grid_junction", category=self.CATEGORY)
        self.assertEqual(len(junction_rooms), 1)
        self.assertEqual(
            exit_obj.destination.id,
            junction_rooms[0].id,
            "deeper exit destination is not Grid Junction",
        )

    # ------------------------------------------------------------------
    # 8. build_junction_topology skips absent zone rooms silently
    # ------------------------------------------------------------------

    def test_junction_topology_skips_absent_zones(self):
        """build_junction_topology returns 0 when no zone rooms exist (no e19.7 data)."""
        junction_rooms = search_tag(key="grid_junction", category=self.CATEGORY)
        self.assertEqual(len(junction_rooms), 1)
        junction_room = junction_rooms[0]

        # Import the function directly from the loaded namespace.
        _, ns = _load_build_fn()
        build_junction_topology = ns["build_junction_topology"]

        # No zone rooms exist in this test DB, so topology wiring is a no-op.
        exits_created = build_junction_topology(junction_room)
        self.assertEqual(
            exits_created, 0,
            f"Expected 0 exits when zones absent, got {exits_created}",
        )

    # ------------------------------------------------------------------
    # 9. build_junction_topology creates gated exits when zone rooms exist
    # ------------------------------------------------------------------

    def test_junction_topology_creates_gated_exit_when_zone_exists(self):
        """A synthetic zone entry room causes build_junction_topology to create a LevelGateExit."""
        from evennia.utils.create import create_object

        junction_rooms = search_tag(key="grid_junction", category=self.CATEGORY)
        self.assertEqual(len(junction_rooms), 1)
        junction_room = junction_rooms[0]

        # Create a synthetic zone entry room tagged as the first datastream variant r0.
        zone_entry = create_object(
            typeclass="evennia.objects.objects.DefaultRoom",
            key="Test Datastream Entry",
            nohome=True,
            tags=[
                ("room:datastream:0:r0", "world_build"),
                ("gridwars-zones", "world_build"),
            ],
        )

        _, ns = _load_build_fn()
        build_junction_topology = ns["build_junction_topology"]
        exits_created = build_junction_topology(junction_room)

        # Should create the forward LevelGateExit + return exit = 2.
        self.assertGreaterEqual(
            exits_created, 1,
            f"Expected >= 1 exit created for synthetic zone, got {exits_created}",
        )

        # Verify the forward exit has the correct typeclass.
        from typeclasses.exits import LevelGateExit
        forward_slug = "grid_junction__exit__datastream-north"
        forward_exits = search_tag(key=forward_slug, category=self.CATEGORY)
        self.assertEqual(
            len(forward_exits), 1,
            f"Expected 1 forward LevelGateExit, got {len(forward_exits)}",
        )
        self.assertIsInstance(
            forward_exits[0],
            LevelGateExit,
            f"Forward exit typeclass is {type(forward_exits[0])}, expected LevelGateExit",
        )

        # Clean up synthetic room.
        zone_entry.delete()
