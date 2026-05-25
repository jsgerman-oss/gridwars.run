"""
Unit tests for the starter-disc on-creation logic in Character.

Covers 3 acceptance criteria (e16.4):
  1. New Character gets exactly one disc in contents.
  2. A second, independent Character also gets its own disc.
  3. Re-triggering at_object_creation on an existing Character does NOT
     create a second disc (idempotency via the 'starter-disc' tag).

Uses EvenniaTest (real Django DB, full Evennia environment) with
character_typeclass overridden to GridWars' Character.
"""

from evennia.utils.test_resources import EvenniaTest

from typeclasses.characters import Character
from typeclasses.discs import Disc


class StarterInventoryTestCase(EvenniaTest):
    """Starter disc is created exactly once per character."""

    character_typeclass = Character

    # ------------------------------------------------------------------
    # 1. New Character gets exactly one disc
    # ------------------------------------------------------------------

    def test_new_character_has_one_starter_disc(self):
        """A freshly created Character has exactly one Disc in contents."""
        discs = [obj for obj in self.char1.contents if isinstance(obj, Disc)]
        self.assertEqual(
            len(discs),
            1,
            f"Expected 1 starter disc, found {len(discs)}.",
        )

    # ------------------------------------------------------------------
    # 2. Second Character gets its own independent disc
    # ------------------------------------------------------------------

    def test_second_character_gets_its_own_disc(self):
        """A second Character also receives exactly one disc, separate from char1's."""
        discs1 = [obj for obj in self.char1.contents if isinstance(obj, Disc)]
        discs2 = [obj for obj in self.char2.contents if isinstance(obj, Disc)]
        self.assertEqual(
            len(discs2),
            1,
            f"char2 expected 1 starter disc, found {len(discs2)}.",
        )
        # The two discs must be different objects.
        self.assertIsNot(
            discs1[0],
            discs2[0],
            "char1 and char2 must each have their own distinct disc instance.",
        )

    # ------------------------------------------------------------------
    # 3. Re-triggering at_object_creation is idempotent
    # ------------------------------------------------------------------

    def test_at_object_creation_is_idempotent(self):
        """Calling at_object_creation again does not spawn a second disc."""
        # Verify baseline.
        discs_before = [obj for obj in self.char1.contents if isinstance(obj, Disc)]
        self.assertEqual(len(discs_before), 1, "Precondition: one disc before re-trigger.")

        # Re-trigger.
        self.char1.at_object_creation()

        discs_after = [obj for obj in self.char1.contents if isinstance(obj, Disc)]
        self.assertEqual(
            len(discs_after),
            1,
            f"After re-trigger, expected 1 disc, found {len(discs_after)}. "
            "at_object_creation is not idempotent.",
        )
