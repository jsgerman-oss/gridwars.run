"""
Unit tests for gridwars.typeclasses.daemons.Daemon.

Covers:
- Default faction is "Daemons" on creation (DA1)
- reset_for_respawn() moves Daemon to the Daemon Gate (DA3 respawn)
- at_post_puppet() and at_pre_unpuppet() are no-ops — no messages (DA1 NPC)

Uses EvenniaTest (real Django DB, full Evennia environment).
"""

from unittest.mock import patch

from evennia.utils.create import create_object
from evennia.utils.test_resources import EvenniaTest

from typeclasses.daemons import Daemon


class DaemonTestBase(EvenniaTest):
    """Shared base: provide a Daemon NPC instance for each test."""

    character_typeclass = Daemon

    def setUp(self):
        super().setUp()
        # char1 from EvenniaTest is already a Daemon due to character_typeclass.
        # Create an explicit one for clarity.
        self.daemon = create_object(Daemon, key="TestDaemon", location=self.room1)


class TestDaemonDefaults(DaemonTestBase):
    """Daemon faction is auto-set to 'Daemons' on creation."""

    def test_daemon_defaults_faction(self):
        """A freshly created Daemon has faction == 'Daemons'."""
        self.assertEqual(self.daemon.faction, "Daemons")


class TestDaemonRespawn(DaemonTestBase):
    """Daemon.reset_for_respawn() relocates to Daemon Gate."""

    def test_daemon_respawn_to_daemon_gate(self):
        """reset_for_respawn() moves the Daemon to the room tagged 'daemon_gate'."""
        # Create a room tagged as daemon_gate so search_tag() returns it.
        gate_room = create_object(
            "evennia.objects.objects.DefaultRoom", key="Daemon Gate"
        )
        gate_room.tags.add("daemon_gate", category="world_build")

        # Move the Daemon somewhere else first so we can verify relocation.
        self.daemon.location = self.room2

        self.daemon.reset_for_respawn()

        self.assertEqual(
            self.daemon.location,
            gate_room,
            f"Expected daemon at Daemon Gate, got {self.daemon.location}",
        )


class TestDaemonLoginHooksAreNoOps(DaemonTestBase):
    """at_post_puppet() and at_pre_unpuppet() send no messages to NPCs."""

    def test_at_post_puppet_sends_no_message(self):
        """Daemon.at_post_puppet() does not call self.msg()."""
        with patch.object(self.daemon, "msg") as mock_msg:
            self.daemon.at_post_puppet()
        mock_msg.assert_not_called()

    def test_at_pre_unpuppet_sends_no_message(self):
        """Daemon.at_pre_unpuppet() does not call self.msg()."""
        with patch.object(self.daemon, "msg") as mock_msg:
            self.daemon.at_pre_unpuppet()
        mock_msg.assert_not_called()
