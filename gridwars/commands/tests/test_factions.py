"""
Unit tests for the faction command (CmdFaction) and faction registry.

Covers (gridwars_run-62h.2 / Epic 9):
  1. faction list shows all three faction names.
  2. faction list shows "unaffiliated" for a caller with faction=None.
  3. faction list shows "aligned with Users" for a caller already aligned.
  4. faction choose <valid> sets caller.faction to canonical name.
  5. faction choose is case-insensitive (lowercase input → canonical case stored).
  6. faction choose <invalid> errors and lists valid options; caller.faction unchanged.
  7. faction choose refuses re-choose when caller already has a faction.
  8. faction choose broadcasts to other characters in the room.

Uses EvenniaCommandTest (real Django DB, full Evennia environment).
"""

from evennia.utils import create
from evennia.utils.test_resources import EvenniaCommandTest

from commands.factions import CmdFaction
from typeclasses.characters import Character


class FactionCommandTestCase(EvenniaCommandTest):
    """CmdFaction: list and choose paths."""

    character_typeclass = Character

    def setUp(self):
        super().setUp()
        # Ensure callers start unaffiliated.
        self.char1.faction = None
        self.char2.faction = None

    # ------------------------------------------------------------------
    # 1. List — shows all three faction names
    # ------------------------------------------------------------------

    def test_faction_list_shows_all_three(self):
        """faction (no args) prints Users, Programs, and Daemons."""
        result = self.call(CmdFaction(), "", caller=self.char1)
        self.assertIn("Users", result)
        self.assertIn("Programs", result)
        self.assertIn("Daemons", result)

    # ------------------------------------------------------------------
    # 2. List — unaffiliated caller
    # ------------------------------------------------------------------

    def test_faction_list_unaffiliated(self):
        """Caller with faction=None sees 'unaffiliated' in list output."""
        self.char1.faction = None
        result = self.call(CmdFaction(), "", caller=self.char1)
        self.assertIn("unaffiliated", result)

    # ------------------------------------------------------------------
    # 3. List — already aligned caller
    # ------------------------------------------------------------------

    def test_faction_list_aligned(self):
        """Caller with faction='Users' sees alignment notice in list output."""
        self.char1.faction = "Users"
        result = self.call(CmdFaction(), "", caller=self.char1)
        self.assertIn("Users", result)
        # The list output should confirm alignment (not just list the faction).
        self.assertIn("aligned", result)

    # ------------------------------------------------------------------
    # 4. Choose — valid faction sets caller.faction
    # ------------------------------------------------------------------

    def test_faction_choose_valid(self):
        """faction choose Users sets caller.faction = 'Users' and confirms."""
        result = self.call(CmdFaction(), "choose Users", caller=self.char1)
        self.assertEqual(self.char1.faction, "Users")
        self.assertIn("Users", result)

    # ------------------------------------------------------------------
    # 5. Choose — case-insensitive input
    # ------------------------------------------------------------------

    def test_faction_choose_case_insensitive(self):
        """faction choose users (lowercase) stores canonical 'Users'."""
        self.call(CmdFaction(), "choose users", caller=self.char1)
        self.assertEqual(self.char1.faction, "Users")

    # ------------------------------------------------------------------
    # 6. Choose — invalid name errors with valid options
    # ------------------------------------------------------------------

    def test_faction_choose_invalid_name(self):
        """faction choose Bogus errors with valid options listed; faction unchanged."""
        self.char1.faction = None
        result = self.call(CmdFaction(), "choose Bogus", caller=self.char1)
        self.assertIsNone(self.char1.faction)
        # Error message should list at least one valid faction.
        self.assertIn("Users", result)

    # ------------------------------------------------------------------
    # 7. Choose — refuses re-choose
    # ------------------------------------------------------------------

    def test_faction_choose_refuses_re_choose(self):
        """Caller already aligned; faction choose Daemons errors; faction unchanged."""
        self.char1.faction = "Programs"
        result = self.call(CmdFaction(), "choose Daemons", caller=self.char1)
        # Must still be Programs — not changed to Daemons.
        self.assertEqual(self.char1.faction, "Programs")
        # Error must mention admin override.
        self.assertIn("admin", result.lower())

    # ------------------------------------------------------------------
    # 8. Choose — broadcasts to room
    # ------------------------------------------------------------------

    def test_faction_choose_broadcasts(self):
        """Other characters in the room receive the join broadcast.

        We mock char2.msg directly before calling the command so we can
        inspect messages delivered to it via location.msg_contents().
        """
        from unittest.mock import Mock, patch

        self.char1.faction = None
        self.char2.faction = None

        # Ensure char2 is in the same room.
        self.char2.location = self.room1

        # Patch char2.msg so we can track what it receives.
        char2_mock_msg = Mock()
        original_msg = self.char2.msg
        self.char2.msg = char2_mock_msg
        try:
            self.call(CmdFaction(), "choose Users", caller=self.char1)
        finally:
            self.char2.msg = original_msg

        # char1.faction must be set to the chosen faction.
        self.assertEqual(self.char1.faction, "Users")

        # char2 must have received a message containing the faction name.
        all_calls_text = " ".join(
            str(args[0]) if call_args[0] else str(call_args[1])
            for call_args in char2_mock_msg.call_args_list
            for args in [call_args[0]]
        )
        self.assertIn("Users", all_calls_text)
