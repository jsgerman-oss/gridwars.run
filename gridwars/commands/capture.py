"""
GridWars.run sector capture command.

`capture` (no args) claims the caller's current sector for their faction.
Requires the caller to be aligned with a faction. Idempotent: re-capturing
a sector your faction already owns is a friendly no-op. Cross-faction
capture is allowed (overwrites prior ownership; no resistance mechanic
yet — that's a follow-up).
"""
from evennia import Command

from world.factions import get as get_faction
from world.ownership import get_owner, set_owner


class CmdCapture(Command):
    """
    Claim the current sector for your faction.

    Usage:
      capture

    Requires you to be aligned (use `faction choose <name>` first).
    Re-capturing your faction's own sector is a no-op. Capturing a
    rival-owned sector overwrites the prior ownership.
    """

    key = "capture"
    aliases = []
    locks = "cmd:all()"
    help_category = "GridWars"

    def func(self):
        caller = self.caller
        loc = caller.location
        if not loc:
            caller.msg("|rYou are adrift between sectors and cannot capture.|n")
            return

        faction_name = caller.faction
        if not faction_name:
            caller.msg(
                "|rYou are unaffiliated.|n Align first with "
                "|wfaction choose <name>|n."
            )
            return

        spec = get_faction(faction_name)
        color = spec["color"] if spec else "|w"

        current_owner = get_owner(loc)
        if current_owner and current_owner.lower() == faction_name.lower():
            caller.msg(
                f"|y{loc.key}|n is already held by "
                f"{color}{faction_name}|n."
            )
            return

        set_owner(loc, faction_name)
        caller.msg(
            f"|g{loc.key}|n is now under {color}{faction_name}|n control."
        )
        if loc:
            loc.msg_contents(
                f"|c{caller.key}|n of {color}{faction_name}|n "
                f"has claimed this sector for the Grid.",
                exclude=[caller],
            )
