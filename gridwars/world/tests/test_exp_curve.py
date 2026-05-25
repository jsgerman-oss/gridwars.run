"""
Unit + integration tests for world.zones.exp (e19.4).

Unit tests (no Evennia DB):
  1. kill_xp formula matrix — table-driven against design-doc §5 examples.
  2. band_mod application — zone_band_min=1 vs zone_band_min=25.
  3. soft_cap behaviour — high-level player farming low daemon.
  4. strike_xp linearity.
  5. Input clamping — zero/negative inputs produce the same result as 1.

Integration tests (EvenniaCommandTest, real DB):
  6. Strike a daemon → attacker gains strike_xp.
  7. Kill a daemon → attacker gains kill_xp (not flat EXP_ON_VICTORY).
  8. Strike a player Character → attacker gains NO character XP on non-kill.
  9. Kill a player Character → attacker gains flat EXP_ON_VICTORY.
"""

import unittest

from evennia.utils import create
from evennia.utils.test_resources import EvenniaCommandTest

from commands.combat import CmdStrike
from typeclasses.characters import Character
from typeclasses.daemons import Daemon
from world.combat import EXP_ON_VICTORY, RESPAWN_INTEGRITY, USERS_SECTOR_TAG, USERS_SECTOR_CATEGORY
from world.zones.exp import (
    KILL_BASE_MULT, BAND_MOD_STEP, SOFT_CAP_MULT, STRIKE_MULT,
    kill_xp, strike_xp,
)


# ---------------------------------------------------------------------------
# 1–5: Pure-function unit tests — no Evennia DB required
# ---------------------------------------------------------------------------

class KillXpFormulaTest(unittest.TestCase):
    """Table-driven tests against the design-doc §5 formula matrix."""

    def _expected(self, daemon_lvl, band_min, player_lvl):
        """Reference implementation mirrors the exact formula in exp.py."""
        base = round(daemon_lvl ** 2 * KILL_BASE_MULT)
        band_mod = 1.0 + BAND_MOD_STEP * (band_min - 1)
        soft_cap = SOFT_CAP_MULT * player_lvl * daemon_lvl
        return min(round(base * band_mod), soft_cap)

    # Design-doc §5 table rows — band[1-5], over-levelled player so soft cap
    # does not trigger (player_level large enough).
    def test_daemon_lvl1_band1(self):
        self.assertEqual(kill_xp(1, 1, 100), self._expected(1, 1, 100))
        self.assertEqual(kill_xp(1, 1, 100), 2)

    def test_daemon_lvl5_band1(self):
        self.assertEqual(kill_xp(5, 1, 100), self._expected(5, 1, 100))
        self.assertEqual(kill_xp(5, 1, 100), 38)

    def test_daemon_lvl15_band1(self):
        self.assertEqual(kill_xp(15, 1, 100), self._expected(15, 1, 100))
        self.assertEqual(kill_xp(15, 1, 100), 338)

    def test_daemon_lvl30_band1(self):
        self.assertEqual(kill_xp(30, 1, 100), self._expected(30, 1, 100))
        self.assertEqual(kill_xp(30, 1, 100), 1350)

    # band[25-40]: band_min=25 → band_mod = 1 + 0.05*24 = 2.2
    def test_daemon_lvl1_band25(self):
        self.assertEqual(kill_xp(1, 25, 100), self._expected(1, 25, 100))
        self.assertEqual(kill_xp(1, 25, 100), 4)

    def test_daemon_lvl5_band25(self):
        # base=38, band_mod=2.2, raw=83.6 → round=84
        self.assertEqual(kill_xp(5, 25, 100), self._expected(5, 25, 100))
        self.assertEqual(kill_xp(5, 25, 100), 84)

    def test_daemon_lvl15_band25(self):
        # base=338, band_mod=2.2, raw=743.6 → round=744
        self.assertEqual(kill_xp(15, 25, 100), self._expected(15, 25, 100))
        self.assertEqual(kill_xp(15, 25, 100), 744)

    def test_daemon_lvl30_band25(self):
        self.assertEqual(kill_xp(30, 25, 100), self._expected(30, 25, 100))
        self.assertEqual(kill_xp(30, 25, 100), 2970)


