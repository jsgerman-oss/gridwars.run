"""
Integration tests for the full new-player onboarding flow (Epic 16).

Covers the end-to-end journey:
  connect → first-login routing → Uplink Node → Welcome Program greeting
  → starter disc in inventory → help entries for every player command.

Test scenarios (7 total):
  1. test_first_login_lands_in_uplink_node
  2. test_subsequent_login_preserves_last_location
  3. test_starter_disc_in_inventory
  4. test_welcome_program_greets_on_entry
  5. test_welcome_program_does_not_greet_npc
  6. test_welcome_program_does_not_greet_objects
  7. test_help_returns_entry_for_every_player_command

Uses EvenniaTest (real Django DB, full Evennia environment).
"""

from unittest.mock import MagicMock, patch

from evennia.utils import create
from evennia.utils.test_resources import EvenniaTest

from typeclasses.characters import Character
from typeclasses.discs import Disc
from typeclasses.welcome_program import UplinkNodeRoom, WelcomeProgram


# ---------------------------------------------------------------------------
# Shared base setup
# ---------------------------------------------------------------------------


class OnboardingBase(EvenniaTest):
    """
    Shared fixture for all onboarding integration tests.

    Builds a minimal world slice:
      - UplinkNodeRoom tagged ``uplink_node / world_build``
      - WelcomeProgram NPC inside the room, tagged ``welcome-program / world_build``
      - char1 set to a fresh-login state (``has_logged_in_once`` unset)
    """

    character_typeclass = Character

    def setUp(self):
        super().setUp()

        # Uplink Node room with the real typeclass used by build_grid.
        self.uplink_node = create.create_object(
            UplinkNodeRoom,
            key="Uplink Node",
            nohome=True,
        )
        self.uplink_node.tags.add("uplink_node", category="world_build")
        self.uplink_node.tags.add("gridwars-core", category="world_build")

        # Welcome Program NPC inside the room.
        self.npc = create.create_object(
            WelcomeProgram,
            key="Welcome Program",
            location=self.uplink_node,
        )
        self.npc.tags.add("welcome-program", category="world_build")

        # Reset char1 to a first-login state.
        self.char1.db.has_logged_in_once = None

    def _puppet(self, char):
        """
        Invoke ``at_post_puppet`` with the world-messages render call suppressed
        so tests do not fail on missing message templates.
        """
        with patch("world.messages.render", return_value=""):
            char.at_post_puppet()


# ---------------------------------------------------------------------------
# Scenario 1 + 2: First-login routing
# ---------------------------------------------------------------------------


class TestFirstLoginRouting(OnboardingBase):
    """
    First login moves a new character to the Uplink Node.
    Subsequent login preserves last location.
    """

    def test_first_login_lands_in_uplink_node(self):
        """
        A character with ``has_logged_in_once`` unset is teleported to the
        Uplink Node when ``at_post_puppet`` fires.
        """
        self.assertFalse(self.char1.db.has_logged_in_once)
        self._puppet(self.char1)
        self.assertEqual(
            self.char1.location,
            self.uplink_node,
            f"First login should land in Uplink Node, "
            f"got: {self.char1.location!r}",
        )

    def test_subsequent_login_preserves_last_location(self):
        """
        A returning character (``has_logged_in_once = True``) stays wherever
        they last were; the Uplink Node routing must not fire again.
        """
        self.char1.location = self.room1
        self.char1.db.has_logged_in_once = True

        self._puppet(self.char1)

        self.assertEqual(
            self.char1.location,
            self.room1,
            "Returning player must not be re-teleported to Uplink Node.",
        )


# ---------------------------------------------------------------------------
# Scenario 3: Starter disc in inventory
# ---------------------------------------------------------------------------


class TestStarterDiscInInventory(OnboardingBase):
    """A newly created character has exactly one disc in contents."""

    def test_starter_disc_in_inventory(self):
        """
        char1 was created with ``Character.at_object_creation``, which spawns
        exactly one starter disc.  No manual setup needed — the EvenniaTest
        harness calls at_object_creation for us.
        """
        discs = [obj for obj in self.char1.contents if isinstance(obj, Disc)]
        self.assertEqual(
            len(discs),
            1,
            f"Expected exactly 1 starter disc in inventory, found {len(discs)}.",
        )


