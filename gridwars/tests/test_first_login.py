"""
Unit tests for the first-login routing hook (Epic 16.5).

Acceptance criteria:
  1. First login routes the character to the Uplink Node room.
  2. Second login does NOT re-teleport — character stays at their last location.
  3. Missing Uplink Node (world not yet built) does not raise — fallback is silent.

Uses EvenniaTest (real Django DB, full Evennia environment).
"""

from unittest.mock import patch

from evennia.utils import create
from evennia.utils.test_resources import EvenniaTest

from typeclasses.characters import Character


class FirstLoginTestBase(EvenniaTest):
    """Shared setup: GridWars Character typeclass, a fake Uplink Node room."""

    character_typeclass = Character

    def setUp(self):
        super().setUp()
        # Create a stand-in Uplink Node room and tag it the way build_grid does.
        self.uplink_node = create.create_object(
            "evennia.objects.objects.DefaultRoom",
            key="Uplink Node",
            nohome=True,
        )
        self.uplink_node.tags.add("uplink_node", category="world_build")

        # Ensure has_logged_in_once is unset on char1 (fresh character).
        self.char1.db.has_logged_in_once = None

    def _puppet(self, char):
        """Call at_post_puppet with messages suppressed."""
        with patch("world.messages.render", return_value=""):
            char.at_post_puppet()


class TestFirstLoginRouting(FirstLoginTestBase):
    """1. First login teleports character to the Uplink Node."""

    def test_first_login_moves_to_uplink_node(self):
        """has_logged_in_once is falsy -> character ends up in Uplink Node."""
        self.assertFalse(self.char1.db.has_logged_in_once)
        self._puppet(self.char1)
        self.assertEqual(
            self.char1.location,
            self.uplink_node,
            f"Expected Uplink Node, got: {self.char1.location}",
        )

    def test_first_login_sets_flag(self):
        """After first login, has_logged_in_once is True."""
        self._puppet(self.char1)
        self.assertTrue(self.char1.db.has_logged_in_once)


class TestSubsequentLoginPassthrough(FirstLoginTestBase):
    """2. Second login does not re-teleport."""

    def test_second_login_stays_at_last_location(self):
        """has_logged_in_once is True -> character location is unchanged."""
        # Place character in a room other than Uplink Node.
        self.char1.location = self.room1
        self.char1.db.has_logged_in_once = True

        self._puppet(self.char1)

        self.assertEqual(
            self.char1.location,
            self.room1,
            "Returning player must stay at their last location, not be re-routed.",
        )


class TestMissingUplinkFallback(FirstLoginTestBase):
    """3. Missing Uplink Node does not raise - login is silent."""

    def test_missing_uplink_node_does_not_crash(self):
        """If search_tag returns empty, at_post_puppet completes without raising."""
        self.char1.db.has_logged_in_once = None
        original_location = self.char1.location

        with patch(
            "evennia.utils.search.search_tag", return_value=[]
        ) as mock_search, patch("evennia.utils.logger.log_warn") as mock_warn:
            self._puppet(self.char1)

        # Should have warned.
        mock_warn.assert_called_once()
        # Location is unchanged (no teleport fired).
        self.assertEqual(self.char1.location, original_location)
        # Flag is still set so we do not retry on every subsequent login.
        self.assertTrue(self.char1.db.has_logged_in_once)
