"""
GridWars.run -- initial sector build script.

Run from repo root:
    cd gridwars && ../.venv/bin/python -c "import os, django; \
      os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.conf.settings'); \
      django.setup(); from world import build_grid; build_grid.build()"

(Note: `evennia batchcode` is an in-game command for authenticated sessions,
 not a CLI subcommand. The Django shell setup above correctly initializes
 Evennia's context and executes the build.)

Idempotency strategy: skip-if-exists.
Each room and exit is looked up by its unique slug tag before creation.
Re-running the script will reuse existing objects rather than duplicating them.
Every room and exit is tagged with:
    key="<slug>",    category="world_build"  (unique identity tag)
    key="gridwars-core", category="world_build"  (membership tag for bulk ops)
"""
from evennia.utils.create import create_object
from evennia.utils.search import search_tag

CATEGORY = "world_build"
TAG_KEY = "gridwars-core"

TYPECLASS_ROOM = "evennia.objects.objects.DefaultRoom"
TYPECLASS_EXIT = "evennia.objects.objects.DefaultExit"
TYPECLASS_UPLINK_NODE = "typeclasses.welcome_program.UplinkNodeRoom"
TYPECLASS_WELCOME_PROGRAM = "typeclasses.welcome_program.WelcomeProgram"
TYPECLASS_LEVEL_GATE_EXIT = "typeclasses.exits.LevelGateExit"

# ---------------------------------------------------------------------------
# Sector definitions
# ---------------------------------------------------------------------------

SECTORS = {
    "users_sector": {
        "key": "Users' Sector",
        "desc": (
            "Rows of terminals glow a steady blue-white against the dark substrate, "
            "each screen alive with scrolling identity-disc readouts and spawn queues. "
            "Civilian programs move between the workstations in short bursts of light, "
            "their code signatures trailing faint neon halos on the grid floor. "
            "This is the first place a newly derezzed program opens its eyes -- "
            "the hum of the Grid vibrating through every compiled bone."
        ),
    },
    "lightcycle_causeway": {
        "key": "Lightcycle Causeway",
        "desc": (
            "The causeway stretches in a perfect vanishing line toward both horizons, "
            "its surface etched with luminescent guide-tracks that pulse in sync with "
            "the Grid's clock cycle. Residual light trails from recent runs bleed "
            "across the pavement in smears of orange and cyan. "
            "Speed is not a luxury here -- it is the language programs speak to survive. "
            "The air carries the sharp scent of ozone and burnt data packets."
        ),
    },
    "daemon_gate": {
        "key": "Daemon Gate",
        "desc": (
            "The gate rises as a monolith of corrupted geometry, its edges flickering "
            "between two states as though the Grid cannot agree on what shape it should hold. "
            "Fragments of derezzed code drift upward in slow spirals, dissolving before "
            "they reach the ceiling. Programs crossing this threshold speak in lower tones, "
            "aware that daemons patrol beyond the boundary and the rules compress. "
            "A low, arhythmic pulse emanates from somewhere deep inside the structure."
        ),
    },
    "archive_node": {
        "key": "Archive Node",
        "desc": (
            "Vaulted stacks of encoded memory towers reach upward, their surfaces "
            "dense with compressed data rendered as frozen light. "
            "The silence here is deliberate -- a design choice by whatever User "
            "assembled this place to hold the Grid's oldest records intact. "
            "Access panels line the walls at intervals, each locked behind multi-layer "
            "identity verification. Even the dust feels archived."
        ),
    },
    "combat_grid": {
        "key": "Combat Grid",
        "desc": (
            "The arena floor is a flat plane of jet-black substrate divided by "
            "bright-white grid lines into perfect squares, each one a potential "
            "kill zone. Observation pylons ring the perimeter, dark and waiting, "
            "built for crowds that have not yet assembled. "
            "The air tastes of latent electricity and the faint residue of past "
            "derezz events still scorched into the surface. "
            "This place was built for one purpose: to determine which programs persist."
        ),
    },
    "uplink_node": {
        "key": "Uplink Node",
        "typeclass": TYPECLASS_UPLINK_NODE,
        "desc": (
            "Awareness arrives in pulses. "
            "The first thing a new program perceives is the Grid clock -- "
            "a deep subsonic tick that measures existence in discrete cycles, "
            "steady and merciless as a heartbeat carved from pure logic. "
            "The Uplink Node is a featureless antechamber of luminous white panels "
            "divided by hairline seams of electric blue, every surface humming "
            "at a frequency just below the threshold of comprehension. "
            "A terminal hum permeates the space, rising and falling with the load "
            "of programs initializing nearby -- you are not alone in this awakening. "
            "Slender columns of encoded light descend from the vaulted ceiling "
            "like rainfall captured mid-fall, each column a stream of identity "
            "data cascading into newly spawned forms. "
            "Your own code resolves last: integrity intact, disc seated, "
            "faction tag still writing itself to your registers. "
            "Somewhere beyond the glowing seam at the far wall, "
            "the pulse of Users' Sector is already audible -- "
            "a wider, louder world waiting for you to jack in."
        ),
    },
    "grid_junction": {
        "key": "Grid Junction",
        "desc": (
            "The hub expands in all directions, a hexagonal plaza of white-lit "
            "substrate suspended above the deep Grid dark. "
            "Eight radial corridors branch outward from the central dais, each "
            "mouth framed by a tall archway of pulsing circuit-trace in a "
            "different frequency: cyan for the open datastreams, amber for the "
            "archive vaults, red-orange for the ICE perimeter. "
            "Status readouts scroll along the archway columns in cascading "
            "columns of green glyphs -- zone load, threat tier, last-ping. "
            "A faint directional hum resonates through the floor plates, "
            "different for each corridor, a tuned reminder that deeper means "
            "harder and the Grid knows exactly who is strong enough to pass. "
            "Scattered programs cluster near the archways in small knots, "
            "studying the readouts, recalibrating their discs before stepping "
            "through. Nobody moves without a plan. Not here."
        ),
    },
}

