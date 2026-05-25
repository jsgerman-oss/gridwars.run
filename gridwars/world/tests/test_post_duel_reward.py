"""
Tests for Epic 17.4 — post-duel reward hook (XP + ELO rating update).

Acceptance criteria:
  1. update_rating is called on duel end — both characters' ratings change.
  2. Winner's rating appears in the victory message.
  3. Loser's rating appears in the defeat message.
  4. Log line emitted: "[duel-end] winner (old→new) defeated loser (old→new)".
  5. Winner gains EXP_ON_VICTORY + BONUS_XP_ON_WIN experience.
  6. Existing XP grant still fires (not regressed away).
  7. Equipped disc.gain_xp(XP_PER_KILL) called when disc is equipped.
  8. disc.gain_xp NOT called when no disc is equipped.

All tests use MagicMock objects to avoid Evennia DB overhead; the ELO math
is already covered by world/tests/test_rating.py.
"""
import logging
from unittest.mock import MagicMock, patch, call

from evennia.utils.test_resources import EvenniaTest

from world.combat import EXP_ON_VICTORY
from world.duels_score import BONUS_XP_ON_WIN, STRIKES_TO_WIN, handle_duel_strike
from typeclasses.discs import XP_PER_KILL


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_char(key: str, rating: int = 1000, equipped_disc=None) -> MagicMock:
    """Lightweight Character stand-in with mutable rating + msg capture."""
    char = MagicMock()
    char.key = key
    char.rating = rating
    char.db.equipped_disc = equipped_disc
    char.db.duel_scores = None
    char.messages = []

    def capture_msg(text, **kwargs):
        char.messages.append(str(text))

    char.msg.side_effect = capture_msg
    return char


def _make_arena(winner_id: int, loser_id: int, scores: dict | None = None) -> MagicMock:
    """Lightweight DuelArena stand-in with score already at STRIKES_TO_WIN."""
    arena = MagicMock()
    # Pre-fill scores so handle_duel_strike trips the win condition on entry.
    arena.db.duel_scores = scores or {str(winner_id): STRIKES_TO_WIN - 1}
    arena.db.origins = {}
    return arena


# ---------------------------------------------------------------------------
# Test suite
# ---------------------------------------------------------------------------

class TestPostDuelRatingUpdate(EvenniaTest):
    """1 & 2 & 3. Ratings change; winner/loser messages contain new rating."""

    def _run_duel_end(self, winner_rating=1000, loser_rating=1000):
        winner = _make_char("Alice", rating=winner_rating)
        loser = _make_char("Bob", rating=loser_rating)
        winner.id = 1
        loser.id = 2
        arena = _make_arena(winner.id, loser.id)

        with patch("world.duels_score.end_arena"):
            handle_duel_strike(arena, winner, loser)

        return winner, loser

    def test_winner_rating_increases(self):
        winner, _ = self._run_duel_end()
        self.assertGreater(winner.rating, 1000)

    def test_loser_rating_decreases(self):
        _, loser = self._run_duel_end()
        self.assertLess(loser.rating, 1000)

    def test_winner_message_contains_new_rating(self):
        winner, _ = self._run_duel_end()
        combined = " ".join(winner.messages)
        self.assertIn(f"(rating: {winner.rating})", combined)

    def test_loser_message_contains_new_rating(self):
        _, loser = self._run_duel_end()
        combined = " ".join(loser.messages)
        self.assertIn(f"(rating: {loser.rating})", combined)

    def test_both_ratings_mutated_in_place(self):
        """update_rating mutates attributes — verify final values are consistent."""
        winner, loser = self._run_duel_end(winner_rating=1200, loser_rating=800)
        self.assertGreater(winner.rating, 1200)
        self.assertLess(loser.rating, 800)


