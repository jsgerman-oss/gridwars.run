"""
Unit tests for gridwars.typeclasses.daemon_variants (e19.3).

Acceptance criteria:
  1. All 8 variants are importable.
  2. Each variant instantiates without error (real Django DB via EvenniaTest).
  3. Each variant has the expected base stats at level 1.
  4. scale_to_level(5) produces correct scaled stats.
  5. scale_to_level(25) produces correct scaled stats.
  6. Each variant inherits patrol + sense + engage AI from Daemon (class
     hierarchy check — DaemonPatrol._step_one handles all Daemon subclasses
     because it queries Daemon.objects.all(), which returns subclass instances).
  7. reset_for_respawn() is inherited and works correctly on each variant.
  8. Each variant carries the expected archetype tag.

Uses EvenniaTest (real Django DB, full Evennia environment).
"""

from evennia.utils.create import create_object
from evennia.utils.test_resources import EvenniaTest

from typeclasses.daemons import Daemon
from typeclasses.daemon_variants import (
    ForgeDaemon,
    FragmentGuardian,
    GridcoreElite,
    ICEPicket,
    JunctionRoamer,
    MutatedCacheDaemon,
    ReadOnlySentry,
    StrayPacket,
)

# ---------------------------------------------------------------------------
# Expected stat profiles per variant.
# Format: (integrity_base, energy_base, damage_base,
#           integrity_per_level, energy_per_level, damage_per_level)
# ---------------------------------------------------------------------------
VARIANT_PROFILES = {
    StrayPacket: {
        "archetype_tag": "datastream",
        "integrity_base": 25,
        "energy_base": 40,
        "damage_base": 6,
        "integrity_per_level": 3,
        "energy_per_level": 3,
        "damage_per_level": 1,
    },
    ReadOnlySentry: {
        "archetype_tag": "archive_node",
        "integrity_base": 80,
        "energy_base": 20,
        "damage_base": 5,
        "integrity_per_level": 8,
        "energy_per_level": 1,
        "damage_per_level": 1,
    },
    ICEPicket: {
        "archetype_tag": "ice_wall",
        "integrity_base": 60,
        "energy_base": 30,
        "damage_base": 14,
        "integrity_per_level": 6,
        "energy_per_level": 2,
        "damage_per_level": 2,
    },
    ForgeDaemon: {
        "archetype_tag": "shard_foundry",
        "integrity_base": 50,
        "energy_base": 35,
        "damage_base": 10,
        "integrity_per_level": 5,
        "energy_per_level": 2,
        "damage_per_level": 2,
    },
    MutatedCacheDaemon: {
        "archetype_tag": "corrupted_cache",
        "integrity_base": 40,
        "energy_base": 50,
        "damage_base": 12,
        "integrity_per_level": 4,
        "energy_per_level": 4,
        "damage_per_level": 2,
    },
    FragmentGuardian: {
        "archetype_tag": "mcp_fragment",
        "integrity_base": 90,
        "energy_base": 40,
        "damage_base": 16,
        "integrity_per_level": 10,
        "energy_per_level": 3,
        "damage_per_level": 2,
    },
    GridcoreElite: {
        "archetype_tag": "gridcore",
        "integrity_base": 120,
        "energy_base": 60,
        "damage_base": 20,
        "integrity_per_level": 12,
        "energy_per_level": 5,
        "damage_per_level": 3,
    },
    JunctionRoamer: {
        "archetype_tag": "junction_plaza",
        "integrity_base": 40,
        "energy_base": 30,
        "damage_base": 8,
        "integrity_per_level": 5,
        "energy_per_level": 2,
        "damage_per_level": 1,
    },
}

ALL_VARIANTS = list(VARIANT_PROFILES.keys())


def _expected_stats(profile, level):
    """Return (integrity, energy, damage) expected at target_level."""
    lvl = level - 1
    integrity = profile["integrity_base"] + lvl * profile["integrity_per_level"]
    energy = profile["energy_base"] + lvl * profile["energy_per_level"]
    damage = profile["damage_base"] + lvl * profile["damage_per_level"]
    return integrity, energy, damage


# ---------------------------------------------------------------------------
# Test 1 — Import
# ---------------------------------------------------------------------------

