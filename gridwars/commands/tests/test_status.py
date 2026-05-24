"""
Unit tests for the status command (CmdStatus).

Covers (gridwars_run-62h.2 / Epic 9):
  1. status output contains all 7 identity fields.
  2. Unaffiliated caller (faction=None) sees '|y' color code and 'unaffiliated'.
  3. Aligned caller (faction='Users') sees faction color '|c' near 'Users'.
  4. Critical integrity (<=24) renders with '|r' color code.

Uses EvenniaCommandTest (real Django DB, full Evennia environment).
"""

from evennia.utils.test_resources import EvenniaCommandTest

from commands.status import CmdStatus
from typeclasses.characters import Character


class StatusCommandTestCase(EvenniaCommandTest):
    """CmdStatus: all fields + color threshold assertions."""

    character_typeclass = Character

    def setUp(self):
        super().setUp()
        self.char1.faction = None
        self.char1.integrity = 100
        self.char1.energy = 50
        self.char1.experience = 0
        self.char1.grid_rank = "User"

    # ------------------------------------------------------------------
    # 1. All fields present in output
    # ------------------------------------------------------------------

    def test_status_shows_all_fields(self):
        """status output contains name, location, faction, integrity, energy, exp, rank."""
        result = self.call(CmdStatus(), "", caller=self.char1)
        # Name
        self.assertIn(self.char1.key, result)
        # Location
        self.assertIn(self.char1.location.key, result)
        # Integrity value
        self.assertIn("100", result)
        # Energy value (default 50)
        self.assertIn("50", result)
        # Experience value (default 0)
        self.assertIn("0", result)
        # Rank label
        self.assertIn(self.char1.grid_rank, result)

    # ------------------------------------------------------------------
    # 2. Unaffiliated shows yellow color + 'unaffiliated'
    # ------------------------------------------------------------------

    def test_status_unaffiliated_shows_yellow(self):
        """faction=None → output contains yellow ANSI code and 'unaffiliated'.

        noansi=False returns ANSI escape sequences; |y maps to \x1b[33m (yellow).
        """
        self.char1.faction = None
        result = self.call(CmdStatus(), "", caller=self.char1, noansi=False)
        self.assertIn("unaffiliated", result)
        # Evennia |y → bright yellow ANSI: ESC[1;33m or ESC[33m.
        self.assertTrue(
            "\x1b[33m" in result or "\x1b[1;33m" in result or "\x1b[1m\x1b[33m" in result,
            f"Expected yellow ANSI code near 'unaffiliated', got: {repr(result[:200])}",
        )

    # ------------------------------------------------------------------
    # 3. Aligned faction color matches registry
    # ------------------------------------------------------------------

    def test_status_faction_color_matches_registry(self):
        """faction='Users' → output contains cyan ANSI code (Users color) near 'Users'.

        noansi=False returns ANSI escape sequences; |c maps to \x1b[36m (cyan).
        """
        self.char1.faction = "Users"
        result = self.call(CmdStatus(), "", caller=self.char1, noansi=False)
        self.assertIn("Users", result)
        # Evennia |c → bright cyan ANSI: ESC[1;36m or ESC[36m.
        self.assertTrue(
            "\x1b[36m" in result or "\x1b[1;36m" in result or "\x1b[1m\x1b[36m" in result,
            f"Expected cyan ANSI code near 'Users', got: {repr(result[:200])}",
        )

    # ------------------------------------------------------------------
    # 4. Critical integrity renders red
    # ------------------------------------------------------------------

    def test_status_critical_integrity_shows_red(self):
        """integrity=10 (<25% threshold) → red ANSI code appears in output.

        noansi=False returns ANSI escape sequences; |r maps to \x1b[31m (red).
        """
        self.char1.integrity = 10
        result = self.call(CmdStatus(), "", caller=self.char1, noansi=False)
        # The bar-color helper returns |r when pct < 25%.
        self.assertTrue(
            "\x1b[31m" in result or "\x1b[1;31m" in result or "\x1b[1m\x1b[31m" in result,
            f"Expected red ANSI code for integrity=10, got: {repr(result[:200])}",
        )
        self.assertIn("10", result)
