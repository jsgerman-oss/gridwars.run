"""
GridWars.run themed message templates.

Single source of truth for runtime ANSI-colored messages: login, logout,
faction-unaffiliated nudge, plus any future system messages. Use Evennia
color codes (|c, |g, |y, |r, |w, |n) — no raw ANSI escapes.

Templates use Python str.format(**kwargs) — call sites pass {name},
{faction}, etc.
"""

LOGIN = "|cIdentity disc verified.|n Welcome back, |c{name}|n."
LOGOUT = "|cDisconnecting from the Grid…|n"

FACTION_NUDGE = (
    "|yYou are unaffiliated.|n Three factions claim sectors on the Grid: "
    "|cUsers|n, |gPrograms|n, |rDaemons|n. "
    "Type |w`faction`|n to view them, |w`faction choose <name>`|n to align."
)


def render(template: str, **kwargs) -> str:
    """Format a template with keyword args. Returns the colored string."""
    return template.format(**kwargs)