class TestDaemonVariantImports(EvenniaTest):
    """All 8 variant classes are importable and are Daemon subclasses."""

    def test_all_variants_importable(self):
        for cls in ALL_VARIANTS:
            self.assertTrue(
                issubclass(cls, Daemon),
                f"{cls.__name__} must be a subclass of Daemon",
            )

    def test_variant_count(self):
        self.assertEqual(len(ALL_VARIANTS), 8, "Expected exactly 8 daemon variants")


# ---------------------------------------------------------------------------
# Test 2 & 8 — Instantiation + archetype tag
# ---------------------------------------------------------------------------

class TestDaemonVariantInstantiation(EvenniaTest):
    """Each variant instantiates, has faction='Daemons', and carries its archetype tag."""

    def test_each_variant_instantiates(self):
        for cls in ALL_VARIANTS:
            with self.subTest(variant=cls.__name__):
                obj = create_object(cls, key=f"test-{cls.__name__}")
                self.assertIsNotNone(obj, f"{cls.__name__} failed to instantiate")
                self.assertEqual(
                    obj.faction,
                    "Daemons",
                    f"{cls.__name__}.faction must be 'Daemons'",
                )

    def test_each_variant_has_archetype_tag(self):
        for cls, profile in VARIANT_PROFILES.items():
            with self.subTest(variant=cls.__name__):
                obj = create_object(cls, key=f"tag-{cls.__name__}")
                expected_tag = profile["archetype_tag"]
                self.assertTrue(
                    obj.tags.has(expected_tag, category="daemon_archetype"),
                    f"{cls.__name__} missing archetype tag '{expected_tag}'",
                )


# ---------------------------------------------------------------------------
# Test 3 — Level-1 base stats (at_object_creation calls scale_to_level(1))
# ---------------------------------------------------------------------------

class TestDaemonVariantBaseStats(EvenniaTest):
    """Each variant has the declared base stats immediately after creation (level 1)."""

    def test_level1_stats(self):
        for cls, profile in VARIANT_PROFILES.items():
            with self.subTest(variant=cls.__name__):
                obj = create_object(cls, key=f"l1-{cls.__name__}")
                exp_int, exp_eng, exp_dmg = _expected_stats(profile, 1)
                self.assertEqual(
                    obj.integrity,
                    exp_int,
                    f"{cls.__name__}.integrity at L1: expected {exp_int}, got {obj.integrity}",
                )
                self.assertEqual(
                    obj.energy,
                    exp_eng,
                    f"{cls.__name__}.energy at L1: expected {exp_eng}, got {obj.energy}",
                )
                self.assertEqual(
                    obj.db.damage,
                    exp_dmg,
                    f"{cls.__name__}.db.damage at L1: expected {exp_dmg}, got {obj.db.damage}",
                )


# ---------------------------------------------------------------------------
# Test 4 — scale_to_level(5)
# ---------------------------------------------------------------------------

class TestDaemonVariantScaleLevel5(EvenniaTest):
    """scale_to_level(5) writes correct stats for every variant."""

    def test_scale_to_level_5(self):
        for cls, profile in VARIANT_PROFILES.items():
            with self.subTest(variant=cls.__name__):
                obj = create_object(cls, key=f"l5-{cls.__name__}")
                obj.scale_to_level(5)
                exp_int, exp_eng, exp_dmg = _expected_stats(profile, 5)
                self.assertEqual(
                    obj.integrity,
                    exp_int,
                    f"{cls.__name__}.integrity at L5: expected {exp_int}, got {obj.integrity}",
                )
                self.assertEqual(
                    obj.energy,
                    exp_eng,
                    f"{cls.__name__}.energy at L5: expected {exp_eng}, got {obj.energy}",
                )
                self.assertEqual(
                    obj.db.damage,
                    exp_dmg,
                    f"{cls.__name__}.db.damage at L5: expected {exp_dmg}, got {obj.db.damage}",
                )


# ---------------------------------------------------------------------------
# Test 5 — scale_to_level(25)
# ---------------------------------------------------------------------------

