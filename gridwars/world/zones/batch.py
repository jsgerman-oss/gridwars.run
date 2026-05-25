"""
GridWars world bootstrap entry point (e19.9).

Provides a single callable — ``bootstrap()`` — that builds the entire world
in one deterministic, idempotent pass:

  1. Core lobby sectors (Users' Sector, Lightcycle Causeway, Daemon Gate,
     Archive Node, Combat Grid, Uplink Node) via ``build_grid.build()``.
  2. All 42 procedurally-generated zone variants via
     ``build_zones.build_all_zones()``.

``build_grid.build()`` already calls ``build_all_zones()`` internally
(wired in e19.7), so ``bootstrap()`` does NOT call ``build_all_zones()``
a second time.  Instead it queries the DB after the build to collect
authoritative counts and prints the unified summary line.

Usage (Evennia batchcode, in-game)::

    @batchcode world.zones.batch

Usage (Django shell / CLI)::

    cd gridwars && ../.venv/bin/python -c "
      import os, django
      os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.conf.settings')
      django.setup()
      from world.zones.batch import bootstrap
      bootstrap()
    "

Re-running is safe — every object is get-or-created; a second call reports
zero new objects created and returns the same totals.

Summary line format::

    GridWars world build complete: 6 lobby sectors + 42 zones
    (~<N> rooms total), <M> daemon spawn markers, <K> exits.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Constants (mirrors build_grid.py and build_zones.py)
# ---------------------------------------------------------------------------

_CATEGORY = "world_build"
_CORE_TAG = "gridwars-core"    # lobby rooms/exits tagged by build_grid.py
_ZONE_TAG = "gridwars-zones"   # procgen zone rooms/exits tagged by build_zones.py


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_exit(obj) -> bool:
    """Return True if *obj* is an Evennia exit (has a non-None destination)."""
    return hasattr(obj, "destination") and obj.destination is not None


def _count_tagged(tag: str) -> tuple[int, int]:
    """Return (room_count, exit_count) for objects carrying *tag*.

    Uses ``search_tag(key=tag, category=_CATEGORY)`` and splits on exit
    detection.
    """
    from evennia.utils.search import search_tag

    objects = search_tag(key=tag, category=_CATEGORY)
    rooms = sum(1 for o in objects if not _is_exit(o))
    exits = sum(1 for o in objects if _is_exit(o))
    return rooms, exits


def _count_daemon_spawn_markers() -> int:
    """Count zone rooms that carry a non-empty ``daemon_spawn_table`` attribute.

    Each such room tells the repop ticker (e19.5) which daemons to spawn.
    This count is used in the summary line as a proxy for "repop scripts ready".
    """
    from evennia.utils.search import search_tag

    zone_objs = search_tag(key=_ZONE_TAG, category=_CATEGORY)
    zone_rooms = [o for o in zone_objs if not _is_exit(o)]
    return sum(
        1 for r in zone_rooms
        if r.attributes.has("daemon_spawn_table")
        and bool(r.attributes.get("daemon_spawn_table"))
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def bootstrap() -> dict[str, int]:
    """Build the entire GridWars world in one idempotent pass.

    Delegates to ``world.build_grid.build()``, which handles both the
    core lobby sectors and the 42 zone variants (via the lazy import of
    ``build_all_zones`` added in e19.7).  Queries the DB afterwards to
    assemble authoritative counts, then prints the unified summary line.

    Returns:
        Dict with integer values for:
            ``lobby_rooms``          — core lobby rooms built
            ``lobby_exits``          — core lobby exits built
            ``zone_rooms``           — total zone rooms (all 42 variants)
            ``zone_exits``           — total intra-zone exits
            ``daemon_spawn_markers`` — zone rooms with daemon_spawn_table set
    """
    from world import build_grid  # noqa: PLC0415 — lazy import requires live DB

    build_grid.build()

    # Query authoritative post-build counts from the live DB.
    lobby_rooms, lobby_exits = _count_tagged(_CORE_TAG)
    zone_rooms, zone_exits = _count_tagged(_ZONE_TAG)
    daemon_markers = _count_daemon_spawn_markers()

    total_rooms = lobby_rooms + zone_rooms
    total_exits = lobby_exits + zone_exits

    print(
        f"GridWars world build complete: "
        f"{lobby_rooms} lobby sectors + 42 zones "
        f"(~{total_rooms} rooms total), "
        f"{daemon_markers} daemon spawn markers, "
        f"{total_exits} exits."
    )

    return {
        "lobby_rooms": lobby_rooms,
        "lobby_exits": lobby_exits,
        "zone_rooms": zone_rooms,
        "zone_exits": zone_exits,
        "daemon_spawn_markers": daemon_markers,
    }
