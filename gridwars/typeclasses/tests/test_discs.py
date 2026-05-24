"""
Unit tests for gridwars.typeclasses.discs.Disc.

Covers 3 acceptance criteria from Epic 12 ID4 (gridwars_run-x3d.4):
  1. Disc defaults on creation: damage_bonus=5, cooldown_seconds=3, disc_class="standard".
  2. Custom values persist: set damage_bonus=10 via Attribute, verify after retrieval.
  3. Disc is a subclass of DefaultObject: is_typeclass checks pass for both exact and
     non-exact lookups.

Uses EvenniaTest (real Django DB, full Evennia environment).
"""

from evennia.utils import create
from evennia.utils.test_resources import EvenniaTest

from typeclasses.discs import Disc


class TestDiscDefaults(EvenniaTest):
    """Disc created with no overrides has correct attribute defaults."""

    def test_disc_defaults_on_creation(self):
        """damage_bonus=5, cooldown_seconds=3, disc_class='standard' out of the box."""
        disc = create.create_object(Disc, key="test-disc")
        self.assertEqual(disc.damage_bonus, 5)
        self.assertEqual(disc.cooldown_seconds, 3)
        self.assertEqual(disc.disc_class, "standard")


class TestDiscCustomValues(EvenniaTest):
    """Disc custom attribute values persist after being set."""

    def test_disc_custom_values_persist(self):
        """Setting damage_bonus to 10 via Attribute is readable after the fact."""
        disc = create.create_object(Disc, key="custom-disc")
        disc.damage_bonus = 10
        # Re-read from the attribute to confirm persistence (AttributeProperty
        # reads through the Evennia attribute store, so no reload needed).
        self.assertEqual(disc.damage_bonus, 10)
        # Other defaults should remain unchanged.
        self.assertEqual(disc.cooldown_seconds, 3)
        self.assertEqual(disc.disc_class, "standard")


class TestDiscTypeclass(EvenniaTest):
    """Disc reports correct typeclass ancestry."""

    def test_disc_subclass_of_default_object(self):
        """
        Disc passes is_typeclass for its own class (exact) and for
        DefaultObject (non-exact, i.e. inheritance walk).
        """
        disc = create.create_object(Disc, key="lineage-disc")
        self.assertTrue(
            disc.is_typeclass("typeclasses.discs.Disc"),
            "Disc should report its own typeclass (exact match).",
        )
        self.assertTrue(
            disc.is_typeclass(
                "evennia.objects.objects.DefaultObject", exact=False
            ),
            "Disc should pass DefaultObject ancestry check (non-exact).",
        )
