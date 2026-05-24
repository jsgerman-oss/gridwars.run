"""
GridWars.run faction registry.

Three founding factions, each with a name, tagline, color code, and
description. Used by the `faction` command and (later) the faction
selection flow. Faction membership is stored on Character.faction
(AttributeProperty from Epic 4).
"""

FACTIONS = {
    "Users": {
        "tagline": "Uploaded. Underestimated.",
        "color": "|c",
        "description": (
            "Civilian programs uploaded into the Grid. Outnumbered, "
            "underestimated, and increasingly organized. The default "
            "faction for fresh sign-ons. If you don't choose, the Grid "
            "assumes you are one of them."
        ),
    },
    "Programs": {
        "tagline": "Order is the throughput.",
        "color": "|g",
        "description": (
            "Entrenched grid natives. Structured combat, predictable "
            "routines, and a deep suspicion of unregistered processes. "
            "They built the lattice and they intend to keep it running."
        ),
    },
    "Daemons": {
        "tagline": "We are the noise in your stack.",
        "color": "|r",
        "description": (
            "Rogue and corrupted processes that slipped the schedule. "
            "Chaotic, fast, and unconcerned with provenance. Daemons "
            "thrive in the Combat Grid and the gaps between sectors."
        ),
    },
}


def get(name: str) -> dict | None:
    """Case-insensitive faction lookup. Returns the spec dict or None."""
    for canon, spec in FACTIONS.items():
        if canon.lower() == name.lower():
            return {"name": canon, **spec}
    return None


def names() -> list[str]:
    """Canonical faction names in declared order."""
    return list(FACTIONS.keys())
