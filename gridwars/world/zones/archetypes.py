"""
Zone archetype prototype definitions (e19.1).

Eight archetypes define the structural parameters for all 42 dynamically-
generated zones. The seeded generator (e19.2) consumes these definitions
to produce deterministic ZoneSpec instances.

Each archetype dict declares:
    archetype_id         str  — unique slug (matches key in ARCHETYPES)
    level_band           (int, int) — inclusive (min, max) level range
    room_count_range     (int, int) — how many rooms a variant may contain
    topology_options     list[str]  — subset of {"linear", "ring", "branching"}
    daemon_palette       list[str]  — typeclass paths for daemon variants
    repop_cadence_sec    int  — seconds between repop ticks
    default_flavor_keys  list[str]  — prose-pool keys emitted as flavor_key refs
                                      (resolved to actual prose by e19.6 wire-up)
    tier                 int  — 1 (sparse) through 3 (dense); controls daemon density

Ordering is from lowest to highest tier, roughly matching the in-world
progression a player would encounter.

No I/O here — pure data module; safe to import with no Evennia context.
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Archetype definitions
# ---------------------------------------------------------------------------

ARCHETYPES: dict[str, dict[str, Any]] = {
    "datastream": {
        "archetype_id": "datastream",
        "level_band": (1, 5),
        "room_count_range": (3, 6),
        "topology_options": ["linear"],
        "daemon_palette": [
            "typeclasses.daemon_variants.StrayPacket",
        ],
        "repop_cadence_sec": 120,
        "default_flavor_keys": [
            "datastream.ambient",
            "datastream.entrance",
            "datastream.corridor",
        ],
        "tier": 1,
    },
    "archive_node": {
        "archetype_id": "archive_node",
        "level_band": (3, 8),
        "room_count_range": (4, 7),
        "topology_options": ["linear", "branching"],
        "daemon_palette": [
            "typeclasses.daemon_variants.ReadOnlySentry",
        ],
        "repop_cadence_sec": 150,
        "default_flavor_keys": [
            "archive_node.ambient",
            "archive_node.entrance",
            "archive_node.vault",
            "archive_node.access_panel",
        ],
        "tier": 1,
    },
    "ice_wall": {
        "archetype_id": "ice_wall",
        "level_band": (6, 12),
        "room_count_range": (4, 8),
        "topology_options": ["linear", "ring"],
        "daemon_palette": [
            "typeclasses.daemon_variants.ICEPicket",
        ],
        "repop_cadence_sec": 90,
        "default_flavor_keys": [
            "ice_wall.ambient",
            "ice_wall.entrance",
            "ice_wall.barrier",
            "ice_wall.checkpoint",
        ],
        "tier": 2,
    },
    "junction_plaza": {
        "archetype_id": "junction_plaza",
        "level_band": (8, 14),
        "room_count_range": (5, 9),
        "topology_options": ["ring", "branching"],
        "daemon_palette": [
            "typeclasses.daemon_variants.JunctionRoamer",
        ],
        "repop_cadence_sec": 100,
        "default_flavor_keys": [
            "junction_plaza.ambient",
            "junction_plaza.entrance",
            "junction_plaza.crossroads",
            "junction_plaza.hub",
        ],
        "tier": 2,
    },
    "shard_foundry": {
        "archetype_id": "shard_foundry",
        "level_band": (12, 18),
        "room_count_range": (5, 10),
        "topology_options": ["linear", "branching"],
        "daemon_palette": [
            "typeclasses.daemon_variants.ForgeDaemon",
        ],
        "repop_cadence_sec": 80,
        "default_flavor_keys": [
            "shard_foundry.ambient",
            "shard_foundry.entrance",
            "shard_foundry.forge",
            "shard_foundry.cooling_bay",
        ],
        "tier": 2,
    },
    "corrupted_cache": {
        "archetype_id": "corrupted_cache",
        "level_band": (15, 22),
        "room_count_range": (6, 10),
        "topology_options": ["branching", "ring"],
        "daemon_palette": [
            "typeclasses.daemon_variants.MutatedCacheDaemon",
        ],
        "repop_cadence_sec": 70,
        "default_flavor_keys": [
            "corrupted_cache.ambient",
            "corrupted_cache.entrance",
            "corrupted_cache.glitch_zone",
            "corrupted_cache.data_rot",
        ],
        "tier": 3,
    },
    "mcp_fragment": {
        "archetype_id": "mcp_fragment",
        "level_band": (20, 28),
        "room_count_range": (6, 12),
        "topology_options": ["ring", "branching"],
        "daemon_palette": [
            "typeclasses.daemon_variants.FragmentGuardian",
        ],
        "repop_cadence_sec": 60,
        "default_flavor_keys": [
            "mcp_fragment.ambient",
            "mcp_fragment.entrance",
            "mcp_fragment.shard_core",
            "mcp_fragment.resonance_field",
        ],
        "tier": 3,
    },
    "gridcore": {
        "archetype_id": "gridcore",
        "level_band": (25, 35),
        "room_count_range": (8, 14),
        "topology_options": ["branching"],
        "daemon_palette": [
            "typeclasses.daemon_variants.GridcoreElite",
        ],
        "repop_cadence_sec": 45,
        "default_flavor_keys": [
            "gridcore.ambient",
            "gridcore.entrance",
            "gridcore.nexus",
            "gridcore.core_breach",
            "gridcore.inner_sanctum",
        ],
        "tier": 3,
    },
}

# Required keys every archetype must have (used by tests + generator).
REQUIRED_KEYS: frozenset[str] = frozenset({
    "archetype_id",
    "level_band",
    "room_count_range",
    "topology_options",
    "daemon_palette",
    "repop_cadence_sec",
    "default_flavor_keys",
    "tier",
})


def get_archetype(archetype_id: str) -> dict[str, Any]:
    """Return the archetype prototype dict for *archetype_id*.

    Args:
        archetype_id: Slug string matching a key in ARCHETYPES.

    Returns:
        The archetype dict (a reference — do not mutate).

    Raises:
        KeyError: When *archetype_id* is not a known archetype slug.
    """
    if archetype_id not in ARCHETYPES:
        raise KeyError(
            f"Unknown archetype {archetype_id!r}. "
            f"Valid ids: {sorted(ARCHETYPES)}"
        )
    return ARCHETYPES[archetype_id]
