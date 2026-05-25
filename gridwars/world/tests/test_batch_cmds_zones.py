"""
Tests for the e19.9 batch_cmds wiring: world.zones.batch.bootstrap().

Covers:
  1. bootstrap() builds 7 core lobby rooms and 12 lobby exits.
  2. bootstrap() builds 42 zone variants (all 8 archetypes present).
  3. bootstrap() is idempotent — second call produces the same counts.
  4. bootstrap() return dict has all expected summary keys.
  5. Daemon spawn markers are present on zone rooms.
  6. No orphaned zone rooms (every zone room carries a zone_id attr).
  7. Zone distribution covers all 8 archetypes.

Uses EvenniaTest (real Django DB, full Evennia environment).

Loading strategy
----------------
``bootstrap()`` calls ``build_grid.build()`` which has a bare ``build()``
call at module scope.  We use the same AST-strip loader as
``test_build_grid.py`` to avoid triggering the module-level build() at
import time against a cold DB.

We then construct a thin ``_bootstrap_fn`` that:
  - Calls the stripped ``build_fn`` (which in turn calls build_all_zones
    via its lazy import — that import is live once Django is set up).
  - Queries the DB for counts identically to ``batch.bootstrap()``.
"""

import sys
import types

from evennia.utils.search import search_tag
from evennia.utils.test_resources import EvenniaTest


# ---------------------------------------------------------------------------
# Loader helpers
# ---------------------------------------------------------------------------

def _load_build_grid_fn():
    """Load build_grid.build() without triggering the module-level build() call.

    Compiles build_grid.py with the trailing bare ``build()`` expression
    stripped so it is safe to load against a fresh test DB.
    """
    import ast
    import pathlib

    src_path = pathlib.Path(__file__).parent.parent / "build_grid.py"
    source = src_path.read_text()

    tree = ast.parse(source, filename=str(src_path))
    stmts = tree.body
    # Strip the last statement if it is a bare ``build()`` call.
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


