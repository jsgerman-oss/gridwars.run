"""
Procgen zone instantiation pipeline (e19.7).

Wires the seeded generator (e19.2), prose pools (e19.6), and archetype
definitions (e19.1) into actual Evennia room + exit objects.

Public API::

    from world.zones.build_zones import build_all_zones, DEFAULT_DISTRIBUTION

    # Called from world.build_grid.build() after core sectors exist.
    result = build_all_zones()
    # result["zones_built"] == 42, result["zones_skipped"] == 0 on first run
    # result["zones_built"] == 0,  result["zones_skipped"] == 42 on re-run

Idempotency
-----------
Every zone room is tagged ``(zone_tag, ZONE_CATEGORY)`` where::

    zone_tag = "zone:<archetype_id>:<variant_index>"

Before creating any room, we check for an existing object with that tag.
Re-running ``build_all_zones()`` is a no-op: it finds all existing rooms,
skips creation, and returns ``zones_skipped == total``.

Daemon spawn markers
--------------------
Live daemons are NOT spawned here (that is the repop ticker, e19.5).
Instead, each room receives a ``db.daemon_spawn_table`` attribute
containing the list of DaemonSpawnEntry dicts from the ZoneSpec.
The repop ticker reads this attribute and creates daemon objects as needed.

Tag scheme
----------
Every room and exit created by this module carries two tags:

    (zone_tag,     ZONE_CATEGORY)   — identity tag for this specific zone
    (MEMBER_TAG,   ZONE_CATEGORY)   — membership tag for bulk ops

where ZONE_CATEGORY = "world_build" (matches build_grid.py convention).
"""

from __future__ import annotations

import random
from typing import Any

from world.zones.archetypes import ARCHETYPES
from world.zones.generator import generate_zone
from world.zones.prose_pools import PROSE_POOLS

# Script typeclass path — avoids a hard import at module level (Evennia may
# not be fully initialised when this module is imported in tests).
REPOP_SCRIPT_TYPECLASS = "world.zones.repop.ZoneRepopScript"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ZONE_CATEGORY = "world_build"   # shared with build_grid.py
MEMBER_TAG = "gridwars-zones"   # bulk-membership tag (parallel to "gridwars-core")

TYPECLASS_ROOM = "evennia.objects.objects.DefaultRoom"
TYPECLASS_EXIT = "evennia.objects.objects.DefaultExit"

# ---------------------------------------------------------------------------
# Distribution — how many variants to instantiate per archetype (sums to 42)
# Source: Epic 19 design §3 table.
# ---------------------------------------------------------------------------

DEFAULT_DISTRIBUTION: dict[str, int] = {
    "datastream":      8,
    "archive_node":    6,
    "ice_wall":        6,
    "junction_plaza":  4,
    "shard_foundry":   5,
    "corrupted_cache": 5,
    "mcp_fragment":    4,
    "gridcore":        4,
}

assert sum(DEFAULT_DISTRIBUTION.values()) == 42, (
    "DEFAULT_DISTRIBUTION must sum to 42 — check the archetype counts."
)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _zone_tag(archetype_id: str, variant_index: int) -> str:
    """Unique identity tag for one zone variant."""
    return f"zone:{archetype_id}:{variant_index}"


def _room_tag(archetype_id: str, variant_index: int, room_slug: str) -> str:
    """Unique identity tag for one room within a zone."""
    return f"room:{archetype_id}:{variant_index}:{room_slug}"


def _exit_tag(archetype_id: str, variant_index: int, from_slug: str, direction: str) -> str:
    """Unique identity tag for one exit."""
    return f"exit:{archetype_id}:{variant_index}:{from_slug}:{direction}"


def _zone_exists(archetype_id: str, variant_index: int) -> bool:
    """Return True if at least one room with this zone's identity tag exists."""
    from evennia.utils.search import search_tag
    tag = _zone_tag(archetype_id, variant_index)
    return bool(search_tag(key=tag, category=ZONE_CATEGORY))


def _resolve_prose(
    archetype_id: str,
    room_index: int,
    seed: int,
) -> tuple[str, str]:
    """Return (room_name, room_desc) for one room using seeded RNG.

    Uses the same seed as the generator so prose selection is stable
    across re-runs. Each room gets a unique sub-seed derived from
    room_index to avoid all rooms drawing from position 0 of the pool.
    """
    pool = PROSE_POOLS.get(archetype_id)
    if pool is None:
        # Fallback: use archetype id + room index as plain text
        display = archetype_id.replace("_", " ").title()
        return f"{display} Chamber {room_index}", f"A sector of the {display} zone."

    rng = random.Random(seed + room_index)
    name = rng.choice(pool["room_name_pool"])
    desc = rng.choice(pool["room_desc_pool"])
    return name, desc


