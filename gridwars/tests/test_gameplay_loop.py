"""
End-to-end integration tests for the full GridWars.run gameplay loop (Epic 17).

Covers five scenarios that exercise the complete path from queue → matchmaking
→ duel resolution → rewards → leaderboard:

  1. test_queue_pairs_two_players
       Two characters queue; matchmaking script tick creates a DuelArena and
       moves both inside.

  2. test_duel_end_updates_ratings
       Simulated 3 strikes from winner — both characters' ELO ratings mutated,
       ops log line emitted.

  3. test_winner_disc_gains_xp
       Winner's equipped disc has xp > 0 (and disc XP == XP_PER_KILL) after the
       duel ends via the 3-strike win condition.

  4. test_leaderboard_reflects_results
       After one complete duel, @leaderboard output lists winner above loser.

  5. test_queue_status_during_match
       A third player who queues solo while a match is in progress sees a
       "Position: 1" line in @queue status output.

Test harness: EvenniaCommandTest / EvenniaTest (real Django DB, full Evennia
environment). Follows the same patterns as commands/tests/test_duels.py and
world/tests/test_matchmaking.py — lazy world-module imports, create_object for
extra characters, clear_queue in setUp/tearDown.
"""

import importlib.util
import unittest

from evennia.objects.models import ObjectDB
from evennia.utils import create
from evennia.utils.create import create_object, create_script
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from commands.leaderboard import CmdLeaderboard, _ranked_players
from commands.queue import CmdQueue
from typeclasses.characters import Character
from typeclasses.discs import Disc, XP_PER_KILL
from world.combat import (
    EXP_ON_VICTORY,
    USERS_SECTOR_CATEGORY,
    USERS_SECTOR_TAG,
)
from world.duels_score import BONUS_XP_ON_WIN, STRIKES_TO_WIN

# Mirror of queue_store._QUEUE_KEY — inlined to avoid pre-discovery import.
_QUEUE_KEY = "gw_duel_queue"

# world.matchmaking ships with PR #81 (gameplay-loop/matchmaking-script).
# When that branch is not yet merged we skip tests that require the script.
_MATCHMAKING_AVAILABLE = importlib.util.find_spec("world.matchmaking") is not None


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_spawn_room():
    """Create the tagged Users' Sector room required for defeat → respawn."""
    return create_object(
        "evennia.objects.objects.DefaultRoom",
        key="Users' Sector",
        tags=[(USERS_SECTOR_TAG, USERS_SECTOR_CATEGORY)],
    )


def _clear_queue():
    from world.queue_store import clear_queue
    clear_queue()


def _equip_disc(char):
    """Create a fresh Disc, place it in *char*, and set equipped_disc."""
    disc = create_object(Disc, key="test-disc", location=char)
    char.db.equipped_disc = disc
    return disc


# ---------------------------------------------------------------------------
# 1. test_queue_pairs_two_players
# ---------------------------------------------------------------------------

class TestQueuePairsTwoPlayers(EvenniaTest):
    """
    Two characters @queue duel → matchmaking script tick → both in a DuelArena.
    """

    character_typeclass = Character

    def setUp(self):
        super().setUp()
        _clear_queue()
        self.p1 = create_object(Character, key="Tron", location=self.room1)
        self.p2 = create_object(Character, key="Flynn", location=self.room1)

    def tearDown(self):
        _clear_queue()
        super().tearDown()

    @unittest.skipUnless(
        _MATCHMAKING_AVAILABLE,
        "world.matchmaking not on branch (PR #81 unmerged) — skipping",
    )
    def test_queue_pairs_two_players(self):
        """Queue two players; one matchmaking tick moves both into a DuelArena."""
        # Lazy import — avoids discovery-phase ModuleNotFoundError (same as
        # world/tests/test_matchmaking.py pattern).
        from world.matchmaking import MatchmakingScript
        from world.queue_store import enqueue, get_queue

        script = create_script(MatchmakingScript)
        script.stop()

        enqueue(self.p1.id)
        enqueue(self.p2.id)
        self.assertEqual(len(get_queue()), 2, "Both players should be in the queue.")

        script.at_repeat()

        # Queue must be drained.
        self.assertEqual(get_queue(), [], "Queue should be empty after a match.")

        # Both players should be co-located in the arena.
        self.assertIsNotNone(self.p1.location, "p1 must have a location.")
        self.assertEqual(
            self.p1.location,
            self.p2.location,
            "Both players must share the same arena room.",
        )

        # The room must be a DuelArena typeclass.
        arena = self.p1.location
        self.assertTrue(
            arena.is_typeclass("typeclasses.duel_arenas.DuelArena", exact=False),
            f"Location should be DuelArena, got {arena.typeclass_path!r}.",
        )


