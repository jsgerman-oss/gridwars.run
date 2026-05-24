"""
Unit tests for gridwars.typeclasses.characters.Character.

Covers:
- Default attribute values on creation
- take_damage() clamping (floor at 0, negative-input guard)
- heal() default and custom cap
- gain_experience() floor at 0
- reset_for_respawn() floor semantics (raise floor / no-free-hp guard)

Uses EvenniaTest (real Django DB, full Evennia environment) with
character_typeclass overridden to GridWars' Character so self.char1
is the class under test.
"""

from evennia.utils.test_resources import EvenniaTest

from typeclasses.characters import Character


class CharacterTestBase(EvenniaTest):
    """Shared base: wire EvenniaTest to use the GridWars Character typeclass."""

    character_typeclass = Character


class TestCharacterDefaults(CharacterTestBase):
    """All attribute defaults are correct on a freshly created Character."""

    def test_defaults_on_creation(self):
        self.assertEqual(self.char1.integrity, 100)
        self.assertEqual(self.char1.energy, 50)
        self.assertEqual(self.char1.experience, 0)
        self.assertIsNone(self.char1.faction)
        self.assertEqual(self.char1.grid_rank, "User")


class TestTakeDamage(CharacterTestBase):
    """take_damage() clamps at zero and ignores negative amounts."""

    def test_take_damage_clamps_at_zero(self):
        """Damage exceeding current integrity floors at 0, not negative."""
        result = self.char1.take_damage(150)
        self.assertEqual(result, 0)
        self.assertEqual(self.char1.integrity, 0)

    def test_take_damage_ignores_negative_input(self):
        """Negative damage is treated as 0 — no accidental healing."""
        original = self.char1.integrity  # 100
        result = self.char1.take_damage(-50)
        self.assertEqual(result, original)
        self.assertEqual(self.char1.integrity, original)


class TestHeal(CharacterTestBase):
    """heal() caps at 100 by default, or at a custom cap."""

    def test_heal_default_cap_100(self):
        """Healing past 100 stops at 100."""
        self.char1.integrity = 50
        self.char1.heal(60)
        self.assertEqual(self.char1.integrity, 100)

    def test_heal_already_at_cap_stays(self):
        """Healing when already at cap leaves integrity unchanged."""
        self.char1.integrity = 100
        self.char1.heal(50)
        self.assertEqual(self.char1.integrity, 100)

    def test_heal_custom_cap(self):
        """A custom cap limits the heal ceiling below the default 100."""
        self.char1.integrity = 50
        result = self.char1.heal(200, cap=80)
        self.assertEqual(result, 80)
        self.assertEqual(self.char1.integrity, 80)


class TestGainExperience(CharacterTestBase):
    """gain_experience() clamps at zero — XP never goes negative."""

    def test_gain_experience_clamps_at_zero(self):
        """Deducting more XP than available floors at 0."""
        self.char1.experience = 0
        result = self.char1.gain_experience(-100)
        self.assertEqual(result, 0)
        self.assertEqual(self.char1.experience, 0)


class TestResetForRespawn(CharacterTestBase):
    """reset_for_respawn() applies a floor without bonus HP."""

    def test_reset_for_respawn_floor(self):
        """Integrity below the floor is raised; faction and experience untouched."""
        self.char1.integrity = 5
        self.char1.faction = "Netrunners"
        self.char1.experience = 999
        self.char1.reset_for_respawn()
        self.assertEqual(self.char1.integrity, 25)
        # Other stats must be untouched
        self.assertEqual(self.char1.faction, "Netrunners")
        self.assertEqual(self.char1.experience, 999)

    def test_reset_for_respawn_no_free_hp(self):
        """Integrity already above the floor is not reduced (no downward clamp)."""
        self.char1.integrity = 80
        self.char1.reset_for_respawn(min_integrity=25)
        self.assertEqual(self.char1.integrity, 80)