def _get_or_create_zone_room(
    archetype_id: str,
    variant_index: int,
    room_slug: str,
    room_name: str,
    room_desc: str,
    spawn_entries: list[dict[str, Any]],
    level_band: tuple[int, int],
    zone_tag: str,
) -> Any:
    """Return existing room by room tag or create a new one."""
    from evennia.utils.create import create_object
    from evennia.utils.search import search_tag

    rtag = _room_tag(archetype_id, variant_index, room_slug)
    existing = search_tag(key=rtag, category=ZONE_CATEGORY)
    if existing:
        return existing[0]

    room = create_object(
        typeclass=TYPECLASS_ROOM,
        key=room_name,
        nohome=True,
        attributes=[
            ("desc", room_desc),
            # Daemon spawn markers — repop ticker (e19.5) reads this.
            ("daemon_spawn_table", spawn_entries),
            # Zone metadata
            ("zone_id", f"{archetype_id}:{variant_index}"),
            ("archetype_id", archetype_id),
            ("level_band", level_band),
        ],
        tags=[
            (rtag,       ZONE_CATEGORY),   # per-room identity
            (zone_tag,   ZONE_CATEGORY),   # zone membership
            (MEMBER_TAG, ZONE_CATEGORY),   # world-wide zone membership
        ],
    )
    return room


def _ensure_zone_exit(
    archetype_id: str,
    variant_index: int,
    from_slug: str,
    from_room: Any,
    to_room: Any,
    direction: str,
    zone_tag: str,
) -> Any:
    """Create a directional exit if one with the same tag does not exist."""
    from evennia.utils.create import create_object
    from evennia.utils.search import search_tag

    etag = _exit_tag(archetype_id, variant_index, from_slug, direction)
    existing = search_tag(key=etag, category=ZONE_CATEGORY)
    if existing:
        return existing[0]

    aliases = [direction[0]] if len(direction) == 1 or direction in (
        "north", "south", "east", "west"
    ) else []

    exit_obj = create_object(
        typeclass=TYPECLASS_EXIT,
        key=direction,
        aliases=aliases,
        location=from_room,
        destination=to_room,
        tags=[
            (etag,       ZONE_CATEGORY),
            (zone_tag,   ZONE_CATEGORY),
            (MEMBER_TAG, ZONE_CATEGORY),
        ],
    )
    return exit_obj


# ---------------------------------------------------------------------------
# Repop script lifecycle
# ---------------------------------------------------------------------------

def _ensure_zone_repop_script(
    archetype_id: str,
    variant_index: int,
    entry_room: Any,
) -> bool:
    """Start a ZoneRepopScript for this zone if one is not already running.

    Idempotent: if a script with key ``"zone_repop:<archetype_id>:<variant_index>"``
    already exists (persistent=True, interval set), this is a no-op.

    The script is stored on *entry_room* so it has a natural DB anchor.
    Interval is taken from the archetype's ``repop_cadence_sec``.

    Returns True if a new script was created, False if one already existed.
    """
    from evennia.utils.create import create_script
    from evennia.utils.search import search_script

    script_key = f"zone_repop:{archetype_id}:{variant_index}"
    existing = search_script(script_key)
    if existing:
        return False

    archetype = ARCHETYPES.get(archetype_id, {})
    cadence = int(archetype.get("repop_cadence_sec", 90))
    zone_id = f"{archetype_id}:{variant_index}"
    level_band = archetype.get("level_band", (1, 5))
    daemon_palette = archetype.get("daemon_palette", ["typeclasses.daemons.Daemon"])

    script = create_script(
        typeclass=REPOP_SCRIPT_TYPECLASS,
        key=script_key,
        obj=entry_room,
        interval=cadence,
        persistent=True,
        autostart=True,
        start_delay=True,
    )
    script.db.zone_id = zone_id
    script.db.zone_archetype = archetype_id
    script.db.level_band_min = int(level_band[0])
    script.db.level_band_max = int(level_band[1])
    script.db.daemon_palette = list(daemon_palette)
    script.db.daemon_target = 1  # default; overridden by admin tooling if needed
    return True


# ---------------------------------------------------------------------------
# Core builder
# ---------------------------------------------------------------------------

