"""
GridWars.run faction commands.

`faction` (no args) — list the 3 factions and the caller's current
affiliation.  `faction choose <name>` — align yourself (one-shot).
"""
from evennia import Command
from world.factions import FACTIONS, get


class CmdFaction(Command):
    """
    Show GridWars factions; pick yours.

    Usage:
      faction                  - list factions + your current affiliation
      faction choose <name>    - align yourself (one-shot; admin override required to change)

    Three factions: Users (cyan), Programs (green), Daemons (red).
    """

    key = "faction"
    aliases = []
    locks = "cmd:all()"
    help_category = "GridWars"

    def func(self):
        caller = self.caller
        arg_str = self.args.strip()

        if arg_str.lower().startswith("choose"):
            target_name = arg_str[len("choose"):].strip()
            self._do_choose(target_name)
            return

        self._do_list()

    def _do_list(self):
        """List all factions and the caller's current affiliation."""
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
                "|yYou are unaffiliated.|n Use `|wfaction choose <name>|n` to align."
            )
        caller.msg("\n".join(out))

    def _do_choose(self, name: str):
        """Validate faction name, set caller.faction, and broadcast to room."""
        caller = self.caller
        if not name:
            caller.msg("|rUsage:|n |wfaction choose <name>|n  (e.g. |wfaction choose Users|n)")
            return
        spec = get(name)
        if not spec:
            valid = " | ".join(FACTIONS.keys())
            caller.msg(f"|rNo such faction: {name}.|n  Valid: |w{valid}|n.")
            return
        canon = spec["name"]
        color = spec["color"]
        # One-shot: refuse re-choose unless admin
        current = caller.attributes.get("faction")
        if current:
            caller.msg(
                f"|yYou are already aligned with {current}.|n  Faction changes require admin override."
            )
            return
        caller.faction = canon
        caller.msg(f"|gAlignment set:|n {color}{canon}|n. {spec['tagline']}")
        # Broadcast to room, excluding caller
        if caller.location:
            caller.location.msg_contents(
                f"|c{caller.key}|n has uploaded into the {color}{canon}|n.",
                exclude=[caller],
            )
