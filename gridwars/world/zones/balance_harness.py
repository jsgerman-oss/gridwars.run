"""
GridWars.run — Balance-tuning harness (e19.10).

Pure-Python, no DB, no Evennia runtime.  Simulates a level-N player
walking a zone of each archetype and killing daemons, then reports:

  - kill_rate         fraction of fights the player wins (integrity > 0)
  - avg_ttk_ticks     average ticks (strikes) to kill the daemon
  - xp_per_kill       average XP awarded per daemon kill (including soft cap)
  - xp_per_hour       estimated XP/hour at a fixed strikes-per-minute rate
  - daemon_dps        damage the daemon deals per tick to the player

Typical usage::

    from world.zones.balance_harness import simulate_combat, BalanceReport
    report = simulate_combat(player_lvl=5, daemon_archetype="datastream", daemon_lvl=3)
    print(report)

CLI usage (designers)::

    python bin/gridwars-balance.py --player-level 5 --json
    python bin/gridwars-balance.py --player-level 10 --archetype ice_wall

Design doc: /tmp/gridwars-epic-19-design.md §5 (EXP curve) + §3 (archetypes).
"""

from __future__ import annotations

import dataclasses
import json
import math
import random
from typing import Optional

from world.zones.archetypes import ARCHETYPES
from world.zones.exp import kill_xp, strike_xp


# ---------------------------------------------------------------------------
# Simulation tuning constants — adjust here for balance experimentation
# ---------------------------------------------------------------------------

#: Player's base integrity at level 1.
PLAYER_INTEGRITY_BASE: int = 100

#: Player gains this many integrity points per level above 1.
PLAYER_INTEGRITY_PER_LEVEL: int = 20

#: Player's base damage per strike (mirrors world.combat.BASE_DAMAGE).
PLAYER_BASE_DAMAGE: int = 10

#: Max random jitter added to each player strike (mirrors world.combat.RANDOM_BONUS_MAX).
PLAYER_RANDOM_BONUS_MAX: int = 5

#: Player strikes per minute (approximates realistic play cadence with cooldown).
PLAYER_STRIKES_PER_MINUTE: float = 12.0

#: How many ticks pass between daemon counter-strikes (daemon attacks every N player ticks).
DAEMON_COUNTER_FREQUENCY: int = 2


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class BalanceReport:
    """Results from a single simulate_combat() run."""

    archetype: str
    daemon_level: int
    player_level: int
    n_runs: int

    # Core metrics
    kill_rate: float           # 0.0 – 1.0
    avg_ttk_ticks: float       # average ticks to kill the daemon (only counting kills)
    xp_per_kill: float         # average XP per successful kill
    xp_per_hour: float         # estimated XP/hour based on PLAYER_STRIKES_PER_MINUTE
    daemon_dps: float          # average damage daemon deals to player per tick

    # Diagnostic fields
    player_survival_rate: float  # fraction of fights player reaches kill without dying
    avg_player_integrity_left: float  # mean player integrity after a kill (kills only)
    zone_band_min: int           # archetype level_band[0] used for XP calc

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def __str__(self) -> str:
        return (
            f"BalanceReport({self.archetype} | player L{self.player_level} "
            f"vs daemon L{self.daemon_level})\n"
            f"  kill_rate          : {self.kill_rate:.1%}\n"
            f"  avg TTK (ticks)    : {self.avg_ttk_ticks:.1f}\n"
            f"  xp_per_kill        : {self.xp_per_kill:.1f}\n"
            f"  xp_per_hour        : {self.xp_per_hour:.0f}\n"
            f"  daemon_dps         : {self.daemon_dps:.2f}\n"
            f"  player_survival    : {self.player_survival_rate:.1%}\n"
            f"  avg integrity left : {self.avg_player_integrity_left:.1f}"
        )


# ---------------------------------------------------------------------------
# Stat helpers (pure, no DB)
# ---------------------------------------------------------------------------

