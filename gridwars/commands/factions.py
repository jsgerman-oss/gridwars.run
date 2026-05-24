"""
GridWars.run faction commands.

`faction` (no args) — list the 3 factions and the caller's current
affiliation. The `faction choose <name>` subcommand is added in F2.
"""
from evennia import Command
from world.factions import FACTIONS, get


class CmdFaction(Command):
    """
    Show the GridWars factions and your current affiliation.

    Usage:
      faction

    Lists Users / Programs / Daemons with tagline + description.
    Indicates which faction you currently belong to (or "unaffiliated").
    Use `faction choose <name>` to align (coming soon).
    """

    key = "faction"
    aliases = []
    locks = "cmd:all()"
    help_category = "GridWars"

    def func(self):
        caller = self.caller
        out = ["|wGridWars Factions|n", ""]
        for name, spec in FACTIONS.items():
            color = spec["color"]
            tagline = spec["tagline"]
            desc = spec["description"]
            out.append(f"{color}{name}|n — |y{tagline}|n")
            out.append(f"  {desc}")
            out.append("")
        current = caller.attributes.get("faction")
        if current:
            spec = get(current)
            color = spec["color"] if spec else "|w"
            out.append(f"You are aligned with {color}{current}|n.")
        else:
            out.append(
                "|yYou are unaffiliated.|n Use `|wfaction choose <name>|n` to align (F2)."
            )
        caller.msg("\n".join(out))