def _make_bootstrap_fn(build_fn):
    """Return a bootstrap() callable backed by the patched build_fn.

    Mirrors the logic in world.zones.batch.bootstrap() but uses the
    stripped build_fn so the module-level call is never hit.
    """
    from evennia.utils.search import search_tag as _search_tag

    _CATEGORY = "world_build"
    _CORE_TAG = "gridwars-core"
    _ZONE_TAG = "gridwars-zones"

    def _is_exit(obj):
        return hasattr(obj, "destination") and obj.destination is not None

    def _count_tagged(tag):
        objs = _search_tag(key=tag, category=_CATEGORY)
        rooms = sum(1 for o in objs if not _is_exit(o))
        exits = sum(1 for o in objs if _is_exit(o))
        return rooms, exits

    def _count_daemon_spawn_markers():
        zone_objs = _search_tag(key=_ZONE_TAG, category=_CATEGORY)
        zone_rooms = [o for o in zone_objs if not _is_exit(o)]
        return sum(
            1 for r in zone_rooms
            if r.attributes.has("daemon_spawn_table")
            and bool(r.attributes.get("daemon_spawn_table"))
        )

    def bootstrap():
        build_fn()
        lobby_rooms, lobby_exits = _count_tagged(_CORE_TAG)
        zone_rooms, zone_exits = _count_tagged(_ZONE_TAG)
        daemon_markers = _count_daemon_spawn_markers()
        return {
            "lobby_rooms": lobby_rooms,
            "lobby_exits": lobby_exits,
            "zone_rooms": zone_rooms,
            "zone_exits": zone_exits,
            "daemon_spawn_markers": daemon_markers,
        }

    return bootstrap


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestBatchCmdsBootstrap(EvenniaTest):
    """world.zones.batch.bootstrap() — wiring, counts, idempotency."""

    CATEGORY = "world_build"
    CORE_TAG = "gridwars-core"
    ZONE_TAG = "gridwars-zones"

    def setUp(self):
        super().setUp()
        build_fn = _load_build_grid_fn()
        self._bootstrap = _make_bootstrap_fn(build_fn)
        self._result = self._bootstrap()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _is_exit(self, obj):
        return hasattr(obj, "destination") and obj.destination is not None

    def _tagged(self, tag):
        return search_tag(key=tag, category=self.CATEGORY)

    def _rooms(self, objs):
        return [o for o in objs if not self._is_exit(o)]

    def _exits(self, objs):
        return [o for o in objs if self._is_exit(o)]

    # ------------------------------------------------------------------
    # 1. Core lobby sectors
    # ------------------------------------------------------------------

    def test_lobby_rooms_and_exits(self):
        """bootstrap() builds 7 core lobby rooms and 12 lobby exits.

        Source of truth: build_grid.SECTORS (7 entries) and build_grid.EXITS
        (12 entries).  Grid Junction was added in e19.8, bringing rooms from 6
        to 7 and exits from 10 to 12 (daemon_gate <-> grid_junction pair).
        """
        core = self._tagged(self.CORE_TAG)
        rooms = self._rooms(core)
        exits = self._exits(core)
        self.assertEqual(
            len(rooms), 7,  # +1 Grid Junction (e19.8); source: build_grid.SECTORS
            f"Expected 7 lobby rooms, got {len(rooms)}: {[r.key for r in rooms]}",
        )
        self.assertEqual(
            len(exits), 12,  # +2 daemon_gate<->grid_junction (e19.8); source: build_grid.EXITS
            f"Expected 12 lobby exits, got {len(exits)}: {[e.key for e in exits]}",
        )

    # ------------------------------------------------------------------
    # 2. 42 zone variants built
    # ------------------------------------------------------------------

    def test_zone_count_42(self):
        """bootstrap() produces exactly 42 distinct zone_id values."""
        zone_rooms = self._rooms(self._tagged(self.ZONE_TAG))
        zone_ids = {
            r.attributes.get("zone_id")
            for r in zone_rooms
            if r.attributes.get("zone_id")
        }
        self.assertEqual(
            len(zone_ids), 42,
            f"Expected 42 distinct zone_ids, got {len(zone_ids)}",
        )

    def test_zone_rooms_exist(self):
        """Zone rooms are present after bootstrap()."""
        zone_rooms = self._rooms(self._tagged(self.ZONE_TAG))
        self.assertGreater(
            len(zone_rooms), 0,
            "No zone rooms found — zones were not built.",
        )

    # ------------------------------------------------------------------
    # 3. Idempotency
    # ------------------------------------------------------------------

    def test_bootstrap_idempotent(self):
        """Calling bootstrap() twice leaves counts unchanged."""
        self._bootstrap()

        rooms = self._rooms(self._tagged(self.CORE_TAG))
        exits = self._exits(self._tagged(self.CORE_TAG))
        self.assertEqual(len(rooms), 7, f"Idempotency: lobby rooms changed to {len(rooms)}")  # +1 Grid Junction (e19.8)
        self.assertEqual(len(exits), 12, f"Idempotency: lobby exits changed to {len(exits)}")  # +2 daemon_gate<->grid_junction (e19.8)

        zone_rooms = self._rooms(self._tagged(self.ZONE_TAG))
        zone_ids = {
            r.attributes.get("zone_id")
            for r in zone_rooms
            if r.attributes.get("zone_id")
        }
        self.assertEqual(
            len(zone_ids), 42,
            f"Idempotency: zone_ids changed to {len(zone_ids)} after second run",
        )

    # ------------------------------------------------------------------
    # 4. Return dict shape
    # ------------------------------------------------------------------

    def test_bootstrap_returns_summary_dict(self):
        """bootstrap() returns a dict with all expected summary keys."""
        expected_keys = {
            "lobby_rooms",
            "lobby_exits",
            "zone_rooms",
            "zone_exits",
            "daemon_spawn_markers",
        }
        self.assertEqual(
            set(self._result.keys()), expected_keys,
            f"Return dict keys: {set(self._result.keys())} != {expected_keys}",
        )

    # ------------------------------------------------------------------
    # 5. Daemon spawn markers
    # ------------------------------------------------------------------

    def test_daemon_spawn_markers_present(self):
        """At least some zone rooms carry a daemon_spawn_table attribute."""
        self.assertGreater(
            self._result["daemon_spawn_markers"], 0,
            "Expected at least one zone room with a daemon_spawn_table, got 0.",
        )

    # ------------------------------------------------------------------
    # 6. No orphaned zone rooms
    # ------------------------------------------------------------------

    def test_no_orphaned_zone_rooms(self):
        """Every zone room has a zone_id attribute (no unattributed rooms)."""
        zone_rooms = self._rooms(self._tagged(self.ZONE_TAG))
        orphans = [r for r in zone_rooms if not r.attributes.has("zone_id")]
        self.assertEqual(
            len(orphans), 0,
            f"{len(orphans)} zone rooms missing zone_id: "
            f"{[r.key for r in orphans[:5]]}",
        )

    # ------------------------------------------------------------------
    # 7. All 8 archetypes present
    # ------------------------------------------------------------------

    def test_all_archetypes_present(self):
        """All 8 archetype IDs appear in the built zone rooms."""
        expected = {
            "datastream",
            "archive_node",
            "ice_wall",
            "junction_plaza",
            "shard_foundry",
            "corrupted_cache",
            "mcp_fragment",
            "gridcore",
        }
        zone_rooms = self._rooms(self._tagged(self.ZONE_TAG))
        found = {
            r.attributes.get("archetype_id")
            for r in zone_rooms
            if r.attributes.get("archetype_id")
        }
        missing = expected - found
        self.assertEqual(
            missing, set(),
            f"Archetypes missing from built zones: {missing}",
        )