def _daemon_stats(archetype_id: str, daemon_level: int) -> tuple[int, int, int]:
    """
    Return (integrity, energy, damage) for a daemon of the given archetype
    and level, computed from class-level constants in daemon_variants.py.

    Rather than importing the Evennia typeclass (which requires DB), we
    hard-code the same arithmetic here, mirroring _DaemonVariantMixin.scale_to_level.

    Returns:
        (integrity, energy, damage) all >= 1.
    """
    # Stat profiles — must stay in sync with daemon_variants.py
    PROFILES: dict[str, dict] = {
        "datastream": {
            "integrity_base": 25, "energy_base": 40, "damage_base": 6,
            "integrity_per_level": 3, "energy_per_level": 3, "damage_per_level": 1,
        },
        "archive_node": {
            "integrity_base": 80, "energy_base": 20, "damage_base": 5,
            "integrity_per_level": 8, "energy_per_level": 1, "damage_per_level": 1,
        },
        "ice_wall": {
            "integrity_base": 60, "energy_base": 30, "damage_base": 14,
            "integrity_per_level": 6, "energy_per_level": 2, "damage_per_level": 2,
        },
        "junction_plaza": {
            "integrity_base": 40, "energy_base": 30, "damage_base": 8,
            "integrity_per_level": 5, "energy_per_level": 2, "damage_per_level": 1,
        },
        "shard_foundry": {
            "integrity_base": 50, "energy_base": 35, "damage_base": 10,
            "integrity_per_level": 5, "energy_per_level": 2, "damage_per_level": 2,
        },
        "corrupted_cache": {
            "integrity_base": 40, "energy_base": 50, "damage_base": 12,
            "integrity_per_level": 4, "energy_per_level": 4, "damage_per_level": 2,
        },
        "mcp_fragment": {
            "integrity_base": 90, "energy_base": 40, "damage_base": 16,
            "integrity_per_level": 10, "energy_per_level": 3, "damage_per_level": 2,
        },
        "gridcore": {
            "integrity_base": 120, "energy_base": 60, "damage_base": 20,
            "integrity_per_level": 12, "energy_per_level": 5, "damage_per_level": 3,
        },
    }
    if archetype_id not in PROFILES:
        raise ValueError(
            f"Unknown archetype {archetype_id!r}. Valid: {sorted(PROFILES)}"
        )
    p = PROFILES[archetype_id]
    lvl = max(1, daemon_level) - 1
    integrity = p["integrity_base"] + lvl * p["integrity_per_level"]
    energy = p["energy_base"] + lvl * p["energy_per_level"]
    damage = p["damage_base"] + lvl * p["damage_per_level"]
    return max(1, integrity), max(1, energy), max(1, damage)


def _player_integrity(player_level: int) -> int:
    """Return starting integrity for a player at *player_level*."""
    return PLAYER_INTEGRITY_BASE + (max(1, player_level) - 1) * PLAYER_INTEGRITY_PER_LEVEL


# ---------------------------------------------------------------------------
# Core simulation
# ---------------------------------------------------------------------------