# ---------------------------------------------------------------------------
# Exit definitions: (from_slug, to_slug, exit_name, aliases)
# ---------------------------------------------------------------------------

EXITS = [
    ("users_sector",        "lightcycle_causeway",  "north",   ["n"]),
    ("lightcycle_causeway", "users_sector",          "south",   ["s"]),
    ("lightcycle_causeway", "daemon_gate",            "east",    ["e"]),
    ("daemon_gate",         "lightcycle_causeway",    "west",    ["w"]),
    ("users_sector",        "archive_node",           "east",    ["e"]),
    ("archive_node",        "users_sector",           "west",    ["w"]),
    ("daemon_gate",         "combat_grid",            "north",   ["n"]),
    ("combat_grid",         "daemon_gate",            "south",   ["s"]),
    ("uplink_node",         "users_sector",           "jack-in", ["ji"]),
    ("users_sector",        "uplink_node",            "return",  []),
    # Grid Junction -- gateway to all 42 zones (e19.8)
    ("daemon_gate",         "grid_junction",          "deeper",  ["dp"]),
    ("grid_junction",       "daemon_gate",            "back",    ["bk"]),
]

# ---------------------------------------------------------------------------
# Tier-1 zone entries from Grid Junction (e19.8)
#
# Each tuple: (exit_name, aliases, archetype_id, variant_index, min_level)
#
# min_level maps to disc level (1-5, from typeclasses.discs.XP_THRESHOLDS).
# Tier-1 zones (Datastream level_band 1-5): min_level=1 -- any disc qualifies.
# Archive Node (level_band 3-8): min_level=2 -- disc must reach L2 (100 XP).
# ICE Wall (level_band 6-12): min_level=3 -- disc must reach L3 (300 XP).
# ---------------------------------------------------------------------------

