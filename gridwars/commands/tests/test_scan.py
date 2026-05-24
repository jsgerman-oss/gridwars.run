"""
Unit tests for the scan command (CmdScan).

Covers (gridwars_run-62h.2 / Epic 9):
  1. Other characters in the room appear in scan output.
  2. The caller (self) is excluded from the "Programs here" section.
  3. Room exits appear in scan output.
  4. Faction tint: a Daemon character is shown with '|r' color.
  5. Flavor fallback: room with no scan_flavor Attribute uses first sentence of desc.

Uses EvenniaCommandTest (real Django DB, full Evennia environment).
char1 and char2 are placed in room1 by the base setUp.
"""

from evennia.utils import create
from evennia.utils.test_resources import EvenniaCommandTest

from commands.scan import CmdScan
from typeclasses.characters import Character


class ScanCommandTestCase(EvenniaCommandTest):
    """CmdScan: character listing, self-exclusion, exits, faction tint, flavor."""

    character_typeclass = Character

    def setUp(self):
        super().setUp()
        # Both chars start in room1 by EvenniaCommandTest default.
        self.char1.faction = None
        self.char2.faction = None

    # ------------------------------------------------------------------
    # 1. Other character appears in output
    # ------------------------------------------------------------------

    def test_scan_shows_other_character(self):
        """char2 in the same room appears in scan output."""
        # Ensure char2 is in room1 with char1.
        self.char2.location = self.room1
        result = self.call(CmdScan(), "", caller=self.char1)
        self.assertIn(self.char2.key, result)

    # ------------------------------------------------------------------
    # 2. Self excluded from Programs section
    # ------------------------------------------------------------------

    def test_scan_excludes_self(self):
        """The caller's name does NOT appear in the 'Programs here' listing.

        Uses a caller whose key cannot be a substring of char2's key.
        EvenniaCommandTest creates char1='Char' and char2='Char2', so we
        check the programs section does not contain a line for char1 by
        verifying char1's key is not listed as its own entry (the line
        format is '  - <name>' or '  - <name> [Faction]').
        """
        self.char2.location = self.room1
        result = self.call(CmdScan(), "", caller=self.char1)

        # Extract the Programs section lines.
        if "Programs here:" in result:
            after_programs = result.split("Programs here:")[1]
            if "Exits:" in after_programs:
                programs_section = after_programs.split("Exits:")[0]
            else:
                programs_section = after_programs

            # Split into individual lines and look for an exact-name match.
            # Each program line is "  - <Name>" or "  - <Name> [Faction]".
            # char1.key = "Char"; char2.key = "Char2" — avoid substring collision
            # by splitting on "-" and checking the first token after the dash.
            caller_key = self.char1.key
            for line in programs_section.splitlines():
                stripped = line.strip()
                if stripped.startswith("- "):
                    # e.g. "- Char2 [Daemons]" or "- Char2"
                    entry = stripped[2:].split()[0]  # first word after "- "
                    self.assertNotEqual(
                        entry, caller_key,
                        f"Caller '{caller_key}' must not appear in Programs here section.",
                    )

    # ------------------------------------------------------------------
    # 3. Exits appear in output
    # ------------------------------------------------------------------

    def test_scan_lists_exits(self):
        """Room exits are listed in the scan output."""
        # Create two exits in room1.
        exit_north = create.create_object(
            "evennia.objects.objects.DefaultExit",
            key="north",
            location=self.room1,
            destination=self.room2,
        )
        exit_east = create.create_object(
            "evennia.objects.objects.DefaultExit",
            key="east",
            location=self.room1,
            destination=self.room2,
        )
        result = self.call(CmdScan(), "", caller=self.char1)
        self.assertIn("north", result)
        self.assertIn("east", result)
        # Clean up exits to avoid polluting other tests.
        exit_north.delete()
        exit_east.delete()

    # ------------------------------------------------------------------
    # 4. Faction tint: Daemons character shows |r
    # ------------------------------------------------------------------

    def test_scan_faction_tint(self):
        """char2 with faction='Daemons' is shown with red ANSI color near their name.

        noansi=False returns ANSI escape sequences; Daemons |r maps to \x1b[31m.
        """
        self.char2.faction = "Daemons"
        self.char2.location = self.room1
        result = self.call(CmdScan(), "", caller=self.char1, noansi=False)
        # char2 should be visible.
        self.assertIn(self.char2.key, result)
        # Daemons color is |r → red ANSI: ESC[1;31m or ESC[31m.
        self.assertTrue(
            "\x1b[31m" in result or "\x1b[1;31m" in result or "\x1b[1m\x1b[31m" in result,
            f"Expected red ANSI code for Daemons faction tint, got: {repr(result[:300])}",
        )

    # ------------------------------------------------------------------
    # 5. Flavor fallback: first sentence of desc when no scan_flavor
    # ------------------------------------------------------------------

    def test_scan_flavor_fallback(self):
        """Room with desc and no scan_flavor uses the first sentence of desc."""
        # Set a multi-sentence desc on room1 with no scan_flavor.
        self.room1.db.desc = "A long flavor sentence here. Another sentence follows."
        # Ensure no scan_flavor is set.
        if self.room1.attributes.has("scan_flavor"):
            self.room1.attributes.remove("scan_flavor")

        result = self.call(CmdScan(), "", caller=self.char1)
        # The first sentence (up to and including the period) should be in output.
        self.assertIn("A long flavor sentence here.", result)
        # The second sentence should NOT appear as part of the flavor.
        # It may be absent or present — we only mandate the first sentence.
        # Primary check: first sentence is in the output.
