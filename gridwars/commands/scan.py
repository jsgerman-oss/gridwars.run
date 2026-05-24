"""
GridWars.run player info commands — `scan`.

Tactical view of the current sector: visible Characters (faction-tinted,
self excluded), exits, and a one-line sector flavor pulled from a
room AttributeProperty `db.scan_flavor` (falls back to first sentence
of `db.desc`).
"""
from evennia import Command
from world.factions import get as get_faction
from world.ownership import get_owner


def _faction_color(name: str | None) -> str:
    if not name:
        return "|y"
    spec = get_faction(name)
    return spec["color"] if spec else "|w"


def _flavor_for(location) -> str:
    """db.scan_flavor takes precedence; fall back to first sentence of db.desc."""
    if not location:
        return "(adrift between sectors)"
    flavor = location.attributes.get("scan_flavor")
    if flavor:
        return flavor
    desc = location.attributes.get("desc", "")
    if not desc:
        return location.key
    # Take the first sentence (split on period, exclamation, question mark)
    for stop in ".!?":
        idx = desc.find(stop)
        if idx != -1:
            return desc[: idx + 1].strip()
    return desc.strip()


class CmdScan(Command):
    """
    Scan the sector — list visible programs, exits, and a flavor line.

    Usage:
      scan

    You see other Characters (excluding yourself, faction-tinted), the
    cardinal exits, and a one-line sense of the sector you're in.
    """

    key = "scan"
    aliases = []
    locks = "cmd:all()"
    help_category = "GridWars"

    def func(self):
        c = self.caller
        loc = c.location

        # Build the output
        out = [f"|c-- |wSECTOR SCAN: {loc.key if loc else 'NULL'}|c --|n"]
        out.append(f"|y{_flavor_for(loc)}|n")
        out.append("")

        # Characters (exclude self)
        chars = [
            obj
            for obj in (loc.contents if loc else [])
            if obj is not c
            and obj.is_typeclass(
                "typeclasses.characters.Character", exact=False
            )
        ]
        if chars:
            out.append("|wPrograms here:|n")
            for ch in chars:
                fac = getattr(ch, "faction", None)
                color = _faction_color(fac)
                tag = f" |w[|n{color}{fac}|n|w]|n" if fac else ""
                out.append(f"  - {color}{ch.key}|n{tag}")
        else:
            out.append("|wPrograms here:|n (none)")

        out.append("")

        # Exits
        exits = [
            e for e in (loc.contents if loc else []) if e.destination is not None
        ]
        if exits:
            out.append("|wExits:|n " + ", ".join(f"|c{e.key}|n" for e in exits))
        else:
            out.append("|wExits:|n (none)")

        # Sector control
        owner = get_owner(loc)
        if owner:
            spec = get_faction(owner)
            color = spec["color"] if spec else "|w"
            out.append(f"|wSector control:|n {color}{owner}|n")
        else:
            out.append("|wSector control:|n |yunclaimed|n")

        c.msg("\n".join(out))