JUNCTION_ZONE_EXITS = [
    # 4 Datastream variants
    ("datastream-north", ["dsn"], "datastream",   0, 1),
    ("datastream-south", ["dss"], "datastream",   1, 1),
    ("datastream-east",  ["dse"], "datastream",   2, 1),
    ("datastream-west",  ["dsw"], "datastream",   3, 1),
    # 2 Archive Node variants
    ("archive-alpha",    ["ara"], "archive_node", 0, 2),
    ("archive-beta",     ["arb"], "archive_node", 1, 2),
    # 2 ICE Wall variants
    ("ice-wall-alpha",   ["iwa"], "ice_wall",     0, 3),
    ("ice-wall-beta",    ["iwb"], "ice_wall",     1, 3),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _exit_slug(from_slug, exit_name):
    """Unique slug for a directional exit from a given room."""
    return f"{from_slug}__exit__{exit_name}"


def _get_or_create_room(slug, spec):
    """Return existing room by slug tag or create a new one."""
    existing = search_tag(key=slug, category=CATEGORY)
    if existing:
        return existing[0]
    typeclass = spec.get("typeclass", TYPECLASS_ROOM)
    room = create_object(
        typeclass=typeclass,
        key=spec["key"],
        nohome=True,
        attributes=[("desc", spec["desc"])],
        tags=[
            (slug, CATEGORY),
            (TAG_KEY, CATEGORY),
        ],
    )
    return room


def _spawn_welcome_program(uplink_room):
    """Spawn a single WelcomeProgram in *uplink_room* if not already present.

    Idempotent: tagged with ``welcome-program / world_build`` so re-running
    build() skips creation if one already exists.
    """
    existing = search_tag("welcome-program", category=CATEGORY)
    if existing:
        return existing[0]
    npc = create_object(
        TYPECLASS_WELCOME_PROGRAM,
        key="Welcome Program",
        location=uplink_room,
    )
    # Tag with the NPC-specific slug only — NOT gridwars-core.
    # gridwars-core is a geometry tag (rooms + exits); NPCs must not
    # appear in build_grid room/exit counts.
    npc.tags.add("welcome-program", category=CATEGORY)
    return npc


def _ensure_exit(from_slug, from_room, to_room, exit_name, aliases):
    """Create a directional exit if one with the same slug tag does not exist."""
    slug = _exit_slug(from_slug, exit_name)
    existing = search_tag(key=slug, category=CATEGORY)
    if existing:
        return existing[0]
    exit_obj = create_object(
        typeclass=TYPECLASS_EXIT,
        key=exit_name,
        aliases=aliases,
        location=from_room,
        destination=to_room,
        tags=[
            (slug, CATEGORY),
            (TAG_KEY, CATEGORY),
        ],
    )
    return exit_obj


def _ensure_level_gate_exit(from_slug, from_room, to_room, exit_name, aliases, min_level):
    """Create a LevelGateExit if one with the same slug tag does not exist.

    Idempotent: if the exit already exists it is returned unchanged.
    """
    slug = _exit_slug(from_slug, exit_name)
    existing = search_tag(key=slug, category=CATEGORY)
    if existing:
        return existing[0]
    exit_obj = create_object(
        typeclass=TYPECLASS_LEVEL_GATE_EXIT,
        key=exit_name,
        aliases=aliases,
        location=from_room,
        destination=to_room,
        attributes=[("min_level", min_level)],
        tags=[
            (slug, CATEGORY),
            (TAG_KEY, CATEGORY),
        ],
    )
    return exit_obj


def build_junction_topology(junction_room):
    """Wire Grid Junction exits to Tier-1 zone entry rooms.

    Called from build() after build_all_zones() (e19.7) has populated zone
    rooms.  Safe to call when zones do not yet exist -- any zone whose entry
    room tag is absent is silently skipped (no error).

    For each entry in JUNCTION_ZONE_EXITS:
      - Looks up the zone's first room by its tag "room:<arch>:<var>:r0".
      - Creates a LevelGateExit from Grid Junction to that room.
      - Creates a plain return exit from that room back to Grid Junction.

    Args:
        junction_room: The Grid Junction room object.

    Returns:
        int: Number of new exits created (forward + return combined).
    """
    exits_created = 0
    zone_category = "world_build"  # matches build_zones.ZONE_CATEGORY

    from world.zones.generator import generate_zone

    for exit_name, aliases, archetype_id, variant_index, min_level in JUNCTION_ZONE_EXITS:
        # The entry room is the first room in the generated spec (index 0).
        # Its slug is {archetype_id}_v{variant_index}_{role} — determined by
        # generate_zone (pure, no I/O), so safe to call here.
        spec = generate_zone(archetype_id, variant_index)
        entry_slug = spec.rooms[0].slug
        entry_tag = f"room:{archetype_id}:{variant_index}:{entry_slug}"
        zone_rooms = search_tag(key=entry_tag, category=zone_category)
        if not zone_rooms:
            # Zone not yet built (e19.7 not run, or test environment) -- skip.
            continue
        zone_entry = zone_rooms[0]

        # Forward: Grid Junction -> zone entry (level-gated).
        forward_slug = _exit_slug("grid_junction", exit_name)
        if not search_tag(key=forward_slug, category=CATEGORY):
            _ensure_level_gate_exit(
                from_slug="grid_junction",
                from_room=junction_room,
                to_room=zone_entry,
                exit_name=exit_name,
                aliases=aliases,
                min_level=min_level,
            )
            exits_created += 1

        # Return: zone entry -> Grid Junction (plain, no gate).
        return_slug = f"zone_entry_{archetype_id}_{variant_index}__exit__grid-junction"
        existing_return = search_tag(key=return_slug, category=CATEGORY)
        if not existing_return:
            create_object(
                typeclass=TYPECLASS_EXIT,
                key="grid-junction",
                aliases=["gj"],
                location=zone_entry,
                destination=junction_room,
                tags=[
                    (return_slug, CATEGORY),
                    (TAG_KEY, CATEGORY),
                ],
            )
            exits_created += 1

    return exits_created


# ---------------------------------------------------------------------------
# Entry point (called by evennia batchcode)
# ---------------------------------------------------------------------------

def build():
    """Create the GridWars sectors, connect them with exits, spawn the Welcome Program, wire junction topology, and instantiate all 42 zones."""
    rooms = {}
    for slug, spec in SECTORS.items():
        rooms[slug] = _get_or_create_room(slug, spec)

    exits_built = 0
    for from_slug, to_slug, name, aliases in EXITS:
        _ensure_exit(from_slug, rooms[from_slug], rooms[to_slug], name, aliases)
        exits_built += 1

    _spawn_welcome_program(rooms["uplink_node"])

    # Instantiate the 42 procedurally-generated zone variants (e19.7).
    from world.zones.build_zones import build_all_zones
    build_all_zones()

    # Wire Grid Junction -> zone entry rooms (requires e19.7 zones to exist).
    junction_exits = build_junction_topology(rooms["grid_junction"])

    print(
        f"GridWars world build complete: "
        f"{len(rooms)} sectors, {exits_built} exits "
        f"(tag='{TAG_KEY}', category='{CATEGORY}'). "
        f"Junction topology: {junction_exits} zone-entry exits wired."
    )


if __name__ == "__main__":
    build()
