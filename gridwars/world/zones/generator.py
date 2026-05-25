"""
Seeded zone-variant generator (e19.2).

Public API::

    from world.zones.generator import generate_zone, ZoneSpec

    spec = generate_zone("datastream", 0)
    spec_dict = spec.to_dict()

``generate_zone`` is a pure function — no I/O, no DB access. Callers are
responsible for persisting the returned ZoneSpec via batch_cmds or the
procgen pipeline (e19.7).

Determinism guarantee
---------------------
``seed = hash(f"{archetype_id}:{variant_index}")``

Python's built-in ``hash()`` is not stable across interpreter restarts
(PYTHONHASHSEED).  We use a deterministic hash instead: SHA-256 of the
UTF-8 encoded key, truncated to a 64-bit integer via ``int.from_bytes``
(signed, big-endian).  Same (archetype_id, variant_index) pair always
produces the same seed regardless of Python version, platform, or
PYTHONHASHSEED setting.

ZoneSpec fields
---------------
zone_id         str     — "{archetype_id}:{variant_index}"
archetype_id    str     — input archetype slug
variant_index   int     — input variant index
seed            int     — deterministic seed used for this spec
level_band      tuple   — (min, max) from archetype
repop_cadence   int     — seconds, from archetype
topology        str     — chosen from archetype.topology_options
rooms           list    — list of RoomSpec dicts (see below)
exits           list    — list of ExitSpec dicts (from_slug → to_slug)
spawn_table     dict    — {room_slug: list[DaemonSpawnEntry]}

RoomSpec keys: slug, key, flavor_key, room_index
ExitSpec keys: from_slug, to_slug, direction (cardinal or "link")
DaemonSpawnEntry keys: typeclass, count, chance (0.0–1.0)
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from typing import Any

from world.zones.archetypes import get_archetype


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------

def _deterministic_seed(archetype_id: str, variant_index: int) -> int:
    """Return a stable 64-bit seed for (archetype_id, variant_index).

    Uses SHA-256 so the seed is process-stable (no PYTHONHASHSEED
    interference).  Truncated to 64 bits via signed big-endian interpretation
    to stay within Python's random.seed() expected range.
    """
    key = f"{archetype_id}:{variant_index}".encode("utf-8")
    digest = hashlib.sha256(key).digest()
    # Take first 8 bytes → 64-bit signed int
    return int.from_bytes(digest[:8], byteorder="big", signed=True)


# ---------------------------------------------------------------------------
# Room / exit / spawn vocabulary
# ---------------------------------------------------------------------------

# Cardinal direction pairs used when building exit graphs.
_DIRECTIONS = [
    ("north", "south"),
    ("south", "north"),
    ("east", "west"),
    ("west", "east"),
]

# Room role labels for slug suffixes and flavor key suffixes.
_ROOM_ROLES = [
    "entrance",
    "corridor_a",
    "corridor_b",
    "junction",
    "inner_chamber",
    "vault",
    "hub",
    "deep_access",
    "terminus",
    "relay_point",
    "overflow_node",
    "shadow_cache",
    "nexus",
    "core_breach",
]

# Daemon density parameters per tier.
# (max_daemons_per_room, base_chance, max_count_per_entry)
_TIER_DENSITY: dict[int, tuple[float, int]] = {
    1: (0.40, 1),   # sparse — tier 1 (Datastream, Archive Node)
    2: (0.60, 2),   # medium — tier 2 (ICE Wall, Junction Plaza, Shard Foundry)
    3: (0.80, 3),   # dense  — tier 3 (Corrupted Cache, MCP Fragment, Gridcore)
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class RoomSpec:
    """Specification for a single room in a generated zone."""

    slug: str
    key: str
    flavor_key: str
    room_index: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "key": self.key,
            "flavor_key": self.flavor_key,
            "room_index": self.room_index,
        }


@dataclass
class ExitSpec:
    """A directional connection between two rooms."""

    from_slug: str
    to_slug: str
    direction: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_slug": self.from_slug,
            "to_slug": self.to_slug,
            "direction": self.direction,
        }


@dataclass
class DaemonSpawnEntry:
    """One entry in a room's daemon spawn table."""

    typeclass: str
    count: int
    chance: float  # 0.0–1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "typeclass": self.typeclass,
            "count": self.count,
            "chance": round(self.chance, 4),
        }