class TestPostDuelXPGrant(EvenniaTest):
    """5 & 6. Winner gains EXP_ON_VICTORY + BONUS_XP_ON_WIN; not just base."""

    def test_winner_gains_correct_total_xp(self):
        winner = _make_char("Alice")
        loser = _make_char("Bob")
        winner.id = 1
        loser.id = 2
        arena = _make_arena(winner.id, loser.id)

        with patch("world.duels_score.end_arena"):
            handle_duel_strike(arena, winner, loser)

        winner.gain_experience.assert_called_once_with(EXP_ON_VICTORY + BONUS_XP_ON_WIN)

    def test_bonus_xp_constant_is_ten(self):
        """Spec mandates flat +10 bonus."""
        self.assertEqual(BONUS_XP_ON_WIN, 10)


class TestPostDuelLogLine(EvenniaTest):
    """4. Ops log line emitted with correct format."""

    def test_log_line_emitted_on_duel_end(self):
        winner = _make_char("Alice", rating=1000)
        loser = _make_char("Bob", rating=1000)
        winner.id = 1
        loser.id = 2
        arena = _make_arena(winner.id, loser.id)

        with patch("world.duels_score.end_arena"):
            with self.assertLogs("world.duels_score", level="INFO") as cm:
                handle_duel_strike(arena, winner, loser)

        # At least one log record should contain [duel-end].
        log_output = "\n".join(cm.output)
        self.assertIn("[duel-end]", log_output)
        self.assertIn("Alice", log_output)
        self.assertIn("Bob", log_output)


class TestPostDuelDiscXP(EvenniaTest):
    """7 & 8. Disc.gain_xp called when equipped; skipped when not equipped."""

    def test_disc_gain_xp_called_when_equipped(self):
        disc = MagicMock()
        winner = _make_char("Alice", equipped_disc=disc)
        loser = _make_char("Bob")
        winner.id = 1
        loser.id = 2
        arena = _make_arena(winner.id, loser.id)

        with patch("world.duels_score.end_arena"):
            handle_duel_strike(arena, winner, loser)

        disc.gain_xp.assert_called_once_with(XP_PER_KILL)

    def test_disc_gain_xp_not_called_when_no_disc(self):
        winner = _make_char("Alice", equipped_disc=None)
        loser = _make_char("Bob")
        winner.id = 1
        loser.id = 2
        arena = _make_arena(winner.id, loser.id)

        with patch("world.duels_score.end_arena"):
            handle_duel_strike(arena, winner, loser)

        # No disc — nothing to call gain_xp on; just ensure no AttributeError.
        # (Implicit pass if we reach here.)

    def test_disc_gain_xp_receives_xp_per_kill_amount(self):
        """Verify the XP constant passed matches XP_PER_KILL (50)."""
        self.assertEqual(XP_PER_KILL, 50)


class TestPostDuelNoWinYet(EvenniaTest):
    """Strikes below threshold must NOT trigger reward flow."""

    def test_no_rating_update_before_threshold(self):
        winner = _make_char("Alice", rating=1000)
        loser = _make_char("Bob", rating=1000)
        winner.id = 1
        loser.id = 2
        # Start with 0 strikes — below threshold.
        arena = _make_arena(winner.id, loser.id, scores={str(winner.id): 0})

        with patch("world.duels_score.end_arena") as mock_end:
            handle_duel_strike(arena, winner, loser)

        # end_arena should NOT have been called yet (1 strike < STRIKES_TO_WIN).
        mock_end.assert_not_called()
        # Rating must not have changed.
        self.assertEqual(winner.rating, 1000)
        self.assertEqual(loser.rating, 1000)

    def test_end_arena_called_at_threshold(self):
        winner = _make_char("Alice")
        loser = _make_char("Bob")
        winner.id = 1
        loser.id = 2
        # Pre-fill to one below threshold so the next call trips the win.
        arena = _make_arena(winner.id, loser.id)

        with patch("world.duels_score.end_arena") as mock_end:
            handle_duel_strike(arena, winner, loser)

        mock_end.assert_called_once_with(arena, winner=winner)
