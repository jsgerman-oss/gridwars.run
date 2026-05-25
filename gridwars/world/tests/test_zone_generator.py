"""
Unit tests for world.zones.generator.generate_zone() — e19.2.

Coverage:
  1. Determinism: generate_zone(a, v) called twice returns equal specs
     (24 cases — 8 archetypes × 3 variants).
  2. Structural validity for each of the 24 cases:
       - ZoneSpec fields all present and correctly typed
       - room_count within archetype's room_count_range
       - topology is one of archetype's topology_options
       - every room slug is unique
       - exits reference only known room slugs
       - spawn_table keys match room slugs exactly
       - level_band matches archetype definition
       - repop_cadence matches archetype definition
  3. Edge cases:
       - generate_zone("datastream", 0) baseline smoke test
       - variant_index=0 vs 1 produce *different* specs (different seeds)
       - negative variant_index raises ValueError
       - unknown archetype raises KeyError
  4. Archetype completeness: every archetype in ARCHETYPES has all
     REQUIRED_KEYS (guards e19.1 / e19.2 contract).

No Evennia DB required — generate_zone is a pure function.
Tests use plain unittest.TestCase (no EvenniaTest).
"""

import unittest
from itertools import product

from world.zones.archetypes import ARCHETYPES, REQUIRED_KEYS, get_archetype
from world.zones.generator import ZoneSpec, generate_zone


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ALL_ARCHETYPES = list(ARCHETYPES.keys())
VARIANTS = [0, 1, 2]


def _all_cases():
    """Yield (archetype_id, variant_index) for all 8×3=24 combinations."""
    yield from product(ALL_ARCHETYPES, VARIANTS)


# ---------------------------------------------------------------------------
# 1. Archetype completeness (e19.1 contract guard)
# ---------------------------------------------------------------------------


class TestArchetypeCompleteness(unittest.TestCase):
    """Every archetype in ARCHETYPES must have all REQUIRED_KEYS."""

    def test_all_archetypes_have_required_keys(self):
        for arch_id, arch in ARCHETYPES.items():
            with self.subTest(archetype=arch_id):
                missing = REQUIRED_KEYS - arch.keys()
                self.assertFalse(
                    missing,
                    f"Archetype {arch_id!r} missing keys: {missing}",
                )

    def test_archetype_ids_match_dict_keys(self):
        """The 'archetype_id' field must match the dict key."""
        for key, arch in ARCHETYPES.items():
            with self.subTest(archetype=key):
                self.assertEqual(
                    arch["archetype_id"],
                    key,
                    f"archetype_id mismatch: key={key!r}, value={arch['archetype_id']!r}",
                )

    def test_eight_archetypes_defined(self):
        self.assertEqual(len(ARCHETYPES), 8, f"Expected 8 archetypes, got {len(ARCHETYPES)}")

    def test_level_bands_are_tuples_of_two_ints(self):
        for arch_id, arch in ARCHETYPES.items():
            with self.subTest(archetype=arch_id):
                lb = arch["level_band"]
                self.assertEqual(len(lb), 2, f"{arch_id}: level_band must have 2 elements")
                self.assertLess(lb[0], lb[1], f"{arch_id}: level_band min must be < max")

    def test_room_count_ranges_are_valid(self):
        for arch_id, arch in ARCHETYPES.items():
            with self.subTest(archetype=arch_id):
                rc = arch["room_count_range"]
                self.assertEqual(len(rc), 2)
                self.assertGreaterEqual(rc[0], 1, f"{arch_id}: room_count_range min must be >= 1")
                self.assertLessEqual(rc[0], rc[1], f"{arch_id}: room_count_range min must be <= max")

    def test_topology_options_are_valid_strings(self):
        valid = {"linear", "ring", "branching"}
        for arch_id, arch in ARCHETYPES.items():
            with self.subTest(archetype=arch_id):
                opts = arch["topology_options"]
                self.assertTrue(opts, f"{arch_id}: topology_options must not be empty")
                for opt in opts:
                    self.assertIn(
                        opt, valid,
                        f"{arch_id}: invalid topology option {opt!r}"
                    )

    def test_tiers_are_1_through_3(self):
        for arch_id, arch in ARCHETYPES.items():
            with self.subTest(archetype=arch_id):
                self.assertIn(
                    arch["tier"], {1, 2, 3},
                    f"{arch_id}: tier must be 1, 2, or 3"
                )

    def test_get_archetype_returns_correct_dict(self):
        for arch_id in ALL_ARCHETYPES:
            with self.subTest(archetype=arch_id):
                arch = get_archetype(arch_id)
                self.assertEqual(arch["archetype_id"], arch_id)

    def test_get_archetype_raises_on_unknown(self):
        with self.assertRaises(KeyError):
            get_archetype("not_a_real_archetype")


# ---------------------------------------------------------------------------
# 2. Determinism — 24 cases
# ---------------------------------------------------------------------------


