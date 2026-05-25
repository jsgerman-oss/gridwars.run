"""
Unit tests for the leaderboard command (CmdLeaderboard).

Covers bd gridwars_run-1h5 acceptance criteria:
  1. Empty DB — no ranked players → shows "No ranked players yet."
  2. Single player — table renders with rank 1.
  3. Five players — all five visible, sorted descending by rating.
  4. Fifteen players — only top 10 shown (cap enforced).
  5. Ties broken alphabetically by name (ascending).

Uses EvenniaCommandTest (real Django DB, full Evennia environment).
"""

from evennia.utils import create
from evennia.utils.test_resources import EvenniaCommandTest

from commands.leaderboard import CmdLeaderboard, _ranked_players
from typeclasses.characters import Character


class LeaderboardCommandTestCase(EvenniaCommandTest):
    """CmdLeaderboard: ordering, cap, ties, and empty-DB safety."""

    character_typeclass = Character

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _make_char(self, name: str, rating: int, faction: str | None = None) -> Character:
        """Create a Character in room1 with the given rating."""
        char = create.create_object(
            Character,
            key=name,
            location=self.room1,
        )
        # Use attributes.add directly to avoid any typeclass-swap descriptor edge cases.
        char.attributes.add("rating", rating)
        if faction:
            char.attributes.add("faction", faction)
        return char

    # ------------------------------------------------------------------
    # 1. Empty DB — no ranked players message
    # ------------------------------------------------------------------

    def test_empty_db_shows_no_ranked_players(self):
        """When all Characters have no rating attribute, the command shows
        "No ranked players yet."

        We clear char1 and char2's rating attributes directly via the
        AttributeHandler (bypassing the descriptor) so this test is robust
        against typeclass-swap edge cases in the Evennia idmapper.
        """
        # Remove the rating attribute entirely so attributes.get("rating")
        # returns None for both fixture characters, triggering the empty path.
        self.char1.attributes.remove("rating")
        self.char2.attributes.remove("rating")

        result = self.call(CmdLeaderboard(), "", caller=self.char1)
        self.assertIn("No ranked players yet.", result)

        # Restore so teardown is clean.
        self.char1.attributes.add("rating", 1000)
        self.char2.attributes.add("rating", 1000)

    # ------------------------------------------------------------------
    # 2. Single player shows rank 1
    # ------------------------------------------------------------------

    def test_single_player_shows_rank_one(self):
        """A single player appears as rank 1 in the table."""
        self.char1.attributes.add("rating", 1500)
        # Remove char2's rating so only char1 is "ranked" in this test.
        self.char2.attributes.remove("rating")

        result = self.call(CmdLeaderboard(), "", caller=self.char1)
        self.assertIn(self.char1.key, result)
        # Rank 1 should appear.
        self.assertIn("1", result)
        # Rating value.
        self.assertIn("1500", result)

        # Restore.
        self.char1.attributes.add("rating", 1000)
        self.char2.attributes.add("rating", 1000)

    # ------------------------------------------------------------------
    # 3. Five players — all visible, sorted descending
    # ------------------------------------------------------------------

    def test_five_players_sorted_descending(self):
        """Five characters appear ordered by rating (highest first)."""
        ratings = [800, 1200, 950, 1500, 1100]
        chars = []
        for i, r in enumerate(ratings):
            c = self._make_char(f"TestChar{i}", r)
            chars.append(c)

        result = self.call(CmdLeaderboard(), "", caller=self.char1)

        # All five names should appear.
        for c in chars:
            self.assertIn(c.key, result)

        # Verify descending order: 1500 appears before 1200 before 1100 etc.
        pos_1500 = result.index("1500")
        pos_1200 = result.index("1200")
        pos_1100 = result.index("1100")
        pos_950 = result.index("950")
        pos_800 = result.index("800")
        self.assertLess(pos_1500, pos_1200)
        self.assertLess(pos_1200, pos_1100)
        self.assertLess(pos_1100, pos_950)
        self.assertLess(pos_950, pos_800)

        # Clean up.
        for c in chars:
            c.delete()

    # ------------------------------------------------------------------
    # 4. Fifteen players — only top 10 shown
    # ------------------------------------------------------------------

    def test_fifteen_players_capped_at_ten(self):
        """With 15+ players, only the top 10 appear in the output."""
        chars = []
        for i in range(15):
            rating = 2000 - (i * 50)  # 2000, 1950, …, 1300
            c = self._make_char(f"Ranked{i:02d}", rating)
            chars.append(c)

        # Ensure char1/char2 (fixture, rating 1000) fall outside top 10.
        # Top 10 are Ranked00..Ranked09 (2000..1550).
        result = self.call(CmdLeaderboard(), "", caller=self.char1)

        # Top 10 names should appear.
        for i in range(10):
            self.assertIn(f"Ranked{i:02d}", result)

        # The 11th–15th should NOT appear.
        for i in range(10, 15):
            self.assertNotIn(f"Ranked{i:02d}", result)

        # Clean up.
        for c in chars:
            c.delete()

    # ------------------------------------------------------------------
    # 5. Tie-breaking: alphabetical by name
    # ------------------------------------------------------------------

    def test_ties_broken_alphabetically(self):
        """Characters with equal rating are sorted alphabetically (name asc)."""
        alpha = self._make_char("Alpha", 1500)
        gamma = self._make_char("Gamma", 1500)
        beta = self._make_char("Beta", 1500)

        # Use the helper directly for a focused ordering check.
        # Remove fixture chars' rating so they don't interfere.
        self.char1.attributes.remove("rating")
        self.char2.attributes.remove("rating")

        ranked = _ranked_players()
        names = [r[1] for r in ranked]

        # Among tied-rating entries, Alpha < Beta < Gamma alphabetically.
        idx_alpha = names.index("Alpha")
        idx_beta = names.index("Beta")
        idx_gamma = names.index("Gamma")
        self.assertLess(idx_alpha, idx_beta, "Alpha should come before Beta in tie.")
        self.assertLess(idx_beta, idx_gamma, "Beta should come before Gamma in tie.")

        # Restore and clean up.
        self.char1.attributes.add("rating", 1000)
        self.char2.attributes.add("rating", 1000)
        alpha.delete()
        beta.delete()
        gamma.delete()
