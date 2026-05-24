"""Admin command: spawn an identity disc for testing."""
from evennia import Command
from evennia.utils.create import create_object


class CmdSpawnDisc(Command):
    """
    Admin: spawn an Identity Disc in your inventory or current room.

    Usage:
      @spawn_disc [<name>]

    Defaults to "standard disc" if no name is given. Spawns into your
    current location (room or inventory if no location).
    """

    key = "@spawn_disc"
    locks = "cmd:perm(Admin)"
    help_category = "Admin"

    def func(self):
        caller = self.caller
        name = self.args.strip() or "standard disc"
        loc = caller.location or caller
        disc = create_object("typeclasses.discs.Disc", key=name, location=loc)
        caller.msg(f"|gSpawned|n {disc.key} (#{disc.id}) at {loc.key}.")
