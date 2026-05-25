"""
GridWars.run — EXP curve for PvE combat (e19.4).

Pure functions; no Evennia DB access.  All tuning constants are
module-level so the balance harness (e19.10) and future operators
can adjust them without touching the formulas.

Formulas (from Epic 19 design doc §5)
--------------------------------------

Kill XP::

    base_xp  = round(daemon_level² × KILL_BASE_MULT)
    band_mod = 1.0 + BAND_MOD_STEP × (zone_band_min - 1)
    soft_cap = SOFT_CAP_MULT × player_level × daemon_level
    xp       = min(round(base_xp × band_mod), soft_cap)

Strike XP::

    xp = daemon_level × STRIKE_MULT

Usage::

    from world.zones.exp import kill_xp, strike_xp

    xp = kill_xp(daemon_level=5, zone_band_min=1, player_level=10)
    xp = strike_xp(daemon_level=5)

Daemon level comes from ``daemon.db.daemon_level`` (set by
``scale_to_level`` in e19.3 daemon variant typeclasses, defaulting to
1 when unset).  Zone band comes from the room's zone metadata; pass 1
when the room has no zone tag (e.g. Daemon Gate, tutorial sector).
"""

# ---------------------------------------------------------------------------
# Tuning constants — change these for balance without touching formulas
# ---------------------------------------------------------------------------

#: Quadratic multiplier for the base kill-XP calculation.
KILL_BASE_MULT: float = 1.5

#: Per-band-level additive step on top of 1.0.
#: band_mod = 1.0 + BAND_MOD_STEP * (zone_band_min - 1)
#: band_min=1 → ×1.00; band_min=25 → ×2.20
BAND_MOD_STEP: float = 0.05

#: Soft-cap multiplier: max XP = SOFT_CAP_MULT * player_level * daemon_level.
SOFT_CAP_MULT: int = 2

#: Linear multiplier for per-strike XP.
STRIKE_MULT: int = 2


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def kill_xp(daemon_level: int, zone_band_min: int, player_level: int) -> int:
    """
    Return the integer XP awarded to the attacker on daemon defeat.

    Args:
        daemon_level:  Level of the defeated daemon (>= 1).
        zone_band_min: Minimum level of the zone's level band (>= 1).
                       Pass 1 for zones without a declared band.
        player_level:  Current level of the attacking player (>= 1).
                       Used only by the soft-cap; does NOT affect base XP.

    Returns:
        Integer XP in range [0, soft_cap].
    """
    daemon_level = max(1, int(daemon_level))
    zone_band_min = max(1, int(zone_band_min))
    player_level = max(1, int(player_level))

    base_xp = round(daemon_level ** 2 * KILL_BASE_MULT)
    band_mod = 1.0 + BAND_MOD_STEP * (zone_band_min - 1)
    soft_cap = SOFT_CAP_MULT * player_level * daemon_level
    return min(round(base_xp * band_mod), soft_cap)


def strike_xp(daemon_level: int) -> int:
    """
    Return the integer XP awarded per successful disc strike against a daemon.

    Args:
        daemon_level: Level of the struck daemon (>= 1).

    Returns:
        Integer XP; always >= STRIKE_MULT (floor at daemon_level=1).
    """
    daemon_level = max(1, int(daemon_level))
    return daemon_level * STRIKE_MULT