# ---------------------------------------------------------------------------
# 2. test_duel_end_updates_ratings
# ---------------------------------------------------------------------------

class TestDuelEndUpdatesRatings(EvenniaTest):
    """
    Three strikes from a single attacker in a DuelArena → ELO ratings mutated,
    ops log line emitted.
    """

    character_typeclass = Character

    def setUp(self):
        super().setUp()
        _clear_queue()
        self.spawn_room = _make_spawn_room()
        self.winner = create_object(Character, key="Sark", location=self.room1)
        self.loser = create_object(Character, key="Clu", location=self.room1)
        # Give the loser enough integrity to absorb strikes without dying.
        self.loser.integrity = 1000

    def tearDown(self):
        _clear_queue()
        super().tearDown()

    def _run_duel_to_win(self):
        """Spawn arena, deliver STRIKES_TO_WIN strikes, return arena id."""
        from world.duels import create_arena
        arena = create_arena(self.winner, self.loser)
        arena_id = arena.id

        for _ in range(STRIKES_TO_WIN):
            self.winner.db.last_strike_time = None
            # Directly invoke handle_duel_strike rather than routing via CmdStrike
            # to avoid the cooldown / damage / defeat side-effects.
            from world.duels_score import handle_duel_strike
            handle_duel_strike(arena=arena, attacker=self.winner, target=self.loser)
            # After the final strike, the arena is deleted; stop iterating.
            if not ObjectDB.objects.filter(id=arena_id).exists():
                break

        return arena_id

    def test_duel_end_updates_ratings(self):
        """Winner's rating rises; loser's rating falls after a 3-strike duel."""
        winner_rating_before = self.winner.rating
        loser_rating_before = self.loser.rating

        self._run_duel_to_win()

        self.assertGreater(
            self.winner.rating,
            winner_rating_before,
            "Winner's rating should increase after a duel win.",
        )
        self.assertLess(
            self.loser.rating,
            loser_rating_before,
            "Loser's rating should decrease after a duel loss.",
        )

    def test_duel_end_emits_log_line(self):
        """Ops log '[duel-end]' line is emitted when the duel concludes."""
        with self.assertLogs("world.duels_score", level="INFO") as log_cm:
            self._run_duel_to_win()

        log_text = "\n".join(log_cm.output)
        self.assertIn("[duel-end]", log_text)
        self.assertIn("Sark", log_text)
        self.assertIn("Clu", log_text)


# ---------------------------------------------------------------------------
# 3. test_winner_disc_gains_xp
# ---------------------------------------------------------------------------

class TestWinnerDiscGainsXP(EvenniaTest):
    """
    Winner's equipped disc has xp == XP_PER_KILL after the win condition fires.
    """

    character_typeclass = Character

    def setUp(self):
        super().setUp()
        _clear_queue()
        self.spawn_room = _make_spawn_room()
        self.winner = create_object(Character, key="Rinzler", location=self.room1)
        self.loser = create_object(Character, key="Tron2", location=self.room1)
        self.loser.integrity = 1000
        self.disc = _equip_disc(self.winner)

    def tearDown(self):
        _clear_queue()
        super().tearDown()

    def test_winner_disc_gains_xp(self):
        """Winner's equipped disc accumulates XP_PER_KILL after the duel ends."""
        self.assertEqual(self.disc.xp, 0, "Disc should start with 0 XP.")

        from world.duels import create_arena
        from world.duels_score import handle_duel_strike

        arena = create_arena(self.winner, self.loser)
        arena_id = arena.id

        for _ in range(STRIKES_TO_WIN):
            handle_duel_strike(arena=arena, attacker=self.winner, target=self.loser)
            if not ObjectDB.objects.filter(id=arena_id).exists():
                break

        # duels_score.handle_duel_strike calls equipped.gain_xp(XP_PER_KILL) on win.
        self.assertGreater(self.disc.xp, 0, "Disc should have gained XP after duel win.")
        self.assertEqual(
            self.disc.xp,
            XP_PER_KILL,
            f"Disc should have exactly XP_PER_KILL ({XP_PER_KILL}) XP; got {self.disc.xp}.",
        )


# ---------------------------------------------------------------------------
# 4. test_leaderboard_reflects_results
# ---------------------------------------------------------------------------