class TestGenerateZoneDeterminism(unittest.TestCase):
    """generate_zone(a, v) must return identical specs on every call."""

    def test_determinism_all_24_cases(self):
        for arch_id, variant in _all_cases():
            with self.subTest(archetype=arch_id, variant=variant):
                spec_a = generate_zone(arch_id, variant)
                spec_b = generate_zone(arch_id, variant)
                self.assertEqual(
                    spec_a.to_dict(),
                    spec_b.to_dict(),
                    f"Non-deterministic output for ({arch_id!r}, {variant})",
                )

    def test_different_variants_produce_different_specs(self):
        """variant 0 and variant 1 must not be equal (different seeds)."""
        for arch_id in ALL_ARCHETYPES:
            with self.subTest(archetype=arch_id):
                spec_0 = generate_zone(arch_id, 0)
                spec_1 = generate_zone(arch_id, 1)
                self.assertNotEqual(
                    spec_0.seed,
                    spec_1.seed,
                    f"{arch_id}: seed must differ between variants",
                )

    def test_different_archetypes_produce_different_specs(self):
        """Two different archetypes at variant 0 must differ."""
        specs = {a: generate_zone(a, 0) for a in ALL_ARCHETYPES}
        zone_ids = [s.zone_id for s in specs.values()]
        self.assertEqual(
            len(zone_ids), len(set(zone_ids)),
            "zone_ids must be unique across archetypes",
        )


# ---------------------------------------------------------------------------
# 3. Structural validity — 24 cases
# ---------------------------------------------------------------------------


class TestGenerateZoneStructure(unittest.TestCase):
    """ZoneSpec fields are present, typed, and logically consistent."""

    def test_zone_id_format(self):
        for arch_id, variant in _all_cases():
            with self.subTest(archetype=arch_id, variant=variant):
                spec = generate_zone(arch_id, variant)
                self.assertEqual(
                    spec.zone_id,
                    f"{arch_id}:{variant}",
                )

    def test_archetype_id_roundtrips(self):
        for arch_id, variant in _all_cases():
            with self.subTest(archetype=arch_id, variant=variant):
                spec = generate_zone(arch_id, variant)
                self.assertEqual(spec.archetype_id, arch_id)

    def test_variant_index_roundtrips(self):
        for arch_id, variant in _all_cases():
            with self.subTest(archetype=arch_id, variant=variant):
                spec = generate_zone(arch_id, variant)
                self.assertEqual(spec.variant_index, variant)

    def test_level_band_matches_archetype(self):
        for arch_id, variant in _all_cases():
            with self.subTest(archetype=arch_id, variant=variant):
                arch = get_archetype(arch_id)
                spec = generate_zone(arch_id, variant)
                self.assertEqual(
                    spec.level_band,
                    tuple(arch["level_band"]),
                )

    def test_repop_cadence_matches_archetype(self):
        for arch_id, variant in _all_cases():
            with self.subTest(archetype=arch_id, variant=variant):
                arch = get_archetype(arch_id)
                spec = generate_zone(arch_id, variant)
                self.assertEqual(
                    spec.repop_cadence,
                    arch["repop_cadence_sec"],
                )

    def test_topology_is_valid_for_archetype(self):
        for arch_id, variant in _all_cases():
            with self.subTest(archetype=arch_id, variant=variant):
                arch = get_archetype(arch_id)
                spec = generate_zone(arch_id, variant)
                self.assertIn(
                    spec.topology,
                    arch["topology_options"],
                    f"Topology {spec.topology!r} not in archetype options",
                )

    def test_room_count_within_range(self):
        for arch_id, variant in _all_cases():
            with self.subTest(archetype=arch_id, variant=variant):
                arch = get_archetype(arch_id)
                spec = generate_zone(arch_id, variant)
                rc_min, rc_max = arch["room_count_range"]
                self.assertGreaterEqual(len(spec.rooms), rc_min)
                self.assertLessEqual(len(spec.rooms), rc_max)

    def test_room_slugs_unique(self):
        for arch_id, variant in _all_cases():
            with self.subTest(archetype=arch_id, variant=variant):
                spec = generate_zone(arch_id, variant)
                slugs = [r.slug for r in spec.rooms]
                self.assertEqual(
                    len(slugs), len(set(slugs)),
                    f"Duplicate room slugs: {slugs}",
                )

    def test_rooms_have_required_fields(self):
        for arch_id, variant in _all_cases():
            with self.subTest(archetype=arch_id, variant=variant):
                spec = generate_zone(arch_id, variant)
                for room in spec.rooms:
                    d = room.to_dict()
                    for fld in ("slug", "key", "flavor_key", "room_index"):
                        self.assertIn(fld, d, f"Room missing field {fld!r}")
                    self.assertIsInstance(d["slug"], str)
                    self.assertIsInstance(d["key"], str)
                    self.assertIsInstance(d["flavor_key"], str)
                    self.assertIsInstance(d["room_index"], int)

    def test_exits_reference_known_room_slugs(self):
        for arch_id, variant in _all_cases():
            with self.subTest(archetype=arch_id, variant=variant):
                spec = generate_zone(arch_id, variant)
                known_slugs = {r.slug for r in spec.rooms}
                for exit_spec in spec.exits:
                    self.assertIn(
                        exit_spec.from_slug, known_slugs,
                        f"Exit from unknown slug {exit_spec.from_slug!r}",
                    )
                    self.assertIn(
                        exit_spec.to_slug, known_slugs,
                        f"Exit to unknown slug {exit_spec.to_slug!r}",
                    )

    def test_exits_have_required_fields(self):
        for arch_id, variant in _all_cases():
            with self.subTest(archetype=arch_id, variant=variant):
                spec = generate_zone(arch_id, variant)
                for exit_spec in spec.exits:
                    d = exit_spec.to_dict()
                    for fld in ("from_slug", "to_slug", "direction"):
                        self.assertIn(fld, d)
                    self.assertIsInstance(d["direction"], str)

    def test_spawn_table_keys_match_room_slugs(self):
        for arch_id, variant in _all_cases():
            with self.subTest(archetype=arch_id, variant=variant):
                spec = generate_zone(arch_id, variant)
                known_slugs = {r.slug for r in spec.rooms}
                self.assertEqual(
                    set(spec.spawn_table.keys()),
                    known_slugs,
                    "spawn_table keys must match room slugs exactly",
                )

    def test_spawn_table_entries_are_valid(self):
        for arch_id, variant in _all_cases():
            with self.subTest(archetype=arch_id, variant=variant):
                arch = get_archetype(arch_id)
                palette = set(arch["daemon_palette"])
                spec = generate_zone(arch_id, variant)
                for slug, entries in spec.spawn_table.items():
                    for entry in entries:
                        d = entry.to_dict()
                        self.assertIn("typeclass", d)
                        self.assertIn("count", d)
                        self.assertIn("chance", d)
                        self.assertIn(
                            d["typeclass"], palette,
                            f"{arch_id}: typeclass {d['typeclass']!r} not in palette",
                        )
                        self.assertGreaterEqual(d["count"], 1)
                        self.assertGreaterEqual(d["chance"], 0.0)
                        self.assertLessEqual(d["chance"], 1.0)

    def test_to_dict_is_fully_serializable(self):
        """to_dict() must return only JSON-compatible types (no tuples, no objects)."""
        import json

        for arch_id, variant in _all_cases():
            with self.subTest(archetype=arch_id, variant=variant):
                spec = generate_zone(arch_id, variant)
                d = spec.to_dict()
                try:
                    json.dumps(d)
                except (TypeError, ValueError) as exc:
                    self.fail(f"to_dict() not JSON-serializable: {exc}")