class TestDaemonVariantScaleLevel25(EvenniaTest):
    """scale_to_level(25) writes correct stats for every variant."""

    def test_scale_to_level_25(self):
        for cls, profile in VARIANT_PROFILES.items():
            with self.subTest(variant=cls.__name__):
                obj = create_object(cls, key=f"l25-{cls.__name__}")
                obj.scale_to_level(25)
                exp_int, exp_eng, exp_dmg = _expected_stats(profile, 25)
                self.assertEqual(
                    obj.integrity,
                    exp_int,
                    f"{cls.__name__}.integrity at L25: expected {exp_int}, got {obj.integrity}",
                )
                self.assertEqual(
                    obj.energy,
                    exp_eng,
                    f"{cls.__name__}.energy at L25: expected {exp_eng}, got {obj.energy}",
                )
                self.assertEqual(
                    obj.db.damage,
                    exp_dmg,
                    f"{cls.__name__}.db.damage at L25: expected {exp_dmg}, got {obj.db.damage}",
                )


# ---------------------------------------------------------------------------
# Test 6 — AI inheritance (class hierarchy)
# ---------------------------------------------------------------------------

class TestDaemonVariantAIInheritance(EvenniaTest):
    """Each variant inherits patrol+sense+engage from Daemon (MRO check)."""

    def test_variants_are_daemon_subclasses(self):
        """Daemon.objects.all() returns variant instances; DaemonPatrol covers them."""
        for cls in ALL_VARIANTS:
            with self.subTest(variant=cls.__name__):
                obj = create_object(cls, key=f"ai-{cls.__name__}")
                # is_typeclass checks the Daemon MRO path.
                self.assertTrue(
                    obj.is_typeclass("typeclasses.daemons.Daemon", exact=False),
                    f"{cls.__name__} must pass is_typeclass('typeclasses.daemons.Daemon')",
                )

    def test_variants_have_reset_for_respawn(self):
        """reset_for_respawn is inherited from Daemon (or Character)."""
        for cls in ALL_VARIANTS:
            with self.subTest(variant=cls.__name__):
                obj = create_object(cls, key=f"rsp-{cls.__name__}")
                self.assertTrue(
                    callable(getattr(obj, "reset_for_respawn", None)),
                    f"{cls.__name__} must expose reset_for_respawn()",
                )


# ---------------------------------------------------------------------------
# Test 7 — reset_for_respawn on each variant
# ---------------------------------------------------------------------------

class TestDaemonVariantRespawn(EvenniaTest):
    """reset_for_respawn restores integrity to at least min_integrity on all variants."""

    def test_reset_for_respawn_restores_integrity(self):
        for cls in ALL_VARIANTS:
            with self.subTest(variant=cls.__name__):
                obj = create_object(cls, key=f"rsp2-{cls.__name__}")
                # Drive integrity to 0, then respawn.
                obj.integrity = 0
                obj.reset_for_respawn(min_integrity=25)
                self.assertGreaterEqual(
                    obj.integrity,
                    25,
                    f"{cls.__name__}.integrity after respawn must be >= 25, got {obj.integrity}",
                )

    def test_reset_for_respawn_does_not_lower_healthy_integrity(self):
        """When integrity > min_integrity, it is left unchanged."""
        for cls in ALL_VARIANTS:
            with self.subTest(variant=cls.__name__):
                obj = create_object(cls, key=f"rsp3-{cls.__name__}")
                obj.integrity = 75
                obj.reset_for_respawn(min_integrity=25)
                self.assertEqual(
                    obj.integrity,
                    75,
                    f"{cls.__name__} respawn must not lower healthy integrity",
                )


# ---------------------------------------------------------------------------
# Test — scale_to_level guards (edge cases)
# ---------------------------------------------------------------------------

class TestDaemonVariantScaleGuards(EvenniaTest):
    """scale_to_level clamps target_level < 1 to 1 (no negative stats)."""

    def test_scale_to_level_zero_clamped_to_1(self):
        obj = create_object(StrayPacket, key="guard-zero")
        obj.scale_to_level(0)
        profile = VARIANT_PROFILES[StrayPacket]
        exp_int, exp_eng, exp_dmg = _expected_stats(profile, 1)
        self.assertEqual(obj.integrity, exp_int)
        self.assertEqual(obj.energy, exp_eng)
        self.assertEqual(obj.db.damage, exp_dmg)

    def test_scale_to_level_negative_clamped_to_1(self):
        obj = create_object(GridcoreElite, key="guard-neg")
        obj.scale_to_level(-5)
        profile = VARIANT_PROFILES[GridcoreElite]
        exp_int, exp_eng, exp_dmg = _expected_stats(profile, 1)
        self.assertEqual(obj.integrity, exp_int)
        self.assertEqual(obj.energy, exp_eng)
        self.assertEqual(obj.db.damage, exp_dmg)
