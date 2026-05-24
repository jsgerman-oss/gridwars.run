"""Unit tests for CmdCapture (gridwars/commands/capture.py)."""
from evennia.utils.test_resources import EvenniaCommandTest

from typeclasses.characters import Character
from commands.capture import CmdCapture
from world.ownership import get_owner


class CaptureTestCase(EvenniaCommandTest):
    character_typeclass = Character

    def setUp(self):
        super().setUp()
        # char1 + room1 from EvenniaCommandTest base
        self.char1.faction = "Users"

    def test_capture_unaffiliated_refused(self):
        self.char1.faction = None
        self.call(CmdCapture(), "", caller=self.char1)
        self.assertIsNone(get_owner(self.room1))

    def test_capture_happy_path(self):
        self.call(CmdCapture(), "", caller=self.char1)
        self.assertEqual(get_owner(self.room1), "Users")

    def test_recapture_same_faction_noop(self):
        self.call(CmdCapture(), "", caller=self.char1)
        result = self.call(CmdCapture(), "", caller=self.char1)
        self.assertIn("already held", result)
        self.assertEqual(get_owner(self.room1), "Users")

    def test_cross_faction_overwrite(self):
        self.call(CmdCapture(), "", caller=self.char1)
        self.char2.faction = "Daemons"
        self.char2.location = self.room1
        self.call(CmdCapture(), "", caller=self.char2)
        self.assertEqual(get_owner(self.room1), "Daemons")
