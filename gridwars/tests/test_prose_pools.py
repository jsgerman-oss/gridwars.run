"""
Smoke tests for gridwars/world/zones/prose_pools.py (e19.6).

Verifies:
  - All 8 archetype pools are present in the PROSE_POOLS registry.
  - Each pool contains the required fields.
  - Each field meets the minimum count specified in the bd acceptance criteria:
      room_name_pool      >= 10 entries
      room_desc_pool      >= 6 entries
      ambient_flavor_pool >= 8 entries
  - All entries are plain strings (no KeyError risk; no format substitution).
  - No entry is empty or whitespace-only.
  - No entry appears verbatim in more than one archetype (cross-archetype duplication).

Uses plain unittest.TestCase — no Evennia DB required; prose_pools.py is pure Python.
"""

import unittest

from world.zones.prose_pools import PROSE_POOLS

EXPECTED_ARCHETYPES = [
    "datastream",
    "archive_node",
    "ice_wall",
    "junction_plaza",
    "shard_foundry",
    "corrupted_cache",
    "mcp_fragment",
    "gridcore",
]

REQUIRED_FIELDS = {
    "room_name_pool": 10,
    "room_desc_pool": 6,
    "ambient_flavor_pool": 8,
}


class TestProsePools(unittest.TestCase):
    """Registry completeness, minimum-count, and quality checks."""

    # ------------------------------------------------------------------
    # Registry structure
    # ------------------------------------------------------------------

    def test_all_archetypes_present(self):
        """Every expected archetype key must appear in PROSE_POOLS."""
        for name in EXPECTED_ARCHETYPES:
            self.assertIn(name, PROSE_POOLS, msg=f"Missing archetype pool: {name!r}")

    def test_no_extra_archetypes(self):
        """PROSE_POOLS must not contain unexpected archetype keys."""
        self.assertEqual(set(PROSE_POOLS.keys()), set(EXPECTED_ARCHETYPES))

    # ------------------------------------------------------------------
    # Required fields present
    # ------------------------------------------------------------------

    def test_required_fields_present(self):
        """Each pool must contain all three required fields."""
        for archetype in EXPECTED_ARCHETYPES:
            pool = PROSE_POOLS[archetype]
            for field in REQUIRED_FIELDS:
                self.assertIn(
                    field,
                    pool,
                    msg=f"Pool {archetype!r} missing field {field!r}",
                )

    # ------------------------------------------------------------------
    # Minimum counts
    # ------------------------------------------------------------------

    def test_minimum_counts(self):
        """Each field in each pool must meet the minimum entry count."""
        for archetype in EXPECTED_ARCHETYPES:
            pool = PROSE_POOLS[archetype]
            for field, minimum in REQUIRED_FIELDS.items():
                entries = pool[field]
                self.assertGreaterEqual(
                    len(entries),
                    minimum,
                    msg=(
                        f"{archetype!r}.{field} has {len(entries)} entries; "
                        f"need at least {minimum}"
                    ),
                )

    # ------------------------------------------------------------------
    # Entry quality
    # ------------------------------------------------------------------

    def test_no_empty_entries(self):
        """No entry in any pool field should be empty or whitespace-only."""
        for archetype in EXPECTED_ARCHETYPES:
            pool = PROSE_POOLS[archetype]
            for field in REQUIRED_FIELDS:
                entries = pool[field]
                for i, entry in enumerate(entries):
                    self.assertIsInstance(
                        entry,
                        str,
                        msg=f"{archetype!r}.{field}[{i}] is not a string: {type(entry)}",
                    )
                    self.assertTrue(
                        entry.strip(),
                        msg=f"{archetype!r}.{field}[{i}] is empty or whitespace",
                    )

    def test_no_cross_archetype_duplication(self):
        """No entry string should appear verbatim in more than one archetype's pools."""
        seen: dict[str, str] = {}  # entry_text -> "archetype.field"
        for archetype, pool in PROSE_POOLS.items():
            for field, entries in pool.items():
                for entry in entries:
                    key = entry.strip()
                    location = f"{archetype}.{field}"
                    self.assertNotIn(
                        key,
                        seen,
                        msg=(
                            f"Duplicate entry found in {location!r} "
                            f"and {seen.get(key)!r}: {key[:80]!r}..."
                        ),
                    )
                    seen[key] = location

    def test_room_names_minimum_length(self):
        """Room names should be at least 2 characters (not trivial stubs)."""
        for archetype in EXPECTED_ARCHETYPES:
            names = PROSE_POOLS[archetype]["room_name_pool"]
            for name in names:
                self.assertGreaterEqual(
                    len(name.strip()),
                    2,
                    msg=f"{archetype!r} room name too short: {name!r}",
                )

    def test_descriptions_have_meaningful_length(self):
        """Room descriptions should each be at least 50 characters."""
        for archetype in EXPECTED_ARCHETYPES:
            descs = PROSE_POOLS[archetype]["room_desc_pool"]
            for i, desc in enumerate(descs):
                self.assertGreaterEqual(
                    len(desc.strip()),
                    50,
                    msg=(
                        f"{archetype!r}.room_desc_pool[{i}] is too short "
                        f"({len(desc.strip())} chars): {desc[:60]!r}"
                    ),
                )

    def test_ambient_lines_have_meaningful_length(self):
        """Ambient flavor lines should each be at least 20 characters."""
        for archetype in EXPECTED_ARCHETYPES:
            lines = PROSE_POOLS[archetype]["ambient_flavor_pool"]
            for i, line in enumerate(lines):
                self.assertGreaterEqual(
                    len(line.strip()),
                    20,
                    msg=(
                        f"{archetype!r}.ambient_flavor_pool[{i}] is too short "
                        f"({len(line.strip())} chars): {line!r}"
                    ),
                )
