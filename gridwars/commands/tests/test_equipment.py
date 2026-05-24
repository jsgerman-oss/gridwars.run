"""
Unit tests for equipment commands (CmdEquip / CmdUnequip / CmdInventory)
and the ID3 disc-aware strike / cooldown paths.

Covers 6 acceptance criteria from Epic 12 ID4 (gridwars_run-x3d.4):
  1. equip <name> sets caller.db.equipped_disc to the disc.
  2. Equipping a non-Disc object is refused; equipped_disc unchanged.
  3. unequip clears equipped_disc to None.
  4. inventory output marks the equipped disc with [equipped].
  5. strike with an equipped disc adds damage_bonus to damage roll.
  6. Cooldown on the equipped disc refuses a rapid second strike.

Uses EvenniaCommandTest (real Django DB, full Evennia environment).
char1 and char2 are placed in room1 by the base setUp.
Each test creates a fresh Disc in char1's inventory.
"""

from evennia.utils import create
from evennia.utils.test_resources import EvenniaCommandTest

from commands.equipment import CmdEquip, CmdInventory, CmdUnequip
from commands.combat import CmdStrike
from typeclasses.characters import Character
from typeclasses.discs import Disc
from world.combat import BASE_DAMAGE, RANDOM_BONUS_MAX, USERS_SECTOR_TAG, USERS_SECTOR_CATEGORY


class EquipmentCommandTestCase(EvenniaCommandTest):
    """CmdEquip / CmdUnequip / CmdInventory: all equipment paths."""

    character_typeclass = Character

    def setUp(self):
        super().setUp()
        # A fresh Disc in char1's inventory for each test.
        self.disc = create.create_object(
            Disc,
            key="test-disc",
            location=self.char1,
        )

    # ------------------------------------------------------------------
    # 1. equip valid disc
    # ------------------------------------------------------------------

    def test_equip_valid_disc(self):
        """equip <name> sets caller.db.equipped_disc to the Disc object."""
        self.call(CmdEquip(), self.disc.key, caller=self.char1)
        self.assertIs(
            self.char1.db.equipped_disc,
            self.disc,
            "equipped_disc should be set to the disc after equipping.",
        )

    # ------------------------------------------------------------------
    # 2. equip non-Disc is refused
    # ------------------------------------------------------------------

    def test_equip_non_disc_refused(self):
        """Trying to equip a plain DefaultObject sends an error; equipped_disc unchanged."""
        # Put a regular object in inventory.
        rock = create.create_object(
            "evennia.objects.objects.DefaultObject",
            key="rock",
            location=self.char1,
        )
        self.char1.db.equipped_disc = None  # ensure starting state is clean
        result = self.call(CmdEquip(), "rock", caller=self.char1)
        self.assertIn("not an Identity Disc", result)
        self.assertIsNone(
            self.char1.db.equipped_disc,
            "equipped_disc must remain None after refusing a non-Disc.",
        )

    # ------------------------------------------------------------------
    # 3. unequip clears equipped
    # ------------------------------------------------------------------

    def test_unequip_clears_equipped(self):
        """equip then unequip leaves equipped_disc as None; disc stays in inventory."""
        self.call(CmdEquip(), self.disc.key, caller=self.char1)
        self.assertIs(self.char1.db.equipped_disc, self.disc)

        self.call(CmdUnequip(), "", caller=self.char1)
        self.assertIsNone(
            self.char1.db.equipped_disc,
            "equipped_disc should be None after unequipping.",
        )
        # Disc must still be in inventory (not removed or deleted).
        self.assertIn(
            self.disc,
            self.char1.contents,
            "Disc must remain in inventory after unequip.",
        )

    # ------------------------------------------------------------------
    # 4. inventory marks equipped disc
    # ------------------------------------------------------------------

    def test_inventory_marks_equipped(self):
        """inventory output contains '[equipped]' next to the equipped disc."""
        self.call(CmdEquip(), self.disc.key, caller=self.char1)
        result = self.call(CmdInventory(), "", caller=self.char1)
        self.assertIn("[equipped]", result)

    # ------------------------------------------------------------------
    # 5. strike with disc uses bonus damage
    # ------------------------------------------------------------------

    def test_strike_with_disc_uses_bonus_damage(self):
        """
        With a disc (damage_bonus=10) equipped, strike damage falls in
        [BASE_DAMAGE + 10, BASE_DAMAGE + RANDOM_BONUS_MAX + 10].
        """
        self.disc.damage_bonus = 10
        self.call(CmdEquip(), self.disc.key, caller=self.char1)

        before = self.char2.integrity  # default 100
        self.call(CmdStrike(), self.char2.key, caller=self.char1)
        after = self.char2.integrity
        damage = before - after

        low = BASE_DAMAGE + 10
        high = BASE_DAMAGE + RANDOM_BONUS_MAX + 10
        self.assertGreaterEqual(
            damage, low,
            f"Damage {damage} should be >= BASE_DAMAGE({BASE_DAMAGE}) + bonus(10) = {low}.",
        )
        self.assertLessEqual(
            damage, high,
            f"Damage {damage} should be <= BASE_DAMAGE({BASE_DAMAGE}) + RANDOM_BONUS_MAX({RANDOM_BONUS_MAX}) + bonus(10) = {high}.",
        )

    # ------------------------------------------------------------------
    # 6. strike cooldown refuses rapid re-strike
    # ------------------------------------------------------------------

    def test_strike_cooldown_refuses_rapid_restrike(self):
        """
        equip disc(cooldown_seconds=10), strike successfully, immediately
        strike again — second strike must be refused; char2.integrity must
        not change on the second attempt.
        """
        self.disc.cooldown_seconds = 10
        self.call(CmdEquip(), self.disc.key, caller=self.char1)

        # First strike: should land (cooldown not yet started).
        before_first = self.char2.integrity
        self.call(CmdStrike(), self.char2.key, caller=self.char1)
        after_first = self.char2.integrity
        self.assertLess(
            after_first, before_first,
            "First strike should reduce char2 integrity.",
        )

        # Second strike: immediate, cooldown still active.
        before_second = self.char2.integrity
        result = self.call(CmdStrike(), self.char2.key, caller=self.char1)
        self.assertIn(
            "cycling", result,
            "Cooldown message should mention 'cycling'.",
        )
        self.assertEqual(
            self.char2.integrity,
            before_second,
            "char2 integrity must be unchanged when strike is refused by cooldown.",
        )
