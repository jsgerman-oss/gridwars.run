"""
GridWars.run player info commands — `status`.

Renders a neon-grid HUD of the caller's identity + stats. Reads
Character AttributeProperty fields (Epic 4) and faction color from
the registry (Epic 5).
"""
from commands.command import Command
from world.factions import get as get_faction
from world.ownership import rooms_owned_by


def _bar_color(value: int, ceiling: int = 100) -> str:
    """Pick a color code based on stat percentage. |g good, |y warn, |r crit."""
    if ceiling <= 0:
        return "|w"
    pct = (value / ceiling) * 100
    if pct >= 60:
        return "|g"
    if pct >= 25:
        return "|y"
    return "|r"


class CmdStatus(Command):
    """
    Show your identity disc — name, sector, faction, integrity, energy, exp, rank.

    Usage:
      status

    Color cues: |ggreen|n = healthy, |yyellow|n = warning, |rred|n = critical.
    """

    key = "status"
    aliases = []
    locks = "cmd:all()"
    help_category = "GridWars"

    def func(self):
        c = self.caller
        sector = c.location.key if c.location else "(adrift)"

        faction_name = c.faction
        if faction_name:
            spec = get_faction(faction_name)
            faction_str = f"{spec['color']}{faction_name}|n" if spec else faction_name
        else:
            faction_str = "|yunaffiliated|n"

        integrity = c.integrity
        energy = c.energy
        experience = c.experience
        grid_rank = c.grid_rank

        i_col = _bar_color(integrity, 100)
        e_col = _bar_color(energy, 100)

        lines = [
            "|c╔══════════ IDENTITY DISC ══════════╗|n",
            f"|w  Name     |n |c{c.key}|n",
            f"|w  Sector   |n |c{sector}|n",
            f"|w  Faction  |n {faction_str}",
            f"|w  Integrity|n {i_col}{integrity:>3}|n / |w100|n",
            f"|w  Energy   |n {e_col}{energy:>3}|n / |w100|n",
            f"|w  Exp      |n |g{experience}|n",
            f"|w  Rank     |n |c{grid_rank}|n",
            "|c╚════════════════════════════════════╝|n",
        ]
        if faction_name:
            held_count = len(rooms_owned_by(faction_name))
            lines.append(f"|w  Sectors  |n |g{held_count}|n held by your faction")
        c.msg("\n".join(lines))
