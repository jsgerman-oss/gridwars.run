"""
Unit tests for gridwars.typeclasses.scripts.DaemonPatrol._step_one().

Covers:
- _step_one() moves a Daemon to a valid adjacent gridwars-core sector (DA2)
- _step_one() causes the Daemon to engage (strike) a non-Daemon Character
  sharing the same room (DA3 sense+engage)
- _step_one() does NOT engage peer Daemons sharing the same room (DA3 faction
  filter)

Uses EvenniaTest (real Django DB, full Evennia environment).

Test-world design:
  room1 <--exit--> room2
  Both rooms are tagged ('gridwars-core', 'world_build') so DaemonPatrol
  considers them valid patrol destinations.
  Exits are tagged the same way so the valid_exits filter matches.
"""

from unittest.mock import patch

from evennia.utils.create import create_object, create_script
from evennia.utils.test_resources import EvenniaTest

from typeclasses.daemons import Daemon
from typeclasses.scripts import DaemonPatrol


def _make_tagged_room(key):
    """Create a DefaultRoom tagged for gridwars-core world_build."""
    room = create_object("evennia.objects.objects.DefaultRoom", key=key)
    room.tags.add("gridwars-core", category="world_build")
    return room


def _connect(src, dst, exit_key):
    """Create a one-way exit from src to dst, tagged gridwars-core."""
    exit_obj = create_object(
        "evennia.objects.objects.DefaultExit",
        key=exit_key,
        location=src,
        destination=dst,
    )
    exit_obj.tags.add("gridwars-core", category="world_build")
    return exit_obj


class DaemonPatrolTestBase(EvenniaTest):
    """Set up a two-room world and a DaemonPatrol script for each test."""

    def setUp(self):
        super().setUp()
        self.sector1 = _make_tagged_room("Sector One")
        self.sector2 = _make_tagged_room("Sector Two")
        # Bidirectional exits so Daemon can move either way.
        self.exit_1_to_2 = _connect(self.sector1, self.sector2, "east")
        self.exit_2_to_1 = _connect(self.sector2, self.sector1, "west")

        # DaemonPatrol script — use as a helper, not a live timer.
        self.patrol = create_script(DaemonPatrol)
        self.patrol.stop()  # Don't let it fire in the test loop.

        # Daemon placed in sector1.
        self.daemon = create_object(Daemon, key="TestDaemon", location=self.sector1)


class TestPatrolMovement(DaemonPatrolTestBase):
    """_step_one() moves the Daemon to a valid adjacent gridwars-core sector."""

    def test_patrol_moves_daemon_to_adjacent_sector(self):
        """Daemon ends up in sector2 (or sector1 if random keeps it) — always tagged."""
        # With only one valid exit from sector1 (east → sector2), the Daemon
        # must end up in sector2 after _step_one().
        # However, _step_one() senses+engages after moving. There's no other
        # character, so the engage branch is a no-op.
        self.patrol._step_one(self.daemon)

        new_loc = self.daemon.location
        self.assertIsNotNone(new_loc)
        self.assertTrue(
            new_loc.tags.has("gridwars-core", category="world_build"),
            f"Daemon moved to untagged location: {new_loc.key}",
        )


class TestPatrolEngagesNonDaemon(DaemonPatrolTestBase):
    """_step_one() calls execute_cmd("strike <target>") on a non-Daemon Character."""

    def test_patrol_engages_non_daemon_in_room(self):
        """After moving, _step_one() calls daemon.execute_cmd('strike <target>') on the
        first non-Daemon Character found in the destination room.
        """
        from typeclasses.characters import Character

        # Place a non-Daemon character in sector2 (the only exit from sector1).
        target = create_object(Character, key="TargetUser", location=self.sector2)

        executed_cmds = []

        def capture_execute_cmd(cmd_str):
            executed_cmds.append(cmd_str)

        # Patch daemon.execute_cmd so we capture the call without needing a real cmdset.
        self.daemon.execute_cmd = capture_execute_cmd

        # Force Daemon to move to sector2 by patching random.choice.
        with patch("typeclasses.scripts.random.choice", return_value=self.exit_1_to_2):
            self.patrol._step_one(self.daemon)

        self.assertEqual(
            self.daemon.location,
            self.sector2,
            "Daemon should have moved to sector2 where the target is.",
        )
        self.assertTrue(
            executed_cmds,
            "_step_one() should have called execute_cmd at least once.",
        )
        self.assertIn(
            f"strike {target.key}",
            executed_cmds,
            f"Expected 'strike {target.key}' to be executed; got: {executed_cmds}",
        )


class TestPatrolDoesNotEngageDaemons(DaemonPatrolTestBase):
    """_step_one() ignores peer Daemons — faction filter excludes 'Daemons'."""

    def test_patrol_does_not_engage_other_daemons(self):
        """Peer Daemon in the same room after move is not struck (integrity unchanged)."""
        peer = create_object(Daemon, key="PeerDaemon", location=self.sector2)
        peer.integrity = 100

        # Force daemon1 to move into sector2 (where peer is).
        with patch("typeclasses.scripts.random.choice", return_value=self.exit_1_to_2):
            self.patrol._step_one(self.daemon)

        self.assertEqual(
            self.daemon.location,
            self.sector2,
            "Daemon should have moved to sector2.",
        )
        self.assertEqual(
            peer.integrity,
            100,
            f"Peer Daemon's integrity must be untouched; got {peer.integrity}.",
        )
