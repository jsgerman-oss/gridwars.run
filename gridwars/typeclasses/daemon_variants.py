"""
GridWars.run — Daemon variant typeclasses (e19.3).

Eight archetype subclasses of Daemon. Each declares:
  - Base stat profile: integrity_base, energy_base, damage_base
  - AI tuning knobs:   patrol_radius, sense_range, engage_threshold
  - scale_to_level(target_level)  — writes scaled attrs on the object;
    called by the repop ticker (e19.5) at spawn time.

Scaling formula (simple linear):
    integrity = integrity_base + (target_level - 1) * integrity_per_level
    energy    = energy_base    + (target_level - 1) * energy_per_level
    damage    = damage_base    + (target_level - 1) * damage_per_level

Level 1 is baseline; the multipliers are per-variant tuning knobs.
The repop ticker calls scale_to_level immediately after object creation,
before the daemon is placed in a zone.

Patrol / sense / engage AI is inherited from DaemonPatrol script (scripts.py)
and Daemon.reset_for_respawn(); no behavior is overridden here.

Variant roster (archetype → zone):
    StrayPacket         Datastream
    ReadOnlySentry      Archive Node
    ICEPicket           ICE Wall
    ForgeDaemon         Shard Foundry
    MutatedCacheDaemon  Corrupted Cache
    FragmentGuardian    MCP Fragment
    GridcoreElite       Gridcore
    JunctionRoamer      Junction Plaza (mixed; thin wrapper over base Daemon)
"""

from typeclasses.daemons import Daemon


# ---------------------------------------------------------------------------
# Base-stat mixin — keeps scale_to_level DRY across variants
# ---------------------------------------------------------------------------

class _DaemonVariantMixin:
    """
    Mixin that adds scale_to_level() to any Daemon subclass.

    Subclasses set class-level tuning knobs; at_object_creation tags
    the archetype so zone builders and the repop ticker can filter.
    """

    # --- Override in each subclass ---
    archetype_tag: str = ""          # world_build tag, e.g. "datastream"

    integrity_base: int = 40
    energy_base: int = 30
    damage_base: int = 8

    integrity_per_level: int = 5
    energy_per_level: int = 2
    damage_per_level: int = 1

    patrol_radius: int = 2           # sectors; used by repop ticker
    sense_range: int = 1             # rooms deep for sensing players
    engage_threshold: int = 1        # min targets to trigger engage

    def at_object_creation(self):
        super().at_object_creation()
        # Stamp archetype tag so zone builders can query by type.
        if self.archetype_tag:
            self.tags.add(self.archetype_tag, category="daemon_archetype")
        # Write un-scaled (level-1) stats immediately so the object is
        # never in an undefined stat state before scale_to_level fires.
        self.scale_to_level(1)

    def scale_to_level(self, target_level: int) -> None:
        """
        Write level-scaled stats onto this daemon.

        Args:
            target_level: Positive integer; 1 = base stats, higher = stronger.
        """
        if target_level < 1:
            target_level = 1
        lvl = target_level - 1
        self.integrity = self.integrity_base + lvl * self.integrity_per_level
        self.energy = self.energy_base + lvl * self.energy_per_level
        self.db.damage = self.damage_base + lvl * self.damage_per_level


# ---------------------------------------------------------------------------
# Variant 1 — StrayPacket  (Datastream)
# Fast, fragile scout. Low HP, moderate damage, wide patrol.
# ---------------------------------------------------------------------------

class StrayPacket(_DaemonVariantMixin, Daemon):
    """Errant data fragment drifting through Datastream sectors."""

    archetype_tag = "datastream"

    integrity_base = 25
    energy_base = 40
    damage_base = 6

    integrity_per_level = 3
    energy_per_level = 3
    damage_per_level = 1

    patrol_radius = 4
    sense_range = 2
    engage_threshold = 1


# ---------------------------------------------------------------------------
# Variant 2 — ReadOnlySentry  (Archive Node)
# Defensive, high HP, low damage, stays put (patrol_radius=1).
# ---------------------------------------------------------------------------

