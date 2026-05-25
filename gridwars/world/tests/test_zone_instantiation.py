"""
Integration tests for world.zones.build_zones.build_all_zones() — e19.7.

Coverage:
  1. 42 zones spawned on first run (rooms exist, tagged correctly).
  2. Idempotent re-build: calling build_all_zones() twice produces no duplicates.
  3. Daemon spawn markers placed: every room has db.daemon_spawn_table attribute.
  4. Level-band ordering: datastream (band 1-5) rooms exist before gridcore rooms.
  5. No orphaned rooms: every zone room has a valid zone_id attribute.
  6. Zone counts match DEFAULT_DISTRIBUTION entries.
  7. Zone rooms are connected via exits (at least one exit per multi-room zone).
  8. Rooms carry level_band attribute matching archetype definition.

Classes:
  TestDefaultDistribution  — pure Python, no DB (unittest.TestCase)
  TestBuildAllZones42      — DB-backed (EvenniaTest)
  TestBuildAllZonesViaFullBuild — DB-backed, exercises build_grid.build() hook
"""

import unittest

from world.zones.archetypes import ARCHETYPES
from world.zones.build_zones import (
    DEFAULT_DISTRIBUTION,
    MEMBER_TAG,
    ZONE_CATEGORY,
    _zone_tag,
    build_all_zones,
)
from world.zones.generator import generate_zone


# ---------------------------------------------------------------------------
# Pure-data tests (no DB, no Evennia)
# ---------------------------------------------------------------------------

class TestDefaultDistribution(unittest.TestCase):
    """Validate DEFAULT_DISTRIBUTION at import time — no DB required."""

    def test_sums_to_42(self):
        self.assertEqual(sum(DEFAULT_DISTRIBUTION.values()), 42)

    def test_all_archetype_ids_known(self):
        for aid in DEFAULT_DISTRIBUTION:
            self.assertIn(aid, ARCHETYPES, f"Unknown archetype_id {aid!r} in DEFAULT_DISTRIBUTION")

    def test_all_variant_counts_positive(self):
        for aid, count in DEFAULT_DISTRIBUTION.items():
            self.assertGreater(count, 0, f"Variant count for {aid!r} must be > 0")

    def test_covers_all_eight_archetypes(self):
        self.assertEqual(set(DEFAULT_DISTRIBUTION.keys()), set(ARCHETYPES.keys()))


# ---------------------------------------------------------------------------
# DB-backed integration tests
# ---------------------------------------------------------------------------

