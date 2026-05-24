"""Admin commands for Daemon NPCs."""
from evennia import Command, create_script
from evennia.utils.search import search_script


class CmdDaemonStart(Command):
    """
    Admin: start the Daemon patrol Script.

    Usage:
      @daemon_start

    Idempotent — if the patrol is already running, this is a no-op.
    """

    key = "@daemon_start"
    locks = "cmd:perm(Admin)"
    help_category = "Admin"

    def func(self):
        existing = search_script("daemon_patrol")
        if existing:
            self.caller.msg("|yDaemon patrol already running.|n")
            return
        create_script("typeclasses.scripts.DaemonPatrol")
        self.caller.msg("|gDaemon patrol started.|n")


class CmdDaemonStop(Command):
    """
    Admin: stop the Daemon patrol Script.

    Usage:
      @daemon_stop
    """

    key = "@daemon_stop"
    locks = "cmd:perm(Admin)"
    help_category = "Admin"

    def func(self):
        existing = search_script("daemon_patrol")
        if not existing:
            self.caller.msg("|yDaemon patrol is not running.|n")
            return
        for script in existing:
            script.stop()
        self.caller.msg("|gDaemon patrol stopped.|n")