class ReadOnlySentry(_DaemonVariantMixin, Daemon):
    """Immovable guardian process locked to read-only archive sectors."""

    archetype_tag = "archive_node"

    integrity_base = 80
    energy_base = 20
    damage_base = 5

    integrity_per_level = 8
    energy_per_level = 1
    damage_per_level = 1

    patrol_radius = 1
    sense_range = 1
    engage_threshold = 1


# ---------------------------------------------------------------------------
# Variant 3 — ICEPicket  (ICE Wall)
# Heavy-hitter. High HP, high damage, slow patrol.
# ---------------------------------------------------------------------------

class ICEPicket(_DaemonVariantMixin, Daemon):
    """Intrusion Countermeasure node anchored to ICE Wall sectors."""

    archetype_tag = "ice_wall"

    integrity_base = 60
    energy_base = 30
    damage_base = 14

    integrity_per_level = 6
    energy_per_level = 2
    damage_per_level = 2

    patrol_radius = 2
    sense_range = 1
    engage_threshold = 1


# ---------------------------------------------------------------------------
# Variant 4 — ForgeDaemon  (Shard Foundry)
# Mid-tier balanced fighter. Standard tuning.
# ---------------------------------------------------------------------------

class ForgeDaemon(_DaemonVariantMixin, Daemon):
    """Industrial process hammering out corrupted shards in foundry sectors."""

    archetype_tag = "shard_foundry"

    integrity_base = 50
    energy_base = 35
    damage_base = 10

    integrity_per_level = 5
    energy_per_level = 2
    damage_per_level = 2

    patrol_radius = 2
    sense_range = 1
    engage_threshold = 1


# ---------------------------------------------------------------------------
# Variant 5 — MutatedCacheDaemon  (Corrupted Cache)
# Unpredictable. Moderate HP, high energy, high damage, wide sense.
# ---------------------------------------------------------------------------

class MutatedCacheDaemon(_DaemonVariantMixin, Daemon):
    """Corrupted cache entry — behaviour degraded, aggression spiked."""

    archetype_tag = "corrupted_cache"

    integrity_base = 40
    energy_base = 50
    damage_base = 12

    integrity_per_level = 4
    energy_per_level = 4
    damage_per_level = 2

    patrol_radius = 3
    sense_range = 2
    engage_threshold = 1


# ---------------------------------------------------------------------------
# Variant 6 — FragmentGuardian  (MCP Fragment)
# Elite single-target defender. Very high HP, high damage, limited patrol.
# ---------------------------------------------------------------------------

class FragmentGuardian(_DaemonVariantMixin, Daemon):
    """Ancient process shard guarding MCP fragment sectors."""

    archetype_tag = "mcp_fragment"

    integrity_base = 90
    energy_base = 40
    damage_base = 16

    integrity_per_level = 10
    energy_per_level = 3
    damage_per_level = 2

    patrol_radius = 1
    sense_range = 2
    engage_threshold = 1


# ---------------------------------------------------------------------------
# Variant 7 — GridcoreElite  (Gridcore)
# Boss-tier. Maximum HP, maximum damage, wide sense. End-game threat.
# ---------------------------------------------------------------------------

class GridcoreElite(_DaemonVariantMixin, Daemon):
    """Core system process — the apex predator of the Grid."""

    archetype_tag = "gridcore"

    integrity_base = 120
    energy_base = 60
    damage_base = 20

    integrity_per_level = 12
    energy_per_level = 5
    damage_per_level = 3

    patrol_radius = 3
    sense_range = 3
    engage_threshold = 1


# ---------------------------------------------------------------------------
# Variant 8 — JunctionRoamer  (Junction Plaza — mixed)
# Thin wrapper; uses all base Daemon defaults. Junction zones host
# mixed traffic; no archetype specialisation required.
# ---------------------------------------------------------------------------

class JunctionRoamer(_DaemonVariantMixin, Daemon):
    """Generic daemon variant found in Junction Plaza transit sectors."""

    archetype_tag = "junction_plaza"

    # Base stats match the Daemon defaults — no tuning needed.
    integrity_base = 40
    energy_base = 30
    damage_base = 8

    integrity_per_level = 5
    energy_per_level = 2
    damage_per_level = 1

    patrol_radius = 2
    sense_range = 1
    engage_threshold = 1
