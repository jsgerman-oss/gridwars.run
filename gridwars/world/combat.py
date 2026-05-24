"""
GridWars.run combat tuning constants.

Pulled into a separate module so Epic 9 tests + future balance tuning
hit one place. NO logic here — the strike command imports these.
"""

BASE_DAMAGE = 10           # deterministic floor
RANDOM_BONUS_MAX = 5       # uniform jitter 0..MAX added to BASE_DAMAGE
EXP_ON_VICTORY = 5         # attacker gains this on defeat
RESPAWN_INTEGRITY = 25     # defeated target restored to this minimum
USERS_SECTOR_TAG = "users_sector"
USERS_SECTOR_CATEGORY = "world_build"