def simulate_combat(
    player_lvl: int,
    daemon_archetype: str,
    daemon_lvl: int,
    n_runs: int = 1000,
    seed: Optional[int] = None,
) -> BalanceReport:
    """
    Simulate *n_runs* fights between a player at *player_lvl* and a daemon
    of type *daemon_archetype* scaled to *daemon_lvl*.

    The fight is modelled as alternating ticks:
      - Odd ticks (1, 3, 5 …): player strikes daemon.
      - Even ticks (2, 4, 6 …): daemon counter-strikes player.
    Both sides deal BASE + randint(0, JITTER) per strike.
    Fight ends when either side's integrity reaches 0.

    Args:
        player_lvl:       Player character level (>= 1).
        daemon_archetype: Archetype slug matching ARCHETYPES keys.
        daemon_lvl:       Daemon level, clamped to archetype's level_band.
        n_runs:           Number of Monte Carlo runs (default 1000).
        seed:             Optional RNG seed for deterministic output.

    Returns:
        BalanceReport dataclass.

    Raises:
        KeyError:   Unknown *daemon_archetype*.
        ValueError: *n_runs* < 1.
    """
    if n_runs < 1:
        raise ValueError(f"n_runs must be >= 1, got {n_runs}")

    archetype = ARCHETYPES[daemon_archetype]  # KeyError on bad id — intentional
    band_min, band_max = archetype["level_band"]

    # Clamp daemon level to archetype band (mirrors hybrid scaling rule).
    daemon_lvl = max(band_min, min(band_max, max(1, daemon_lvl)))

    daemon_integrity, _daemon_energy, daemon_damage = _daemon_stats(daemon_archetype, daemon_lvl)
    player_max_integrity = _player_integrity(player_lvl)

    rng = random.Random(seed)

    total_ttk: float = 0.0
    total_xp: float = 0.0
    total_daemon_damage_dealt: float = 0.0
    total_daemon_strikes: int = 0
    kills: int = 0
    total_player_integrity_after: float = 0.0

    for _ in range(n_runs):
        player_hp = player_max_integrity
        daemon_hp = daemon_integrity
        tick = 0
        player_alive = True

        while player_hp > 0 and daemon_hp > 0:
            tick += 1
            # Player strikes daemon on every tick.
            player_strike = PLAYER_BASE_DAMAGE + rng.randint(0, PLAYER_RANDOM_BONUS_MAX)
            daemon_hp -= player_strike

            if daemon_hp <= 0:
                break  # kill — daemon loses before counter-strike this tick

            # Daemon counter-strikes player every DAEMON_COUNTER_FREQUENCY ticks.
            if tick % DAEMON_COUNTER_FREQUENCY == 0:
                d_jitter = rng.randint(0, max(1, daemon_damage // 4))
                hit = daemon_damage + d_jitter
                player_hp -= hit
                total_daemon_damage_dealt += hit
                total_daemon_strikes += 1

        if daemon_hp <= 0 and player_hp > 0:
            kills += 1
            total_ttk += tick
            xp = kill_xp(daemon_lvl, band_min, player_lvl)
            total_xp += xp
            total_player_integrity_after += player_hp

    kill_rate = kills / n_runs
    avg_ttk = total_ttk / kills if kills else float("inf")
    avg_xp = total_xp / kills if kills else 0.0
    daemon_dps = (
        total_daemon_damage_dealt / total_daemon_strikes
        if total_daemon_strikes else float(daemon_damage)
    )
    avg_integrity_left = total_player_integrity_after / kills if kills else 0.0

    # XP/hour estimate: assume player successfully kills at the rate implied
    # by avg_ttk_ticks and PLAYER_STRIKES_PER_MINUTE.  If kill_rate < 1.0 we
    # scale down proportionally (player wastes ticks on losing fights).
    if kills and avg_ttk < float("inf") and PLAYER_STRIKES_PER_MINUTE > 0:
        seconds_per_kill = (avg_ttk / PLAYER_STRIKES_PER_MINUTE) * 60.0
        kills_per_hour = (3600.0 / seconds_per_kill) * kill_rate
        xp_per_hour = kills_per_hour * avg_xp
    else:
        xp_per_hour = 0.0

    return BalanceReport(
        archetype=daemon_archetype,
        daemon_level=daemon_lvl,
        player_level=player_lvl,
        n_runs=n_runs,
        kill_rate=kill_rate,
        avg_ttk_ticks=round(avg_ttk, 2) if math.isfinite(avg_ttk) else float("inf"),
        xp_per_kill=round(avg_xp, 2),
        xp_per_hour=round(xp_per_hour, 1),
        daemon_dps=round(daemon_dps, 3),
        player_survival_rate=kill_rate,
        avg_player_integrity_left=round(avg_integrity_left, 2),
        zone_band_min=band_min,
    )


# ---------------------------------------------------------------------------
# Multi-zone sweep
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class ZoneSweepRow:
    """One row of the full zone sweep output."""
    archetype: str
    band_min: int
    band_max: int
    tier: int
    player_level: int
    daemon_level: int
    kill_rate: float
    xp_per_kill: float
    xp_per_hour: float
    daemon_dps: float
    flag: str  # "" | "UNFARMABLE" | "TOO_LUCRATIVE"

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


#: XP/hour below this threshold is flagged as UNFARMABLE.
UNFARMABLE_XPH_THRESHOLD: float = 10.0

#: XP/hour above this multiple of the archetype-band-appropriate rate is
#: flagged as TOO_LUCRATIVE.  Heuristic — adjust as the curve is tuned.
TOO_LUCRATIVE_XPH_THRESHOLD: float = 50_000.0


def sweep_all_zones(
    player_levels: Optional[list[int]] = None,
    n_runs: int = 500,
    seed: int = 42,
) -> list[ZoneSweepRow]:
    """
    Simulate every (player_level, archetype) pair and return a flat list of
    ZoneSweepRow objects.

    Daemon level is set to the midpoint of the archetype's level band, clamped
    to [band_min, band_max].  This represents a typical encounter inside the zone.

    Args:
        player_levels: List of player levels to simulate.  Defaults to
                       [1, 5, 10, 20, 30, 40].
        n_runs:        Runs per (player, archetype) pair (default 500).
        seed:          RNG seed for determinism (default 42).

    Returns:
        List of ZoneSweepRow, ordered by (archetype tier, player_level).
    """
    if player_levels is None:
        player_levels = [1, 5, 10, 20, 30, 40]

    rows: list[ZoneSweepRow] = []
    # Sort archetypes by tier then band_min for readability.
    sorted_archetypes = sorted(
        ARCHETYPES.values(),
        key=lambda a: (a["tier"], a["level_band"][0]),
    )

    for archetype in sorted_archetypes:
        aid = archetype["archetype_id"]
        band_min, band_max = archetype["level_band"]
        daemon_lvl = (band_min + band_max) // 2  # midpoint representative

        for plvl in player_levels:
            report = simulate_combat(
                player_lvl=plvl,
                daemon_archetype=aid,
                daemon_lvl=daemon_lvl,
                n_runs=n_runs,
                seed=seed,
            )

            if report.xp_per_hour < UNFARMABLE_XPH_THRESHOLD and report.kill_rate < 0.05:
                flag = "UNFARMABLE"
            elif report.xp_per_hour > TOO_LUCRATIVE_XPH_THRESHOLD:
                flag = "TOO_LUCRATIVE"
            else:
                flag = ""

            rows.append(ZoneSweepRow(
                archetype=aid,
                band_min=band_min,
                band_max=band_max,
                tier=archetype["tier"],
                player_level=plvl,
                daemon_level=report.daemon_level,
                kill_rate=round(report.kill_rate, 3),
                xp_per_kill=round(report.xp_per_kill, 1),
                xp_per_hour=round(report.xp_per_hour, 0),
                daemon_dps=round(report.daemon_dps, 2),
                flag=flag,
            ))

    return rows


def format_table(rows: list[ZoneSweepRow]) -> str:
    """
    Format sweep rows as a human-readable ASCII table for stdout.

    Columns: archetype, band, tier, player_lvl, daemon_lvl, kill%, xp/kill, xp/hr, dps, flag
    """
    header = (
        f"{'Archetype':<18} {'Band':>6} {'T':>2} {'PL':>3} {'DL':>3} "
        f"{'Kill%':>6} {'XP/kill':>8} {'XP/hr':>9} {'DPS':>6}  Flag"
    )
    separator = "-" * len(header)
    lines = [header, separator]

    current_tier = None
    for row in rows:
        if current_tier is not None and row.tier != current_tier:
            lines.append("")
        current_tier = row.tier

        band = f"{row.band_min}-{row.band_max}"
        flag_str = f"  << {row.flag}" if row.flag else ""
        lines.append(
            f"{row.archetype:<18} {band:>6} {row.tier:>2} {row.player_level:>3} "
            f"{row.daemon_level:>3} {row.kill_rate:>5.0%} {row.xp_per_kill:>8.1f} "
            f"{row.xp_per_hour:>9.0f} {row.daemon_dps:>6.2f}{flag_str}"
        )

    return "\n".join(lines)