@dataclass
class ZoneSpec:
    """Complete specification for one zone variant.

    This is the spec layer only — no rooms are created here.  The procgen
    pipeline (e19.7) reads ZoneSpec.to_dict() to drive batch_cmds emission.
    """

    zone_id: str
    archetype_id: str
    variant_index: int
    seed: int
    level_band: tuple[int, int]
    repop_cadence: int
    topology: str
    rooms: list[RoomSpec] = field(default_factory=list)
    exits: list[ExitSpec] = field(default_factory=list)
    spawn_table: dict[str, list[DaemonSpawnEntry]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "zone_id": self.zone_id,
            "archetype_id": self.archetype_id,
            "variant_index": self.variant_index,
            "seed": self.seed,
            "level_band": list(self.level_band),
            "repop_cadence": self.repop_cadence,
            "topology": self.topology,
            "rooms": [r.to_dict() for r in self.rooms],
            "exits": [e.to_dict() for e in self.exits],
            "spawn_table": {
                slug: [entry.to_dict() for entry in entries]
                for slug, entries in self.spawn_table.items()
            },
        }


# ---------------------------------------------------------------------------
# Topology builders
# ---------------------------------------------------------------------------

def _build_linear_exits(rooms: list[RoomSpec]) -> list[ExitSpec]:
    """Connect rooms in a single chain: 0→1→2→...→N with back-links."""
    exits: list[ExitSpec] = []
    fwd, bwd = "north", "south"
    for i in range(len(rooms) - 1):
        exits.append(ExitSpec(
            from_slug=rooms[i].slug,
            to_slug=rooms[i + 1].slug,
            direction=fwd,
        ))
        exits.append(ExitSpec(
            from_slug=rooms[i + 1].slug,
            to_slug=rooms[i].slug,
            direction=bwd,
        ))
    return exits


def _build_ring_exits(rooms: list[RoomSpec]) -> list[ExitSpec]:
    """Connect rooms in a ring; last room loops back to first."""
    exits = _build_linear_exits(rooms)
    if len(rooms) >= 3:
        # Close the ring: last → first (east) and first → last (west)
        exits.append(ExitSpec(
            from_slug=rooms[-1].slug,
            to_slug=rooms[0].slug,
            direction="east",
        ))
        exits.append(ExitSpec(
            from_slug=rooms[0].slug,
            to_slug=rooms[-1].slug,
            direction="west",
        ))
    return exits