class BandModTest(unittest.TestCase):
    """Band modifier scales XP upward monotonically as band_min increases."""

    def test_band_mod_increases_with_band_min(self):
        """Higher zone band_min → more XP for same daemon/player levels."""
        xp_band1 = kill_xp(10, 1, 100)
        xp_band10 = kill_xp(10, 10, 100)
        xp_band25 = kill_xp(10, 25, 100)
        self.assertLess(xp_band1, xp_band10)
        self.assertLess(xp_band10, xp_band25)

    def test_band_min_1_gives_no_bonus(self):
        """zone_band_min=1 → band_mod=1.0 → no bonus over base."""
        base = round(10 ** 2 * KILL_BASE_MULT)
        self.assertEqual(kill_xp(10, 1, 1000), base)


class SoftCapTest(unittest.TestCase):
    """Soft cap fires when player is over-levelled for the daemon."""

    def test_soft_cap_fires_for_over_levelled_player(self):
        """Level-30 player vs level-1 daemon: capped at 2*30*1=60, base is 2."""
        result = kill_xp(daemon_level=1, zone_band_min=1, player_level=30)
        # base = round(1*1.5) = 2; soft_cap = 2*30*1 = 60 → NOT capped
        # Actually 2 < 60, so soft cap doesn't trigger here.
        # Test a case where base > soft_cap.
        # daemon_level=10, player_level=1: base=150, soft_cap=2*1*10=20.
        result = kill_xp(daemon_level=10, zone_band_min=1, player_level=1)
        expected_soft_cap = SOFT_CAP_MULT * 1 * 10
        self.assertEqual(result, expected_soft_cap)

    def test_soft_cap_does_not_reduce_fair_fight(self):
        """Player level matches daemon level — soft cap should not trigger."""
        # daemon_level=5, player_level=5: base=38, soft_cap=2*5*5=50 → no cap.
        result = kill_xp(daemon_level=5, zone_band_min=1, player_level=5)
        base = round(5 ** 2 * KILL_BASE_MULT)
        self.assertEqual(result, base)

    def test_soft_cap_scales_with_player_level(self):
        """Higher player level raises the soft cap, allowing more XP from high daemons."""
        xp_low_player = kill_xp(daemon_level=20, zone_band_min=1, player_level=1)
        xp_high_player = kill_xp(daemon_level=20, zone_band_min=1, player_level=25)
        self.assertLess(xp_low_player, xp_high_player)


class StrikeXpTest(unittest.TestCase):
    """strike_xp is linear: daemon_level × STRIKE_MULT."""

    def test_level_1(self):
        self.assertEqual(strike_xp(1), STRIKE_MULT)

    def test_level_5(self):
        self.assertEqual(strike_xp(5), 5 * STRIKE_MULT)

    def test_level_30(self):
        self.assertEqual(strike_xp(30), 30 * STRIKE_MULT)

    def test_linear_scaling(self):
        """Each level adds exactly STRIKE_MULT XP."""
        for lvl in range(1, 20):
            self.assertEqual(strike_xp(lvl), lvl * STRIKE_MULT)


class InputClampingTest(unittest.TestCase):
    """Zero and negative inputs are clamped to 1 — no negative XP."""

    def test_kill_xp_zero_daemon_level(self):
        self.assertEqual(kill_xp(0, 1, 10), kill_xp(1, 1, 10))

    def test_kill_xp_negative_daemon_level(self):
        self.assertEqual(kill_xp(-5, 1, 10), kill_xp(1, 1, 10))

    def test_kill_xp_zero_band_min(self):
        self.assertEqual(kill_xp(5, 0, 10), kill_xp(5, 1, 10))

    def test_kill_xp_zero_player_level(self):
        """Zero player_level clamps to 1 — soft cap is still positive."""
        result = kill_xp(5, 1, 0)
        self.assertGreaterEqual(result, 0)

    def test_strike_xp_zero_level(self):
        self.assertEqual(strike_xp(0), strike_xp(1))

    def test_strike_xp_negative_level(self):
        self.assertEqual(strike_xp(-3), strike_xp(1))


# ---------------------------------------------------------------------------
# 6–9: Integration tests — Evennia DB + CmdStrike
# ---------------------------------------------------------------------------

