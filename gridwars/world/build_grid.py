"""
GridWars.run -- initial sector build script.

Run from repo root:
    cd gridwars && ../.venv/bin/python -c "import os, django; \\
      os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.conf.settings'); \\
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
}

# ---------------------------------------------------------------------------
# Exit definitions: (from_slug, to_slug, exit_name, aliases)
# ---------------------------------------------------------------------------

EXITS = [
    ("users_sector",       "lightcycle_causeway", "north", ["n"]),
    ("lightcycle_causeway", "users_sector",        "south", ["s"]),
    ("lightcycle_causeway", "daemon_gate",          "east",  ["e"]),
    ("daemon_gate",         "lightcycle_causeway",  "west",  ["w"]),
    ("users_sector",       "archive_node",          "east",  ["e"]),
    ("archive_node",        "users_sector",          "west",  ["w"]),
    ("daemon_gate",         "combat_grid",           "north", ["n"]),
    ("combat_grid",         "daemon_gate",           "south", ["s"]),
    ("uplink_node",         "users_sector",          "jack-in", ["ji"]),
    ("users_sector",        "uplink_node",           "return",  []),
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


# ---------------------------------------------------------------------------
# Entry point (called by evennia batchcode)
# ---------------------------------------------------------------------------

def build():
    """Create the GridWars sectors, connect them with exits, spawn the Welcome Program, and instantiate all 42 zones."""
    rooms = {}
    for slug, spec in SECTORS.items():
        rooms[slug] = _get_or_create_room(slug, spec)

    exits_built = 0
    for from_slug, to_slug, name, aliases in EXITS:
        _ensure_exit(from_slug, rooms[from_slug], rooms[to_slug], name, aliases)
        exits_built += 1

    _spawn_welcome_program(rooms["uplink_node"])

    print(
        f"GridWars world build complete: "
        f"{len(rooms)} sectors, {exits_built} exits "
        f"(tag='{TAG_KEY}', category='{CATEGORY}')."
    )

    # Instantiate the 42 procedurally-generated zone variants (e19.7).
    from world.zones.build_zones import build_all_zones
    build_all_zones()


if __name__ == "__main__":
    build()
