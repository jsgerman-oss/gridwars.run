"""
GridWars.run duel protocol commands — challenge / accept / decline.

challenge <target>: same-sector only. Stores pending challenge on
target.db.pending_challenge_from = caller and clears after 30s.

accept: invokes world.duels.create_arena and clears the pending state.

decline: clears the pending state.

LD3 adds the in-arena duel mechanic.
"""
from evennia import Command
from evennia.utils.utils import delay

from world.duels import create_arena


CHALLENGE_TIMEOUT_SECONDS = 30


class CmdChallenge(Command):
    """
    Challenge another character to a duel (same sector).

    Usage:
      challenge <target>

    Target must be in your current sector. They have 30s to `accept`
    or `decline`; otherwise the challenge expires.
    """

    key = "challenge"
    locks = "cmd:all()"
    help_category = "GridWars"

    def func(self):
        caller = self.caller
        arg = self.args.strip()
        if not arg:
            caller.msg("|rUsage:|n |wchallenge <target>|n")
            return
        target = caller.search(arg, location=caller.location, quiet=True)
        if isinstance(target, list):
            target = target[0] if target else None
        if target is None:
            caller.msg(f"|rNo '{arg}' here.|n")
            return
        if target is caller:
            caller.msg("|rYou cannot challenge yourself.|n")
            return
        if not target.is_typeclass("typeclasses.characters.Character", exact=False):
            caller.msg("|rYou can only challenge other characters.|n")
            return
        if target.db.pending_challenge_from:
            caller.msg(
                f"|y{target.key} already has a pending challenge.|n"
            )
            return
        target.db.pending_challenge_from = caller
        target.msg(
            f"|c{caller.key}|n has challenged you to a duel. "
            f"Type |waccept|n or |wdecline|n within {CHALLENGE_TIMEOUT_SECONDS}s."
        )
        caller.msg(f"|gChallenge sent|n to {target.key}.")
        delay(CHALLENGE_TIMEOUT_SECONDS, self._expire, target, caller)

    @staticmethod
    def _expire(target, original_challenger):
        # Only clear if the pending challenge is still this challenger's.
        if target.db.pending_challenge_from is original_challenger:
            target.db.pending_challenge_from = None
            target.msg(
                f"|yThe challenge from {original_challenger.key} has expired.|n"
            )
            original_challenger.msg(
                f"|y{target.key} did not respond. Challenge expired.|n"
            )


class CmdAccept(Command):
    """
    Accept a pending duel challenge.

    Usage:
      accept
    """

    key = "accept"
    locks = "cmd:all()"
    help_category = "GridWars"

    def func(self):
        caller = self.caller
        challenger = caller.db.pending_challenge_from
        if not challenger:
            caller.msg("|yNo pending challenge.|n")
            return
        caller.db.pending_challenge_from = None
        create_arena(challenger, caller)
        caller.msg("|gChallenge accepted.|n Entering the arena...")
        challenger.msg(
            f"|c{caller.key}|n accepted your challenge. Entering the arena..."
        )


class CmdDecline(Command):
    """
    Decline a pending duel challenge.

    Usage:
      decline
    """

    key = "decline"
    locks = "cmd:all()"
    help_category = "GridWars"

    def func(self):
        caller = self.caller
        challenger = caller.db.pending_challenge_from
        if not challenger:
            caller.msg("|yNo pending challenge.|n")
            return
        caller.db.pending_challenge_from = None
        caller.msg("|gDeclined.|n")
        if challenger:
            challenger.msg(
                f"|y{caller.key} declined your challenge.|n"
            )