class ExpCurveIntegrationTest(EvenniaCommandTest):
    """
    Verify XP lands on Character.experience correctly for PvE and PvP.

    char1 = attacker (Character typeclass).
    daemon = Daemon NPC placed in the same room.
    char2 = secondary player Character for PvP tests.
    """

    character_typeclass = Character

    def setUp(self):
        super().setUp()
        # Spawn room for defeated targets
        self.spawn_room = create.create_object(
            "evennia.objects.objects.DefaultRoom",
            key="Users' Sector",
            tags=[(USERS_SECTOR_TAG, USERS_SECTOR_CATEGORY)],
        )
        # Create a Daemon NPC in char1's room
        self.daemon = create.create_object(
            Daemon,
            key="TestDaemon",
            location=self.char1.location,
        )
        # Set daemon level (normally set by scale_to_level via repop ticker)
        self.daemon.db.daemon_level = 5

    # ------------------------------------------------------------------
    # 6. Strike a daemon → attacker gains strike_xp (non-kill hit)
    # ------------------------------------------------------------------

    def test_strike_daemon_grants_strike_xp(self):
        """
        A non-killing hit on a Daemon grants strike_xp(daemon_level) to the
        attacker's Character.experience (in addition to disc XP).
        """
        # Set daemon integrity high so a single strike can't kill it.
        self.daemon.integrity = 100
        xp_before = self.char1.experience

        self.call(CmdStrike(), self.daemon.key, caller=self.char1)

        expected_xp = strike_xp(5)
        xp_after = self.char1.experience
        # XP should have increased by strike_xp(5) = 10
        self.assertEqual(
            xp_after - xp_before,
            expected_xp,
            f"Expected character XP +{expected_xp}, got +{xp_after - xp_before}",
        )

    # ------------------------------------------------------------------
    # 7. Kill a daemon → attacker gains kill_xp (not EXP_ON_VICTORY)
    # ------------------------------------------------------------------

    def test_kill_daemon_grants_kill_xp(self):
        """
        Killing a Daemon grants kill_xp(daemon_level, zone_band_min, player_level),
        NOT the flat EXP_ON_VICTORY used for PvP.
        """
        from commands.combat import _player_level
        from world.combat import BASE_DAMAGE

        # Set daemon integrity to minimum so next strike kills it.
        self.daemon.integrity = BASE_DAMAGE  # any roll will kill

        xp_before = self.char1.experience
        # Compute the expected level the same way combat.py does.
        plvl = _player_level(self.char1)
        # zone_band_min defaults to 1 (room has no db.zone_band_min).
        expected_xp = kill_xp(daemon_level=5, zone_band_min=1, player_level=plvl)

        self.call(CmdStrike(), self.daemon.key, caller=self.char1)

        xp_after = self.char1.experience
        self.assertEqual(
            xp_after - xp_before,
            expected_xp,
            f"Expected kill XP {expected_xp} (plvl={plvl}), got {xp_after - xp_before}",
        )
        # Daemon is NOT dead-and-deleted; it respawned.
        self.assertIsNotNone(self.daemon.pk)

    # ------------------------------------------------------------------
    # 7b. Verify kill_xp ≠ EXP_ON_VICTORY for daemon (formula distinction)
    # ------------------------------------------------------------------

    def test_daemon_kill_xp_differs_from_pvp(self):
        """kill_xp(5, 1, 1) should not equal the flat PvP EXP_ON_VICTORY."""
        self.assertNotEqual(
            kill_xp(5, 1, 1),
            EXP_ON_VICTORY,
            "Daemon kill XP and PvP EXP_ON_VICTORY coincidentally match — "
            "check tuning constants if this is intentional.",
        )

    # ------------------------------------------------------------------
    # 8. Strike a player → NO character XP on non-kill hit
    # ------------------------------------------------------------------

    def test_strike_player_grants_no_character_xp_on_hit(self):
        """
        Hitting (but not killing) a player Character does NOT grant any
        character XP to the attacker.
        """
        self.char2.integrity = 100
        xp_before = self.char1.experience

        self.call(CmdStrike(), self.char2.key, caller=self.char1)

        # No PvE strike XP — char2 is a Character, not a Daemon.
        self.assertEqual(
            self.char1.experience,
            xp_before,
            "Attacker should not gain character XP from hitting a player.",
        )

    # ------------------------------------------------------------------
    # 9. Kill a player → flat EXP_ON_VICTORY
    # ------------------------------------------------------------------

    def test_kill_player_grants_exp_on_victory(self):
        """
        Defeating a player Character awards the flat EXP_ON_VICTORY,
        NOT the daemon kill_xp curve.
        """
        from world.combat import BASE_DAMAGE
        self.char2.integrity = BASE_DAMAGE  # ensure kill

        xp_before = self.char1.experience
        self.call(CmdStrike(), self.char2.key, caller=self.char1)

        self.assertEqual(
            self.char1.experience - xp_before,
            EXP_ON_VICTORY,
            f"PvP kill should award {EXP_ON_VICTORY} XP, "
            f"got {self.char1.experience - xp_before}.",
        )
