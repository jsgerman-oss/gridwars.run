"""
GridWars.run duel queue commands.

@queue duel    -- enter the matchmaking queue
@queue leave   -- leave the matchmaking queue
@queue status  -- show your position (or '' to get same view)

Queue state is stored in ServerConfig (survives evennia reload).
The matchmaking script (e17.2) pairs callers from this queue.
"""

from evennia import Command

from world import queue_store


class CmdQueue(Command):
    """
    Manage your place in the duel matchmaking queue.

    Usage:
      @queue          - show queue status
      @queue status   - show queue status
      @queue duel     - join the matchmaking queue
      @queue leave    - leave the matchmaking queue

    When two players are queued the matchmaking script pairs them
    into a duel automatically.
    """

    key = "@queue"
    aliases = ["queue"]
    locks = "cmd:all()"
    help_category = "GridWars"

    def func(self):
        arg = self.args.strip().lower()
        if arg in ("", "status"):
            self._status()
        elif arg == "duel":
            self._enqueue()
        elif arg == "leave":
            self._dequeue()
        else:
            self.caller.msg(
                f"|rUnknown queue subcommand:|n |w{self.args.strip()}|n\n"
                "Usage: |w@queue duel|n | |w@queue leave|n | |w@queue status|n"
            )

    def _enqueue(self):
        char = self.caller
        added = queue_store.enqueue(char.id)
        if not added:
            char.msg("|yYou are already in the duel queue.|n")
            return
        queue = queue_store.get_queue()
        position = queue.index(char.id) + 1
        char.msg(
            f"|gYou joined the duel queue.|n "
            f"You are number |w{position}|n in line."
        )

    def _dequeue(self):
        char = self.caller
        removed = queue_store.dequeue(char.id)
        if not removed:
            char.msg("|yYou are not in the duel queue.|n")
            return
        char.msg("|gYou left the duel queue.|n")

    def _status(self):
        char = self.caller
        queue = queue_store.get_queue()
        if not queue:
            char.msg("|yThe duel queue is empty.|n")
            return
        if char.id in queue:
            position = queue.index(char.id) + 1
            char.msg(
                f"|wDuel queue:|n {len(queue)} waiting -- "
                f"you are number |w{position}|n in line."
            )
        else:
            char.msg(
                f"|wDuel queue:|n {len(queue)} player(s) waiting. "
                "Use |w@queue duel|n to join."
            )
