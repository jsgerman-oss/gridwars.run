"""
GridWars.run — per-zone repop ticker (e19.5).

ZoneRepopScript is an Evennia Script that runs on a fixed cadence (taken
from the archetype's ``repop_cadence_sec``) and refills daemons in
zone-tagged rooms that are not currently in combat.

Zone tagging convention (set by the zone builder / build_grid):
    room.tags.add(zone_id, category="zone")          — membership
    room.db.zone_archetype  str    — archetype slug (e.g. "datastream")
    room.db.zone_daemon_palette  list[str]  — typeclass paths for daemons
    room.db.zone_level_band      (int, int) — (min_level, max_level)
    room.db.zone_daemon_target   int        — desired daemon count per room

Script stored attributes (set at creation):
    self.db.zone_id        str  — zone membership tag
    self.db.zone_archetype str  — archetype slug (for display / reload)
    self.db.level_band_min int  — band floor (default 1)
    self.db.level_band_max int  — band ceiling (default 5)
    self.db.daemon_palette list[str]  — typeclass paths to pick from
    self.db.daemon_target  int  — desired daemon count per room

Scaling rule (hybrid model from epic-19 design):
    target_level = clamp(max_player_level_in_zone, band_min, band_max)
    If no players in zone → use band_min.

Safety rules (all inside at_repeat):
    1. Skip rooms with combat_active flag set.
    2. Skip rooms where daemon count >= zone_daemon_target.
    3. Skip if zone has no players AND last_player_visit > LOW_ACTIVITY_TIMEOUT.
       (slow-mode: reduces unnecessary ticks on empty zones)
    4. Idempotent: spawn at most one daemon per room per tick.

No persistent daemon references are stored here; each tick queries live DB.
"""

from __future__ import annotations

import random
import time
from typing import Optional

from evennia.scripts.scripts import DefaultScript
from evennia.utils.create import create_object
from evennia.utils.search import search_tag

from world.room_state import is_room_in_combat

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Zone with no player activity for this many seconds drops to slow-mode.
LOW_ACTIVITY_TIMEOUT = 600  # 10 minutes

# Default daemon count target per room when not set on the script.
DEFAULT_DAEMON_TARGET = 1

# Fallback repop cadence when not configured at script-creation time.
DEFAULT_CADENCE_SEC = 90


# ---------------------------------------------------------------------------
# Helpers (module-level so tests can import them directly)
# ---------------------------------------------------------------------------

def _get_zone_rooms(zone_id: str):
    """Return all rooms tagged with *zone_id* in the 'zone' category."""
    return list(search_tag(zone_id, category="zone"))


def _live_daemon_count(room) -> int:
    """Count Daemon-faction objects present in *room*."""
    from typeclasses.daemons import Daemon

    return sum(1 for obj in room.contents if isinstance(obj, Daemon))


def _player_levels_in_zone(rooms) -> list[int]:
    """Collect levels of all Account-puppeted characters across *rooms*."""
    levels = []
    for room in rooms:
        for obj in room.contents:
            if hasattr(obj, "account") and obj.account and hasattr(obj, "db"):
                lvl = getattr(obj.db, "level", None)
                if lvl is not None:
                    levels.append(int(lvl))
    return levels


def _clamp(value: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, value))


def _pick_typeclass(daemon_palette: list[str]) -> str:
    """Pick a random daemon typeclass from *daemon_palette*."""
    if not daemon_palette:
        return "typeclasses.daemons.Daemon"
    return random.choice(daemon_palette)


def _daemon_key(typeclass: str) -> str:
    """Derive a human-readable key from the typeclass path tail."""
    return typeclass.rsplit(".", 1)[-1]


def spawn_daemon_in_room(room, typeclass: str, target_level: int):
    """
    Spawn a single daemon of *typeclass* in *room*, scaled to *target_level*.

    Calls ``scale_to_level(target_level)`` on the daemon if the method exists
    (provided by ``_DaemonVariantMixin`` on all variant classes).

    Returns the spawned daemon object.
    """
    daemon = create_object(
        typeclass=typeclass,
        key=_daemon_key(typeclass),
        location=room,
    )
    if hasattr(daemon, "scale_to_level"):
        daemon.scale_to_level(target_level)
    daemon.tags.add("gridwars-core", category="world_build")
    return daemon


