"""
GridWars.run sector ownership -- data layer.

Ownership is stored as a Room tag: ``("owned-by:<FactionName>", "ownership")``.
A room may have at most one ownership tag at a time (set_owner enforces
this by clearing prior ownership tags before adding the new one).

Evennia lowercases tag keys on storage (TagHandler.add, tags.py:513).
That means ``"owned-by:Users"`` is stored as ``"owned-by:users"``.
get_owner recovers canonical casing via the factions registry so callers
always receive ``"Users"`` / ``"Programs"`` / ``"Daemons"``, never a
lowercased variant.

NOTE: this module is the data layer ONLY. The ``capture`` command (SO2)
and display integration (SO3) build on these helpers.
"""
from evennia.utils.search import search_tag

from world import factions as _factions

OWNERSHIP_CATEGORY = "ownership"
OWNERSHIP_TAG_PREFIX = "owned-by:"


def _ownership_slug(faction_name: str) -> str:
    """Return the raw tag key for the given faction name (lowercased by Evennia on write)."""
    return f"{OWNERSHIP_TAG_PREFIX}{faction_name}"


def get_owner(room) -> str | None:
    """Return the canonical faction name owning this room, or None if unclaimed.

    Evennia lowercases tag keys internally, so we recover canonical casing
    from the factions registry (case-insensitive lookup).
    """
    if not room:
        return None
    for tag in room.tags.get(category=OWNERSHIP_CATEGORY, return_list=True) or []:
        if tag and tag.startswith(OWNERSHIP_TAG_PREFIX):
            raw_name = tag[len(OWNERSHIP_TAG_PREFIX):]
            spec = _factions.get(raw_name)
            if spec:
                return spec["name"]
            # Unrecognised faction stored in tag -- return as-is rather than None.
            return raw_name
    return None


def set_owner(room, faction_name: str) -> None:
    """Claim a room for the given faction. Clears any prior ownership tag first.

    Args:
        room: An Evennia Room (or any typeclass object with a tags handler).
        faction_name: Canonical faction name, e.g. ``"Users"``.
    """
    if not room or not faction_name:
        return
    clear_owner(room)
    room.tags.add(_ownership_slug(faction_name), category=OWNERSHIP_CATEGORY)


def clear_owner(room) -> None:
    """Remove all ownership tags from this room (idempotent on unclaimed rooms).

    Args:
        room: An Evennia Room (or any typeclass object with a tags handler).
    """
    if not room:
        return
    for tag in room.tags.get(category=OWNERSHIP_CATEGORY, return_list=True) or []:
        if tag and tag.startswith(OWNERSHIP_TAG_PREFIX):
            room.tags.remove(tag, category=OWNERSHIP_CATEGORY)


def rooms_owned_by(faction_name: str) -> list:
    """Return all rooms currently owned by the given faction.

    Args:
        faction_name: Canonical faction name, e.g. ``"Programs"``.

    Returns:
        list: Matching Room objects (may be empty).
    """
    if not faction_name:
        return []
    return list(search_tag(_ownership_slug(faction_name), category=OWNERSHIP_CATEGORY))