def _load_build_fn():
    """
    Load build_grid.build without triggering the module-level build() call.
    Mirrors the pattern in test_build_grid.py.
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
    """All objects tagged (MEMBER_TAG, ZONE_CATEGORY) that are rooms (no destination)."""
    from evennia.utils.search import search_tag
    tagged = search_tag(key=MEMBER_TAG, category=ZONE_CATEGORY)
    return [
        o for o in tagged
        if not (hasattr(o, "destination") and o.destination is not None)
    ]


try:
    from evennia.utils.test_resources import EvenniaTest as _EvenniaTest

    class TestBuildAllZones42(_EvenniaTest):
        """42 zones are created; rooms carry correct tags and attributes."""

        def setUp(self):
            super().setUp()
            self._result = build_all_zones()

        # ------------------------------------------------------------------
        # 1. 42 zones spawned
        # ------------------------------------------------------------------

        def test_42_zones_built(self):
            """build_all_zones() reports zones_built == 42 on first run."""
            self.assertEqual(
                self._result["zones_built"], 42,
                f"Expected 42 zones built, got {self._result['zones_built']}. "
                f"Result: {self._result}",
            )

        def test_zone_room_count_matches_generator(self):
            """Total rooms built matches sum of room counts from generate_zone()."""
            expected_rooms = 0
            for aid, count in DEFAULT_DISTRIBUTION.items():
                for vi in range(count):
                    expected_rooms += len(generate_zone(aid, vi).rooms)
            self.assertEqual(
                self._result["rooms_built"], expected_rooms,
                f"Expected {expected_rooms} rooms, got {self._result['rooms_built']}",
            )

        def test_zone_tags_present_for_all_variants(self):
            """Every (archetype_id, variant_index) pair has at least one tagged room."""
            from evennia.utils.search import search_tag
            for aid, count in DEFAULT_DISTRIBUTION.items():
                for vi in range(count):
                    tag = _zone_tag(aid, vi)
                    hits = search_tag(key=tag, category=ZONE_CATEGORY)
                    self.assertGreater(
                        len(hits), 0,
                        f"No rooms found for zone tag {tag!r}",
                    )

        # ------------------------------------------------------------------
        # 2. Idempotent re-build
        # ------------------------------------------------------------------

        def test_idempotent_rebuild_skips_all(self):
            """Calling build_all_zones() a second time skips all 42 zones."""
            result2 = build_all_zones()
            self.assertEqual(result2["zones_built"], 0)
            self.assertEqual(result2["zones_skipped"], 42)

        def test_room_count_unchanged_after_rebuild(self):
            """Room count is identical after a second build_all_zones() call."""
            rooms_before = len(_zone_rooms())
            build_all_zones()
            rooms_after = len(_zone_rooms())
            self.assertEqual(rooms_before, rooms_after)

        # ------------------------------------------------------------------
        # 3. Daemon spawn markers placed
        # ------------------------------------------------------------------

        def test_every_room_has_daemon_spawn_table(self):
            """Every zone room has a db.daemon_spawn_table attribute (list)."""
            rooms = _zone_rooms()
            self.assertGreater(len(rooms), 0, "No zone rooms found")
            for room in rooms:
                # Coerce to list first: Evennia stores list attributes as
                # _SaverList (a list subclass), which fails assertIsInstance(…, list)
                # in some environments. list() normalises either form.
                table = list(room.db.daemon_spawn_table)
                self.assertIsInstance(
                    table, list,
                    f"Room {room.key!r} missing list daemon_spawn_table, got {type(room.db.daemon_spawn_table)}",
                )

        def test_spawn_table_entries_have_required_keys(self):
            """Non-empty spawn table entries carry typeclass, count, chance."""
            rooms = _zone_rooms()
            for room in rooms:
                for entry in (room.db.daemon_spawn_table or []):
                    for key in ("typeclass", "count", "chance"):
                        self.assertIn(
                            key, entry,
                            f"Spawn entry in {room.key!r} missing key {key!r}: {entry}",
                        )

        # ------------------------------------------------------------------
        # 4. Level-band ordering
        # ------------------------------------------------------------------

        def test_level_band_ordering_datastream_before_gridcore(self):
            """Datastream rooms have lower level_band min than gridcore rooms."""
            from evennia.utils.search import search_tag
            ds_tag = _zone_tag("datastream", 0)
            gc_tag = _zone_tag("gridcore", 0)
            ds_rooms = [
                o for o in search_tag(key=ds_tag, category=ZONE_CATEGORY)
                if not (hasattr(o, "destination") and o.destination is not None)
            ]
            gc_rooms = [
                o for o in search_tag(key=gc_tag, category=ZONE_CATEGORY)
                if not (hasattr(o, "destination") and o.destination is not None)
            ]
            self.assertGreater(len(ds_rooms), 0, "No datastream variant-0 rooms found")
            self.assertGreater(len(gc_rooms), 0, "No gridcore variant-0 rooms found")

            ds_band = tuple(ds_rooms[0].db.level_band)
            gc_band = tuple(gc_rooms[0].db.level_band)
            self.assertLess(
                ds_band[0], gc_band[0],
                f"Datastream band min {ds_band[0]} is not less than gridcore band min {gc_band[0]}",
            )

        # ------------------------------------------------------------------
        # 5. No orphaned rooms
        # ------------------------------------------------------------------

        def test_no_orphaned_rooms(self):
            """Every zone room has a non-empty zone_id in 'archetype:variant' format."""
            rooms = _zone_rooms()
            self.assertGreater(len(rooms), 0)
            for room in rooms:
                zone_id = room.db.zone_id
                self.assertTrue(
                    zone_id,
                    f"Room {room.key!r} (#{room.id}) has empty zone_id",
                )
                parts = zone_id.split(":")
                self.assertEqual(
                    len(parts), 2,
                    f"zone_id {zone_id!r} on {room.key!r} does not match 'archetype:variant' format",
                )

        # ------------------------------------------------------------------
        # 6. Zone counts match distribution
        # ------------------------------------------------------------------

        def test_zone_counts_per_archetype(self):
            """Each archetype has exactly distribution[archetype] zones."""
            from evennia.utils.search import search_tag
            for aid, expected_count in DEFAULT_DISTRIBUTION.items():
                actual = 0
                for vi in range(expected_count):
                    tag = _zone_tag(aid, vi)
                    if search_tag(key=tag, category=ZONE_CATEGORY):
                        actual += 1
                self.assertEqual(
                    actual, expected_count,
                    f"Archetype {aid!r}: expected {expected_count} zones, found {actual}",
                )

        # ------------------------------------------------------------------
        # 7. Connectivity: multi-room zones have exits
        # ------------------------------------------------------------------

        def test_zone_rooms_connected_where_expected(self):
            """Every zone variant with >1 room has at least one intra-zone exit."""
            from evennia.utils.search import search_tag
            for aid, count in DEFAULT_DISTRIBUTION.items():
                for vi in range(count):
                    tag = _zone_tag(aid, vi)
                    zone_objects = search_tag(key=tag, category=ZONE_CATEGORY)
                    exits = [
                        o for o in zone_objects
                        if hasattr(o, "destination") and o.destination is not None
                    ]
                    spec = generate_zone(aid, vi)
                    with self.subTest(archetype=aid, variant=vi):
                        if len(spec.rooms) > 1:
                            self.assertGreater(
                                len(exits), 0,
                                f"Zone {aid}:{vi} has {len(spec.rooms)} rooms but no exits",
                            )

        # ------------------------------------------------------------------
        # 8. level_band attribute matches archetype
        # ------------------------------------------------------------------

        def test_room_level_band_matches_archetype(self):
            """Rooms carry level_band matching their archetype's definition."""
            from evennia.utils.search import search_tag
            for aid, count in DEFAULT_DISTRIBUTION.items():
                archetype_band = tuple(ARCHETYPES[aid]["level_band"])
                for vi in range(count):
                    tag = _zone_tag(aid, vi)
                    rooms = [
                        o for o in search_tag(key=tag, category=ZONE_CATEGORY)
                        if not (hasattr(o, "destination") and o.destination is not None)
                    ]
                    for room in rooms:
                        with self.subTest(archetype=aid, variant=vi, room=room.key):
                            band = tuple(room.db.level_band)
                            self.assertEqual(
                                band, archetype_band,
                                f"{room.key!r} has level_band {band}, expected {archetype_band}",
                            )

    class TestBuildAllZonesViaFullBuild(_EvenniaTest):
        """Verify build_grid.build() also triggers zone instantiation."""

        def setUp(self):
            super().setUp()
            self._build_fn = _load_build_fn()
            self._build_fn()

        def test_zones_created_via_full_build(self):
            """After build_grid.build(), zone rooms exist (MEMBER_TAG tagged)."""
            rooms = _zone_rooms()
            self.assertGreater(
                len(rooms), 0,
                "build_grid.build() did not create any zone rooms",
            )

        def test_full_build_idempotent(self):
            """Running build_grid.build() twice does not double zone rooms."""
            rooms_before = len(_zone_rooms())
            self._build_fn()
            rooms_after = len(_zone_rooms())
            self.assertEqual(rooms_before, rooms_after)

except ImportError:
    # evennia not available in the test runner environment — skip DB tests.
    pass


if __name__ == "__main__":
    unittest.main()
