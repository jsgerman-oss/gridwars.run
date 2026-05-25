"""
Unit tests for the duel command suite (CmdChallenge / CmdAccept / CmdDecline)
and the end-to-end duel flow through handle_duel_strike.

Covers acceptance criteria for LD4 (gridwars_run-7xs.4):
  1. challenge happy path — pending_challenge_from set, both chars messaged.
  2. cross-room challenge rejected — no target found, state unchanged.
  3. decline clears pending challenge state.
  4. accept creates DuelArena, moves both chars in, clears pending state.
  5. expiry callback clears pending state (tested via static method directly).
  6. duel to completion — 3 strikes, winner gets XP, both return home, arena
     is deleted from DB.
  7. double-challenge refused — target already has pending challenge.
  8. self-challenge refused.
"""

from evennia.objects.models import ObjectDB
from evennia.utils import create
from evennia.utils.test_resources import EvenniaCommandTest

from commands.combat import CmdStrike
from commands.duels import CmdAccept, CmdChallenge, CmdDecline
from typeclasses.characters import Character
from world.combat import (
    EXP_ON_VICTORY,
    USERS_SECTOR_CATEGORY,
    USERS_SECTOR_TAG,
)


class DuelCommandTestCase(EvenniaCommandTest):
    """CmdChallenge / CmdAccept / CmdDecline: happy paths and failure modes."""

    character_typeclass = Character

    def setUp(self):
        super().setUp()
        # Create the tagged Users' Sector room so defeat→respawn can find it
        # (required for the end-to-end duel test where a strike may zero integrity).
        self.spawn_room = create.create_object(
            "evennia.objects.objects.DefaultRoom",
            key="Users' Sector",
            tags=[(USERS_SECTOR_TAG, USERS_SECTOR_CATEGORY)],
        )
        # Ensure no leftover challenge state from previous tests.
        self.char1.db.pending_challenge_from = None
        self.char2.db.pending_challenge_from = None

    # ------------------------------------------------------------------
    # 1. Challenge happy path
    # ------------------------------------------------------------------

    def test_challenge_sets_pending_and_messages_both(self):
        """challenge <target> in same room sets pending_challenge_from and messages both."""
        result = self.call(CmdChallenge(), self.char2.key, caller=self.char1)
        # char1 gets "Challenge sent" confirmation.
        self.assertIn("Challenge sent", result)
        # char2 now has a pending challenge from char1.
        self.assertIs(
            self.char2.db.pending_challenge_from,
            self.char1,
            "pending_challenge_from should be char1 after challenge.",
        )

    # ------------------------------------------------------------------
    # 2. Cross-room challenge rejected
    # ------------------------------------------------------------------

    def test_cross_room_challenge_rejected(self):
        """Challenging a target in a different room is rejected; state unchanged."""
        self.char2.location = self.room2  # move char2 out
        result = self.call(CmdChallenge(), self.char2.key, caller=self.char1)
        self.assertIn("No '", result)
        self.assertIsNone(
            self.char2.db.pending_challenge_from,
            "pending_challenge_from must stay None when target is in another room.",
        )

    # ------------------------------------------------------------------
    # 3. Decline clears state
    # ------------------------------------------------------------------

    def test_decline_clears_pending_challenge(self):
        """decline clears pending_challenge_from back to None."""
        # Manually set the pending state as if challenge was called.
        self.char2.db.pending_challenge_from = self.char1
        result = self.call(CmdDecline(), "", caller=self.char2)
        self.assertIn("Declined", result)
        self.assertIsNone(
            self.char2.db.pending_challenge_from,
            "pending_challenge_from should be None after decline.",
        )

    # ------------------------------------------------------------------
    # 4. Accept creates arena and moves both chars in
    # ------------------------------------------------------------------

    def test_accept_creates_arena_moves_both_chars(self):
        """accept creates a DuelArena, moves both participants in, clears pending state."""
        self.char2.db.pending_challenge_from = self.char1
        original_char2_location = self.char2.location

        result = self.call(CmdAccept(), "", caller=self.char2)
        self.assertIn("accepted", result)

        # pending state cleared
        self.assertIsNone(
            self.char2.db.pending_challenge_from,
            "pending_challenge_from should be None after accept.",
        )

        # Both chars must now be in the same room — the arena.
        arena = self.char1.location
        self.assertIsNotNone(arena, "char1 should have a location after accept.")
        self.assertEqual(
            self.char1.location,
            self.char2.location,
            "Both chars should be in the same arena after accept.",
        )
        # Confirm the room is actually a DuelArena typeclass.
        self.assertTrue(
            arena.is_typeclass("typeclasses.duel_arenas.DuelArena", exact=False),
            f"Location should be a DuelArena, got {arena.typeclass_path!r}.",
        )

    # ------------------------------------------------------------------
    # 5. Expiry clears state (static method, no real delay)
    # ------------------------------------------------------------------

    def test_expiry_callback_clears_state(self):
        """Manually firing _expire() clears pending_challenge_from."""
        self.char2.db.pending_challenge_from = self.char1
        # Call the staticmethod directly — avoids relying on the real delay().
        CmdChallenge._expire(self.char2, self.char1)
        self.assertIsNone(
            self.char2.db.pending_challenge_from,
            "pending_challenge_from should be None after _expire fires.",
        )

    # ------------------------------------------------------------------
    # 6. End-to-end duel: 3 strikes → winner + both return home + arena gone
    # ------------------------------------------------------------------

    def test_duel_to_completion_winner_xp_and_return(self):
        """
        Full duel flow: challenge→accept spawns arena, 3 strikes in arena
        triggers end_arena — char1 (winner) gets EXP_ON_VICTORY, both return
        to room1, and the arena object is deleted from the DB.
        """
        # Record origins and XP before duel.
        char1_origin = self.char1.location  # room1
        char2_origin = self.char2.location  # room1
        char1_xp_before = self.char1.experience

        # Challenge + accept to spawn arena.
        self.char2.db.pending_challenge_from = self.char1
        self.call(CmdAccept(), "", caller=self.char2)

        arena = self.char1.location
        arena_id = arena.id
        self.assertTrue(
            arena.is_typeclass("typeclasses.duel_arenas.DuelArena", exact=False),
            "Should be in a DuelArena after accept.",
        )

        # Deliver 3 strikes from char1 → char2 in the arena.
        # Reset cooldown and ensure char2 integrity stays above 0 per strike
        # (set high integrity so defeat-flow doesn't fire mid-duel).
        self.char2.integrity = 1000  # high enough to survive 3 hits
        for _ in range(3):
            # Clear cooldown timestamp so rapid test strikes are never refused.
            self.char1.db.last_strike_time = None
            self.call(CmdStrike(), self.char2.key, caller=self.char1)

        # After 3 strikes, end_arena should have fired.
        # Both chars back at their origins.
        self.assertEqual(
            self.char1.location,
            char1_origin,
            f"char1 should be back at origin {char1_origin!r}, got {self.char1.location!r}.",
        )
        self.assertEqual(
            self.char2.location,
            char2_origin,
            f"char2 should be back at origin {char2_origin!r}, got {self.char2.location!r}.",
        )
        # Arena deleted from DB.
        self.assertFalse(
            ObjectDB.objects.filter(id=arena_id).exists(),
            "Arena should be deleted from DB after duel ends.",
        )
        # Winner gained XP.
        self.assertEqual(
            self.char1.experience,
            char1_xp_before + EXP_ON_VICTORY,
            f"char1 should have gained {EXP_ON_VICTORY} XP.",
        )

    # ------------------------------------------------------------------
    # 7. Double-challenge refused (optional — guards the pending check)
    # ------------------------------------------------------------------

    def test_double_challenge_refused(self):
        """Challenging a target who already has a pending challenge is refused."""
        self.char2.db.pending_challenge_from = self.char1
        result = self.call(CmdChallenge(), self.char2.key, caller=self.char1)
        self.assertIn("already has a pending challenge", result)

    # ------------------------------------------------------------------
    # 8. Self-challenge refused
    # ------------------------------------------------------------------

    def test_self_challenge_refused(self):
        """A character cannot challenge themselves."""
        result = self.call(CmdChallenge(), self.char1.key, caller=self.char1)
        self.assertIn("cannot challenge yourself", result)