# ---------------------------------------------------------------------------
# Scenario 4, 5, 6: Welcome Program greeting
# ---------------------------------------------------------------------------


class TestWelcomeProgramGreeting(OnboardingBase):
    """
    UplinkNodeRoom.at_object_receive triggers WelcomeProgram.greet for
    player characters and only for player characters.
    """

    def test_welcome_program_greets_on_entry(self):
        """
        Moving a character into the Uplink Node triggers the Welcome Program
        greeting.  We verify via a mock on ``char1.msg`` that the banner is
        delivered.
        """
        # Place char1 outside first so the move is genuine.
        self.char1.location = self.room1

        with patch.object(self.char1, "msg") as mock_msg:
            # Simulate room arrival by calling the hook directly.
            self.uplink_node.at_object_receive(
                self.char1,
                source_location=self.room1,
                move_type="move",
            )

        # msg() should have been called at least once with the tutorial banner.
        mock_msg.assert_called_once()
        banner_text = mock_msg.call_args[0][0]
        # Banner must include key command names from WELCOME_BANNER.
        for keyword in ("status", "scan", "equip", "strike", "jack-in"):
            self.assertIn(
                keyword,
                banner_text,
                f"Tutorial banner missing expected keyword: {keyword!r}",
            )

    def test_welcome_program_does_not_greet_npc(self):
        """
        WelcomeProgram itself subclasses Character; moving it into the room
        must NOT trigger a greeting (avoid NPC greeting NPC).
        """
        other_npc = create.create_object(
            WelcomeProgram,
            key="Another Program",
            location=self.room1,
        )
        with patch.object(other_npc, "msg") as mock_msg:
            self.uplink_node.at_object_receive(
                other_npc,
                source_location=self.room1,
                move_type="move",
            )

        mock_msg.assert_not_called()

    def test_welcome_program_does_not_greet_objects(self):
        """
        A generic non-character object arriving in the Uplink Node must not
        trigger any greeting.
        """
        generic_obj = create.create_object(
            "evennia.objects.objects.DefaultObject",
            key="DataPad",
            location=self.room1,
        )
        # Use mock on the NPC's greet method to detect any mistaken call.
        with patch.object(self.npc, "greet") as mock_greet:
            self.uplink_node.at_object_receive(
                generic_obj,
                source_location=self.room1,
                move_type="move",
            )

        mock_greet.assert_not_called()


# ---------------------------------------------------------------------------
# Scenario 7: Help entries for every player command
# ---------------------------------------------------------------------------


# Canonical list of GridWars player commands that must have help entries.
# Derived from the HELP_ENTRY_DICTS in world/help_entries.py (e16.6 / e18.2).
PLAYER_COMMANDS = [
    "status",
    "scan",
    "strike",
    "challenge",
    "equip",
    "inventory",
    "faction",
    "north",
    "south",
    "east",
    "west",
    "look",
    "say",
    "pose",
    "who",
]


class TestHelpEntriesExist(EvenniaTest):
    """
    Verify that every player-facing command has a non-empty help entry
    defined in world.help_entries.HELP_ENTRY_DICTS.

    This test does NOT exercise the `help` command itself (which requires a
    full server session); instead it imports the data source directly so the
    assertion is fast, deterministic, and environment-independent.
    """

    def setUp(self):
        super().setUp()
        from world.help_entries import HELP_ENTRY_DICTS

        self._help_map = {entry["key"]: entry["text"] for entry in HELP_ENTRY_DICTS}

    def test_help_returns_entry_for_every_player_command(self):
        """
        Every command in PLAYER_COMMANDS has a corresponding entry in
        HELP_ENTRY_DICTS with non-empty text.
        """
        missing = []
        empty = []
        for cmd in PLAYER_COMMANDS:
            if cmd not in self._help_map:
                missing.append(cmd)
            elif not self._help_map[cmd].strip():
                empty.append(cmd)

        if missing:
            self.fail(
                f"Help entries missing for commands: {missing!r}\n"
                f"Add entries to world/help_entries.py.",
            )
        if empty:
            self.fail(
                f"Help entries present but empty for commands: {empty!r}\n"
                f"Fill in the text field in world/help_entries.py.",
            )
