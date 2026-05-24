"""
Unit tests for the strike command and defeat→respawn flow.

Covers the 5 acceptance criteria from Epic 6 St2 (gridwars_run-8zk.2):
  1. Same-room strike reduces target integrity by BASE_DAMAGE..BASE_DAMAGE+RANDOM_BONUS_MAX.
  2. Cross-room strike is rejected; target integrity unchanged.
  3. Self-strike is refused; caller integrity unchanged.
  4. Striking a non-Character object is refused.
  5. Defeat triggers respawn: target moved to Users' Sector, integrity reset to
     RESPAWN_INTEGRITY, attacker gains EXP_ON_VICTORY XP, target NOT deleted.

Uses EvenniaCommandTest (real Django DB, full Evennia environment).
char1 and char2 are both placed in room1 by the base setUp; char2 is left
there for same-room tests and moved to room2 for the cross-room test.
"""

from evennia.utils import create
from evennia.utils.test_resources import EvenniaCommandTest

from commands.combat import CmdStrike
from typeclasses.characters import Character
from world.combat import (
    BASE_DAMAGE,
    EXP_ON_VICTORY,
    RANDOM_BONUS_MAX,
    RESPAWN_INTEGRITY,
    USERS_SECTOR_CATEGORY,
    USERS_SECTOR_TAG,
)


class StrikeTestCase(EvenniaCommandTest):
    """Strike command: happy path + 4 failure modes + defeat flow."""

    character_typeclass = Character

    def setUp(self):
        super().setUp()
        # EvenniaTestMixin places both chars in room1; no move needed for same-room tests.
        # Create the tagged Users' Sector room so defeat→respawn can find it.
        self.spawn_room = create.create_object(
            "evennia.objects.objects.DefaultRoom",
            key="Users' Sector",
            tags=[(USERS_SECTOR_TAG, USERS_SECTOR_CATEGORY)],
        )

    # ------------------------------------------------------------------
    # 1. Same-room hit
    # ------------------------------------------------------------------

    def test_same_room_strike_reduces_integrity(self):
        """A strike in the same room deals BASE_DAMAGE..BASE_DAMAGE+RANDOM_BONUS_MAX."""
        before = self.char2.integrity  # 100 by default
        self.call(CmdStrike(), self.char2.key, caller=self.char1)
        after = self.char2.integrity
        damage = before - after
        self.assertGreaterEqual(damage, BASE_DAMAGE)
        self.assertLessEqual(damage, BASE_DAMAGE + RANDOM_BONUS_MAX)

    # ------------------------------------------------------------------
    # 2. Cross-room rejection
    # ------------------------------------------------------------------

    def test_cross_room_strike_fails(self):
        """Striking a target in a different room is rejected; integrity unchanged."""
        self.char2.location = self.room2  # move target out of room1
        before = self.char2.integrity
        result = self.call(CmdStrike(), self.char2.key, caller=self.char1)
        self.assertIn("No character", result)
        self.assertEqual(self.char2.integrity, before)

    # ------------------------------------------------------------------
    # 3. Self-strike refused
    # ------------------------------------------------------------------

    def test_self_strike_refused(self):
        """A character cannot strike themselves; integrity unchanged."""
        before = self.char1.integrity
        result = self.call(CmdStrike(), self.char1.key, caller=self.char1)
        self.assertIn("yourself", result)
        self.assertEqual(self.char1.integrity, before)

    # ------------------------------------------------------------------
    # 4. Non-Character rejection
    # ------------------------------------------------------------------

    def test_strike_on_non_character_refused(self):
        """Striking a plain object (not a Character) is rejected by the typeclass filter."""
        dummy = create.create_object(
            "evennia.objects.objects.DefaultObject",
            key="rock",
            location=self.char1.location,
        )
        result = self.call(CmdStrike(), "rock", caller=self.char1)
        self.assertIn("No character", result)

    # ------------------------------------------------------------------
    # 5. Defeat triggers respawn + XP grant + target survives in DB
    # ------------------------------------------------------------------

    def test_defeat_triggers_respawn_and_xp(self):
        """
        When a strike drops target integrity to 0:
        - Target is moved to the tagged Users' Sector room.
        - Target integrity is reset to RESPAWN_INTEGRITY (25).
        - Attacker gains EXP_ON_VICTORY (5) experience.
        - Target object still exists in the DB (not deleted).
        """
        # Set target integrity low enough that even minimum damage (BASE_DAMAGE=10) kills.
        self.char2.integrity = BASE_DAMAGE  # exactly 10; any roll kills
        attacker_xp_before = self.char1.experience
        target_id = self.char2.id

        self.call(CmdStrike(), self.char2.key, caller=self.char1)

        # Target still exists in DB (Characters are NEVER deleted on defeat)
        from evennia.objects.models import ObjectDB

        self.assertTrue(
            ObjectDB.objects.filter(id=target_id).exists(),
            "Target object must not be deleted on defeat.",
        )
        # Target respawned in Users' Sector
        self.assertEqual(
            self.char2.location,
            self.spawn_room,
            f"Target should be in Users' Sector, got {self.char2.location!r}.",
        )
        # Target integrity restored to RESPAWN_INTEGRITY
        self.assertEqual(
            self.char2.integrity,
            RESPAWN_INTEGRITY,
            f"Target integrity should be {RESPAWN_INTEGRITY}, got {self.char2.integrity}.",
        )
        # Attacker gained XP
        self.assertEqual(
            self.char1.experience,
            attacker_xp_before + EXP_ON_VICTORY,
            f"Attacker XP should have grown by {EXP_ON_VICTORY}.",
        )
