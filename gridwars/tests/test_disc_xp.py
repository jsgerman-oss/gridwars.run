"""
Unit tests for disc XP + leveling (e17.6).

Covers 5 acceptance criteria:
  1. Fresh disc: L1, xp=0, damage_bonus=5.
  2. Add 100xp → L2, damage_bonus=7, level-up message emitted.
  3. Add 1500xp from L1 → L5 (multiple level-ups in one call), damage_bonus=13.
  4. Cap test: at L5, adding more xp keeps level at 5.
  5. Status command shows Disc L{lvl} ({xp}/{next}xp) line when disc is equipped.

Uses EvenniaTest / EvenniaCommandTest (real Django DB, full Evennia environment).
"""

from unittest.mock import patch

from evennia.utils import create
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from commands.status import CmdStatus
from typeclasses.characters import Character
from typeclasses.discs import Disc, XP_PER_KILL, XP_PER_STRIKE, XP_THRESHOLDS


class TestDiscXPDefaults(EvenniaTest):
    """1. Fresh disc has correct defaults: L1, xp=0, damage_bonus=5."""

    def test_fresh_disc_defaults(self):
        disc = create.create_object(Disc, key="fresh-disc")
        self.assertEqual(disc.level, 1)
        self.assertEqual(disc.xp, 0)
        self.assertEqual(disc.damage_bonus, 5)


class TestDiscLevelUp(EvenniaTest):
    """2. Adding 100xp from L1 → L2, damage_bonus=7, message emitted."""

    def test_gain_100xp_levels_to_2(self):
        disc = create.create_object(Disc, key="xp-disc")
        # Put disc in a room (not a Character) so no level-up message fires.
        disc.location = self.room1

        disc.gain_xp(100)

        self.assertEqual(disc.level, 2)
        self.assertEqual(disc.damage_bonus, 7)

    def test_level_up_message_sent_when_equipped(self):
        """Level-up message sent to holding Character, not to a plain room."""
        disc = create.create_object(Disc, key="lvlmsg-disc")
        # Place disc in char1 (a Character) to simulate equipped state.
        disc.location = self.char1

        received = []
        original_msg = self.char1.msg

        def capture_msg(text, **kwargs):
            received.append(str(text))
            original_msg(text, **kwargs)

        self.char1.msg = capture_msg
        disc.gain_xp(100)

        self.assertEqual(disc.level, 2)
        # At least one message should mention level-up.
        self.assertTrue(
            any("leveled up" in m.lower() or "L2" in m for m in received),
            f"Expected level-up message, got: {received}",
        )


class TestDiscMultipleLevelUps(EvenniaTest):
    """3. Adding 1500xp from L1 in one call → L5, damage_bonus=13."""

    def test_gain_1500xp_from_l1_reaches_l5(self):
        disc = create.create_object(Disc, key="rocket-disc")
        disc.location = self.room1  # not a Character, suppress messages

        disc.gain_xp(1500)

        self.assertEqual(disc.level, 5)
        self.assertEqual(disc.damage_bonus, 13)


class TestDiscLevelCap(EvenniaTest):
    """4. At L5, adding more xp does not increase level beyond 5."""

    def test_level_capped_at_5(self):
        disc = create.create_object(Disc, key="capped-disc")
        disc.location = self.room1

        # Bring to L5 first.
        disc.gain_xp(1500)
        self.assertEqual(disc.level, 5)

        xp_at_l5 = disc.xp
        # Add more XP — level must stay at 5.
        disc.gain_xp(9999)
        self.assertEqual(disc.level, 5, "Level must not exceed 5.")
        self.assertGreater(disc.xp, xp_at_l5, "XP should still accumulate past cap.")


class TestStatusShowsDiscLine(EvenniaCommandTest):
    """5. Status command shows disc level + XP when a disc is equipped."""

    character_typeclass = Character

    def setUp(self):
        super().setUp()
        self.char1.faction = None
        self.char1.integrity = 100
        self.char1.energy = 50
        self.char1.experience = 0
        self.char1.grid_rank = "User"

    def test_status_no_disc_no_disc_line(self):
        """Without an equipped disc, no 'Disc' line appears."""
        self.char1.db.equipped_disc = None
        result = self.call(CmdStatus(), "", caller=self.char1)
        self.assertNotIn("Disc", result)

    def test_status_with_equipped_disc_shows_level_and_xp(self):
        """With an equipped disc, status output contains level + xp progress."""
        disc = create.create_object(Disc, key="status-disc", location=self.char1)
        self.char1.db.equipped_disc = disc

        result = self.call(CmdStatus(), "", caller=self.char1)

        # Should contain the disc name.
        self.assertIn("status-disc", result)
        # Should contain level marker.
        self.assertIn("L1", result)
        # Should contain XP progress (L1 has 0 xp, next threshold is 100).
        self.assertIn("0/100xp", result)