# ---------------------------------------------------------------------------
# Script
# ---------------------------------------------------------------------------

class ZoneRepopScript(DefaultScript):
    """
    Per-zone repop ticker. One instance per zone, started during world build.

    Required setup (caller must set before or at creation):
        script.db.zone_id        — zone membership tag string
        script.db.zone_archetype — archetype slug (human label)

    Optional (defaults applied at tick time when not set):
        script.db.level_band_min — int, default 1
        script.db.level_band_max — int, default 5
        script.db.daemon_palette — list[str], default ["typeclasses.daemons.Daemon"]
        script.db.daemon_target  — int per room, default DEFAULT_DAEMON_TARGET
    """

    def at_script_creation(self):
        self.key = "zone_repop"
        self.desc = "Zone daemon repop ticker"
        self.interval = DEFAULT_CADENCE_SEC
        self.persistent = True
        self.start_delay = True  # wait one full interval before first tick

    # ------------------------------------------------------------------
    # Attribute accessors with safe defaults
    # ------------------------------------------------------------------

    def _zone_id(self) -> Optional[str]:
        return self.db.zone_id

    def _level_band(self) -> tuple[int, int]:
        lo = self.db.level_band_min or 1
        hi = self.db.level_band_max or 5
        return (int(lo), int(hi))

    def _daemon_palette(self) -> list[str]:
        palette = self.db.daemon_palette
        if palette:
            return list(palette)
        return ["typeclasses.daemons.Daemon"]

    def _daemon_target(self) -> int:
        t = self.db.daemon_target
        return int(t) if t is not None else DEFAULT_DAEMON_TARGET

    # ------------------------------------------------------------------
    # Zone-level activity check (slow-mode guard)
    # ------------------------------------------------------------------

    def _zone_is_inactive(self, rooms) -> bool:
        """Return True if zone has been player-free for > LOW_ACTIVITY_TIMEOUT.

        A zone is active when either:
          - at least one Account-puppeted character is currently in any room, OR
          - at least one room has a last_player_visit timestamp within the timeout.
        """
        for room in rooms:
            for obj in room.contents:
                if hasattr(obj, "account") and obj.account:
                    return False

        now = time.time()
        for room in rooms:
            last_visit = room.db.last_player_visit
            if last_visit is not None:
                if now - float(last_visit) < LOW_ACTIVITY_TIMEOUT:
                    return False

        return True

    # ------------------------------------------------------------------
    # Main tick
    # ------------------------------------------------------------------

    def at_repeat(self):
        """Called every self.interval seconds. Core repop logic lives here."""
        zone_id = self._zone_id()
        if not zone_id:
            return

        rooms = _get_zone_rooms(zone_id)
        if not rooms:
            return

        if self._zone_is_inactive(rooms):
            return

        band_min, band_max = self._level_band()
        player_levels = _player_levels_in_zone(rooms)
        if player_levels:
            target_level = _clamp(max(player_levels), band_min, band_max)
        else:
            target_level = band_min

        palette = self._daemon_palette()
        daemon_target = self._daemon_target()

        for room in rooms:
            self._tick_room(room, palette, daemon_target, target_level)

    def _tick_room(self, room, palette, daemon_target, target_level):
        """Evaluate one room and spawn at most one daemon if appropriate."""
        # Safety rule 1: skip rooms with active combat.
        if is_room_in_combat(room):
            return

        # Safety rule 2: skip if daemon count already at or above target.
        if _live_daemon_count(room) >= daemon_target:
            return

        typeclass = _pick_typeclass(palette)
        spawn_daemon_in_room(room, typeclass, target_level)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def is_valid(self) -> bool:
        """Self-terminate if zone has been deleted (no rooms tagged with zone_id)."""
        zone_id = self._zone_id()
        if not zone_id:
            return True  # Not yet configured; keep running.
        return len(_get_zone_rooms(zone_id)) > 0