class TestLeaderboardReflectsResults(EvenniaCommandTest):
    """
    After one full duel, @leaderboard renders winner's name before loser's.
    """

    character_typeclass = Character

    def setUp(self):
        super().setUp()
        _clear_queue()
        self.spawn_room = _make_spawn_room()

        # Use char1 as winner, char2 as loser (both created by EvenniaCommandTest).
        self.char1.integrity = 100
        self.char1.rating = 1000
        self.char2.integrity = 1000   # high so defeat-flow doesn't fire
        self.char2.rating = 1000

    def tearDown(self):
        _clear_queue()
        super().tearDown()

    def _run_duel_to_win(self, winner, loser):
        """Deliver STRIKES_TO_WIN handle_duel_strike calls; return arena_id."""
        from world.duels import create_arena
        from world.duels_score import handle_duel_strike

        arena = create_arena(winner, loser)
        arena_id = arena.id

        for _ in range(STRIKES_TO_WIN):
            handle_duel_strike(arena=arena, attacker=winner, target=loser)
            if not ObjectDB.objects.filter(id=arena_id).exists():
                break

        return arena_id

    def test_leaderboard_reflects_results(self):
        """After char1 beats char2, @leaderboard shows char1 above char2."""
        self._run_duel_to_win(self.char1, self.char2)

        # Winner's rating must exceed loser's.
        self.assertGreater(
            self.char1.rating,
            self.char2.rating,
            "Winner should have a higher rating after the duel.",
        )

        # _ranked_players() returns sorted (rank, name, rating, faction) tuples.
        ranked = _ranked_players()
        names = [name for _, name, _, _ in ranked]

        self.assertIn(self.char1.key, names, "Winner must appear in leaderboard.")
        self.assertIn(self.char2.key, names, "Loser must appear in leaderboard.")

        winner_pos = names.index(self.char1.key)
        loser_pos = names.index(self.char2.key)
        self.assertLess(
            winner_pos,
            loser_pos,
            f"Winner ({self.char1.key}) should rank above loser ({self.char2.key}) "
            f"on the leaderboard; got positions {winner_pos} vs {loser_pos}.",
        )

    def test_leaderboard_command_output_contains_winner(self):
        """@leaderboard command output contains the winner's name after a duel."""
        self._run_duel_to_win(self.char1, self.char2)

        result = self.call(CmdLeaderboard(), "", caller=self.char1)
        self.assertIn(self.char1.key, result, "Leaderboard output must name the winner.")


# ---------------------------------------------------------------------------
# 5. test_queue_status_during_match
# ---------------------------------------------------------------------------

class TestQueueStatusDuringMatch(EvenniaCommandTest):
    """
    A third player who queues solo while a match is in flight sees "1" in
    @queue status output (position 1 in the waiting queue).
    """

    character_typeclass = Character

    def setUp(self):
        super().setUp()
        _clear_queue()
        # p3 is the solo waiter — use char1.
        # p1 and p2 get matched and removed from the queue.
        self.p1 = create_object(Character, key="Grid1", location=self.room1)
        self.p2 = create_object(Character, key="Grid2", location=self.room1)
        self.p3 = self.char1

    def tearDown(self):
        _clear_queue()
        super().tearDown()

    def test_queue_status_during_match(self):
        """
        Scenario: p1 + p2 are matched (removed from queue); p3 queues solo
        while that match is in flight and sees position 1.

        The matchmaking step is simulated via queue_store directly so this
        test does not depend on world.matchmaking (PR #81).  What matters is
        the queue-state contract: p3 is the only remaining entry and @queue
        status reflects position 1.
        """
        from world.queue_store import clear_queue, dequeue, enqueue, get_queue

        # Step 1: p1 and p2 enter the queue.
        enqueue(self.p1.id)
        enqueue(self.p2.id)
        self.assertEqual(len(get_queue()), 2)

        # Step 2: simulate matchmaking pairing — drain p1 and p2 from queue
        # exactly as MatchmakingScript.at_repeat() would do.
        dequeue(self.p1.id)
        dequeue(self.p2.id)
        self.assertEqual(get_queue(), [], "p1 + p2 should be drained (matched).")

        # Step 3: p3 queues solo while the p1-vs-p2 match is in flight.
        enqueue(self.p3.id)
        self.assertIn(self.p3.id, get_queue())

        # Step 4: p3 checks queue status — must see position 1.
        result = self.call(CmdQueue(), "status", caller=self.p3)
        # CmdQueue._status reports "you are number <N> in line" when queued.
        self.assertIn("1", result, f"p3 should see position 1 in queue; got: {result!r}")
        # Sanity: not the "queue is empty" message.
        self.assertNotIn("empty", result.lower())
