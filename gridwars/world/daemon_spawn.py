"""
Daemon spawn helper. Call from Django shell after world build:

    from world.daemon_spawn import spawn_initial_daemon
    spawn_initial_daemon()

DA2 will hook this into the patrol Script lifecycle. DA1 just exposes
the callable so the Daemon can be created and tagged for idempotent
rebuild.
"""
from evennia.utils.create import create_object
from evennia.utils.search import search_tag


def spawn_initial_daemon():
    """Spawn one Daemon at Daemon Gate if not already present. Idempotent."""
    existing = search_tag("initial_daemon", category="world_build")
    if existing:
        return existing[0]
    gate = search_tag("daemon_gate", category="world_build")
    if not gate:
        raise RuntimeError("daemon_gate sector not built; run world.build_grid first")
    daemon = create_object(
        "typeclasses.daemons.Daemon",
        key="Daemon-0001",
        location=gate[0],
    )
    daemon.tags.add("initial_daemon", category="world_build")
    daemon.tags.add("gridwars-core", category="world_build")
    return daemon