def _build_branching_exits(
    rooms: list[RoomSpec],
    rng: random.Random,
) -> list[ExitSpec]:
    """Build a spanning tree with optional cross-links.

    Algorithm:
      1. Start with a linear spine from room[0] through half the rooms.
      2. Branch each remaining room off a random spine room.
      3. Cross-link ~25% of adjacent non-connected pairs for loops.
    """
    n = len(rooms)
    exits: list[ExitSpec] = []
    # Track which (from, to) pairs exist to avoid duplicates.
    linked: set[tuple[str, str]] = set()

    def _add(from_slug: str, to_slug: str, direction: str) -> None:
        key_fwd = (from_slug, to_slug)
        key_bwd = (to_slug, from_slug)
        if key_fwd not in linked and key_bwd not in linked:
            exits.append(ExitSpec(from_slug=from_slug, to_slug=to_slug, direction=direction))
            exits.append(ExitSpec(from_slug=to_slug, to_slug=from_slug, direction=_opposite(direction)))
            linked.add(key_fwd)
            linked.add(key_bwd)

    def _opposite(d: str) -> str:
        return {"north": "south", "south": "north", "east": "west", "west": "east"}.get(d, "link")

    # Spine: rooms 0 .. spine_end
    spine_end = max(1, n // 2)
    for i in range(spine_end):
        _add(rooms[i].slug, rooms[i + 1].slug, "north")

    # Branches: attach remaining rooms to a random spine node
    spine_slugs = [rooms[i].slug for i in range(spine_end + 1)]
    branch_dirs = ["east", "west"]
    for i in range(spine_end + 1, n):
        parent_slug = rng.choice(spine_slugs)
        dir_choice = rng.choice(branch_dirs)
        _add(parent_slug, rooms[i].slug, dir_choice)
        spine_slugs.append(rooms[i].slug)

    return exits


def _apply_topology(
    topology: str,
    rooms: list[RoomSpec],
    rng: random.Random,
) -> list[ExitSpec]:
    if topology == "linear":
        return _build_linear_exits(rooms)
    if topology == "ring":
        return _build_ring_exits(rooms)
    if topology == "branching":
        return _build_branching_exits(rooms, rng)
    raise ValueError(f"Unknown topology {topology!r}")


# ---------------------------------------------------------------------------
# Spawn table builder
# ---------------------------------------------------------------------------

def _build_spawn_table(
    rooms: list[RoomSpec],
    archetype: dict[str, Any],
    rng: random.Random,
) -> dict[str, list[DaemonSpawnEntry]]:
    """Build a per-room daemon spawn table scaled by archetype tier.

    Tier 1 (sparse): ~40% chance per room, max 1 daemon.
    Tier 2 (medium): ~60% chance per room, max 2 daemons.
    Tier 3 (dense):  ~80% chance per room, max 3 daemons.

    The entrance room (index 0) always has reduced density (chance × 0.5)
    to ease player entry regardless of tier.
    """
    tier = archetype["tier"]
    base_chance, max_count = _TIER_DENSITY[tier]
    palette = archetype["daemon_palette"]
    table: dict[str, list[DaemonSpawnEntry]] = {}

    for room in rooms:
        entries: list[DaemonSpawnEntry] = []
        # Entrance room gets reduced spawn pressure.
        room_chance = base_chance * 0.5 if room.room_index == 0 else base_chance
        for typeclass in palette:
            if rng.random() < room_chance:
                count = rng.randint(1, max_count)
                chance = round(room_chance * rng.uniform(0.7, 1.0), 4)
                entries.append(DaemonSpawnEntry(
                    typeclass=typeclass,
                    count=count,
                    chance=chance,
                ))
        table[room.slug] = entries

    return table


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_zone(archetype_id: str, variant_index: int) -> ZoneSpec:
    """Generate a deterministic ZoneSpec for the given archetype + variant.

    This function is pure — it performs no I/O and creates no database
    objects. Calling it twice with identical arguments returns equal specs.

    Args:
        archetype_id:   Slug string identifying the archetype (e.g. "datastream").
        variant_index:  Non-negative integer distinguishing zone variants
                        within the same archetype.

    Returns:
        A fully populated ZoneSpec instance.

    Raises:
        KeyError:    When *archetype_id* is not a registered archetype slug.
        ValueError:  When *variant_index* is negative.
    """
    if variant_index < 0:
        raise ValueError(
            f"variant_index must be non-negative, got {variant_index!r}"
        )

    archetype = get_archetype(archetype_id)
    seed = _deterministic_seed(archetype_id, variant_index)
    rng = random.Random(seed)

    # --- Room count (within archetype's range) ---
    room_min, room_max = archetype["room_count_range"]
    room_count = rng.randint(room_min, room_max)

    # --- Topology ---
    topology = rng.choice(archetype["topology_options"])

    # --- Flavor pool ---
    flavor_pool = archetype["default_flavor_keys"]

    # --- Build rooms ---
    zone_id = f"{archetype_id}:{variant_index}"
    rooms: list[RoomSpec] = []
    used_roles: set[str] = set()
    for i in range(room_count):
        # Pick a role label for this room (prefer unique; wrap if exhausted).
        available = [r for r in _ROOM_ROLES if r not in used_roles]
        role = rng.choice(available) if available else rng.choice(_ROOM_ROLES)
        used_roles.add(role)

        slug = f"{archetype_id}_v{variant_index}_{role}"
        # Human-readable key: "Datastream Entrance", etc.
        arch_display = archetype_id.replace("_", " ").title()
        role_display = role.replace("_", " ").title()
        key = f"{arch_display} {role_display}"

        # flavor_key cycles through the archetype's prose pool.
        flavor_key = flavor_pool[i % len(flavor_pool)]

        rooms.append(RoomSpec(
            slug=slug,
            key=key,
            flavor_key=flavor_key,
            room_index=i,
        ))

    # --- Build exits ---
    exits = _apply_topology(topology, rooms, rng)

    # --- Build spawn table ---
    spawn_table = _build_spawn_table(rooms, archetype, rng)

    return ZoneSpec(
        zone_id=zone_id,
        archetype_id=archetype_id,
        variant_index=variant_index,
        seed=seed,
        level_band=tuple(archetype["level_band"]),
        repop_cadence=archetype["repop_cadence_sec"],
        topology=topology,
        rooms=rooms,
        exits=exits,
        spawn_table=spawn_table,
    )