def _build_one_zone(archetype_id: str, variant_index: int) -> dict[str, int]:
    """Instantiate one zone variant.  Returns {"rooms": n, "exits": n}."""
    spec = generate_zone(archetype_id, variant_index)
    zone_tag = _zone_tag(archetype_id, variant_index)
    level_band = tuple(spec.level_band)

    # Build a slug → Room mapping
    slug_to_room: dict[str, Any] = {}
    for room_spec in spec.rooms:
        spawn_entries = [
            e.to_dict() for e in spec.spawn_table.get(room_spec.slug, [])
        ]
        name, desc = _resolve_prose(archetype_id, room_spec.room_index, spec.seed)
        room = _get_or_create_zone_room(
            archetype_id=archetype_id,
            variant_index=variant_index,
            room_slug=room_spec.slug,
            room_name=name,
            room_desc=desc,
            spawn_entries=spawn_entries,
            level_band=level_band,
            zone_tag=zone_tag,
        )
        slug_to_room[room_spec.slug] = room

    # Wire intra-zone exits
    exits_created = 0
    for exit_spec in spec.exits:
        from_room = slug_to_room.get(exit_spec.from_slug)
        to_room = slug_to_room.get(exit_spec.to_slug)
        if from_room is None or to_room is None:
            continue
        _ensure_zone_exit(
            archetype_id=archetype_id,
            variant_index=variant_index,
            from_slug=exit_spec.from_slug,
            from_room=from_room,
            to_room=to_room,
            direction=exit_spec.direction,
            zone_tag=zone_tag,
        )
        exits_created += 1

    # Start the repop ticker for this zone (idempotent).
    entry_room = next(iter(slug_to_room.values())) if slug_to_room else None
    if entry_room is not None:
        _ensure_zone_repop_script(archetype_id, variant_index, entry_room)

    return {"rooms": len(slug_to_room), "exits": exits_created}


# ---------------------------------------------------------------------------
# Repop script recovery for already-existing zones
# ---------------------------------------------------------------------------

def _ensure_repop_for_existing_zone(archetype_id: str, variant_index: int) -> None:
    """Ensure a repop script is running for a zone whose rooms already exist.

    Called during the idempotency-skip path of build_all_zones() so that
    calling build_all_zones() on a world built before auto-start was added
    still results in all 42 repop scripts running.
    """
    from evennia.utils.search import search_tag

    zone_tag = _zone_tag(archetype_id, variant_index)
    zone_objects = search_tag(key=zone_tag, category=ZONE_CATEGORY)
    rooms = [
        o for o in zone_objects
        if not (hasattr(o, "destination") and o.destination is not None)
    ]
    if not rooms:
        return
    _ensure_zone_repop_script(archetype_id, variant_index, rooms[0])


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def build_all_zones(
    distribution: dict[str, int] | None = None,
) -> dict[str, int]:
    """Instantiate all zone variants described by *distribution*.

    Iterates archetypes in level-band order (lowest first), calling
    ``generate_zone`` for each ``(archetype_id, variant_index)`` pair,
    then persisting rooms, exits, and daemon spawn markers.

    Idempotent: zones that already exist (detected via identity tag) are
    counted as skipped rather than duplicated.

    Args:
        distribution: Mapping of ``archetype_id`` → number of variants to
            instantiate.  Defaults to ``DEFAULT_DISTRIBUTION`` (42 zones).

    Returns:
        Dict with keys:
            ``zones_built``   — number of new zones created this run
            ``zones_skipped`` — number of existing zones skipped
            ``rooms_built``   — total rooms created
            ``exits_built``   — total exits created
    """
    if distribution is None:
        distribution = DEFAULT_DISTRIBUTION

    # Sort archetypes by level_band min so build order matches player progression
    ordered_archetypes = sorted(
        distribution.keys(),
        key=lambda aid: ARCHETYPES[aid]["level_band"][0] if aid in ARCHETYPES else 999,
    )

    zones_built = 0
    zones_skipped = 0
    rooms_built = 0
    exits_built = 0

    for archetype_id in ordered_archetypes:
        count = distribution[archetype_id]
        for variant_index in range(count):
            if _zone_exists(archetype_id, variant_index):
                zones_skipped += 1
                # Zone rooms already exist; ensure repop script is running
                # in case it was never started (e.g. first run before this
                # feature landed, or manual script deletion).
                _ensure_repop_for_existing_zone(archetype_id, variant_index)
                continue
            result = _build_one_zone(archetype_id, variant_index)
            zones_built += 1
            rooms_built += result["rooms"]
            exits_built += result["exits"]

    total = zones_built + zones_skipped
    print(
        f"[build_zones] {total} zones total: "
        f"{zones_built} built, {zones_skipped} skipped "
        f"({rooms_built} rooms, {exits_built} exits created)."
    )
    return {
        "zones_built": zones_built,
        "zones_skipped": zones_skipped,
        "rooms_built": rooms_built,
        "exits_built": exits_built,
    }