# ---------------------------------------------------------------------------
# 4. Smoke test + edge cases
# ---------------------------------------------------------------------------


class TestGenerateZoneEdgeCases(unittest.TestCase):
    """Edge cases and input validation."""

    def test_datastream_variant_0_baseline(self):
        """Baseline smoke: generate_zone('datastream', 0) returns a valid ZoneSpec."""
        spec = generate_zone("datastream", 0)
        self.assertIsInstance(spec, ZoneSpec)
        self.assertEqual(spec.archetype_id, "datastream")
        self.assertEqual(spec.variant_index, 0)
        self.assertGreater(len(spec.rooms), 0)

    def test_negative_variant_index_raises(self):
        with self.assertRaises(ValueError):
            generate_zone("datastream", -1)

    def test_unknown_archetype_raises(self):
        with self.assertRaises(KeyError):
            generate_zone("not_an_archetype", 0)

    def test_large_variant_index_deterministic(self):
        """variant_index=999 should be stable across two calls."""
        spec_a = generate_zone("gridcore", 999)
        spec_b = generate_zone("gridcore", 999)
        self.assertEqual(spec_a.to_dict(), spec_b.to_dict())

    def test_rooms_not_empty_for_all_archetypes(self):
        for arch_id in ALL_ARCHETYPES:
            with self.subTest(archetype=arch_id):
                spec = generate_zone(arch_id, 0)
                self.assertGreater(
                    len(spec.rooms), 0,
                    f"{arch_id}: must have at least one room",
                )

    def test_linear_topology_has_chained_exits(self):
        """Linear topology must produce at least room_count-1 forward exits."""
        # Datastream only has "linear" topology, so we can rely on it.
        spec = generate_zone("datastream", 0)
        self.assertEqual(spec.topology, "linear")
        n = len(spec.rooms)
        # Linear topology produces (n-1) forward + (n-1) back exits = 2*(n-1)
        self.assertEqual(len(spec.exits), 2 * (n - 1))

    def test_gridcore_uses_branching_topology(self):
        """Gridcore only has 'branching' in topology_options."""
        arch = get_archetype("gridcore")
        self.assertEqual(arch["topology_options"], ["branching"])
        spec = generate_zone("gridcore", 0)
        self.assertEqual(spec.topology, "branching")


if __name__ == "__main__":
    unittest.main()
