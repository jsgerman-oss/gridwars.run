"""
Unit tests for gridwars/world/rating.py — pure ELO math.

Test cases:
1. Even match (1000 vs 1000): winner gains ~16, loser loses ~16.
2. Favourite wins (1500 vs 1000): small delta (~3).
3. Underdog upset (1000 vs 1500): large delta (~29).
4. Floor: max(0, ...) guard — rating returned by update_rating is never negative.
5. New Character has rating == 1000.
"""

from unittest.mock import MagicMock

from evennia.utils.test_resources import EvenniaTest

from typeclasses.characters import Character
from world.rating import update_rating


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _char(rating: int) -> MagicMock:
    """Return a lightweight stand-in with a mutable .rating attribute."""
    c = MagicMock()
    c.rating = rating
    return c


# ---------------------------------------------------------------------------
# ELO math tests — no DB required; uses _char() mocks
# ---------------------------------------------------------------------------

class TestUpdateRatingEvenMatch(EvenniaTest):
    """1000 vs 1000 — symmetric; each side moves ~16 points."""

    def test_winner_gains_points(self):
        w, l = _char(1000), _char(1000)
        new_w, _ = update_rating(w, l)
        self.assertAlmostEqual(new_w, 1000, delta=17)
        self.assertGreater(new_w, 1000)

    def test_loser_loses_points(self):
        w, l = _char(1000), _char(1000)
        _, new_l = update_rating(w, l)
        self.assertAlmostEqual(new_l, 1000, delta=17)
        self.assertLess(new_l, 1000)

    def test_delta_is_symmetric(self):
        w, l = _char(1000), _char(1000)
        new_w, new_l = update_rating(w, l)
        # Winner's gain == loser's loss (ratings are symmetric at 1000v1000)
        gain = new_w - 1000
        loss = 1000 - new_l
        self.assertEqual(gain, loss)

    def test_attributes_mutated_in_place(self):
        w, l = _char(1000), _char(1000)
        new_w, new_l = update_rating(w, l)
        self.assertEqual(w.rating, new_w)
        self.assertEqual(l.rating, new_l)


class TestUpdateRatingFavouriteWins(EvenniaTest):
    """1500 vs 1000 — heavy favourite wins; delta is small (~3)."""

    def test_winner_gains_small_amount(self):
        w, l = _char(1500), _char(1000)
        new_w, _ = update_rating(w, l)
        delta = new_w - 1500
        self.assertGreaterEqual(delta, 1)
        self.assertLessEqual(delta, 5)

    def test_loser_loses_small_amount(self):
        w, l = _char(1500), _char(1000)
        _, new_l = update_rating(w, l)
        delta = 1000 - new_l
        self.assertGreaterEqual(delta, 1)
        self.assertLessEqual(delta, 5)


class TestUpdateRatingUnderdogUpset(EvenniaTest):
    """1000 beats 1500 — underdog wins; large delta (~29)."""

    def test_winner_gains_large_amount(self):
        w, l = _char(1000), _char(1500)
        new_w, _ = update_rating(w, l)
        delta = new_w - 1000
        self.assertGreaterEqual(delta, 25)
        self.assertLessEqual(delta, 33)

    def test_loser_loses_large_amount(self):
        w, l = _char(1000), _char(1500)
        _, new_l = update_rating(w, l)
        delta = 1500 - new_l
        self.assertGreaterEqual(delta, 25)
        self.assertLessEqual(delta, 33)


class TestUpdateRatingFloor(EvenniaTest):
    """max(0, ...) guard: returned ratings are never negative.

    With k=32 the maximum single-game delta is ~32, so a loser rated at
    1000 cannot drop below 0 in one update. We verify the guard by passing
    a mock whose .rating is set to an artificially low starting value so
    that the raw result would be negative, confirming the floor fires.
    """

    def test_return_values_are_non_negative(self):
        """Returned tuple values are always >= 0 regardless of inputs."""
        w, l = _char(2000), _char(5)
        new_w, new_l = update_rating(w, l)
        self.assertGreaterEqual(new_w, 0)
        self.assertGreaterEqual(new_l, 0)

    def test_floor_fires_when_delta_exceeds_loser_rating(self):
        """Loser with very low rating floored at 0 when delta exceeds their rating.

        w=1 beats l=16: expected delta ~16.7, raw new_l = 16 - 16.7 = -0.7,
        which rounds to -1. The max(0, ...) guard returns 0 instead.
        """
        w, l = _char(1), _char(16)
        _, new_l = update_rating(w, l)
        self.assertEqual(new_l, 0)


# ---------------------------------------------------------------------------
# Character attribute test — requires Evennia DB via EvenniaTest
# ---------------------------------------------------------------------------

class TestCharacterRatingDefault(EvenniaTest):
    """New Character has rating == 1000 out of the box."""

    character_typeclass = Character

    def test_new_character_rating_default(self):
        self.assertEqual(self.char1.rating, 1000)
