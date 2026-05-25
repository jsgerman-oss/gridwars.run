"""
GridWars.run leaderboard command — `@leaderboard`.

Renders the top-10 rated characters in a neon-grid table ordered by ELO
rating descending. Ties broken by character name alphabetically (ascending).

Epic 17.5 — bd gridwars_run-1h5.
"""

from evennia import Command

from typeclasses.characters import Character

# Maximum number of rows to show.
_TOP_N = 10


def _get_rating(char) -> int | None:
    """
    Read the rating off a Character, tolerating any typeclass-swap edge case.

    AttributeProperty descriptors live on the typeclass class object.
    When Evennia's idmapper swaps __class__ at object-fetch time, the
    descriptor is accessible via the normal attribute lookup.  We use
    `attributes.get` directly as the canonical path so we don't depend
    on __class__ being fully set — this is safe and avoids AttributeError
    in tests where characters created by other test fixtures may lack the
    descriptor on their swapped class.
    """
    return char.attributes.get("rating")


def _ranked_players() -> list[tuple[int, str, int, str | None]]:
    """
    Return up to _TOP_N characters sorted by rating desc, name asc.

    Each entry is (rank, name, rating, faction).
    Characters without a rating attribute are excluded (defensive — all
    Characters default to 1000 at creation via at_object_creation).
    """
    chars = list(Character.objects.all())
    # Read rating via the AttributeHandler to avoid typeclass-swap edge cases.
    rated = [(c, _get_rating(c)) for c in chars]
    rated = [(c, r) for c, r in rated if r is not None]
    # Sort: rating descending, name ascending for ties.
    rated.sort(key=lambda cr: (-cr[1], cr[0].key.lower()))
    top = rated[:_TOP_N]
    return [
        (rank + 1, c.key, r, c.attributes.get("faction"))
        for rank, (c, r) in enumerate(top)
    ]


class CmdLeaderboard(Command):
    """
    Show the top-10 characters by ELO rating.

    Usage:
      @leaderboard

    Displays a neon-grid table of the top-10 ranked programs on the Grid,
    ordered by rating from highest to lowest. Ties are broken alphabetically.
    """

    key = "@leaderboard"
    aliases = ["leaderboard"]
    locks = "cmd:all()"
    help_category = "GridWars"

    def func(self):
        rows = _ranked_players()

        if not rows:
            self.caller.msg("|yNo ranked players yet.|n")
            return

        # Column widths for fixed-width layout.
        # Rank: 4 chars, Name: 20 chars, Rating: 6 chars, Faction: remainder.
        header = (
            "|c╔══════════ GRID LEADERBOARD ═══════════╗|n\n"
            "|c  #    Name                 Rating  Faction|n\n"
            "|c  ─    ────────────────────  ──────  ───────|n"
        )

        lines = [header]
        for rank, name, rating, faction in rows:
            # Rank column: right-aligned in 2 chars, cyan.
            rank_str = f"|c{rank:>2}|n"
            # Name: left-aligned in 20 chars, white.
            name_str = f"|w{name:<20}|n"
            # Rating: right-aligned in 6 chars, green.
            rating_str = f"|g{rating:>6}|n"
            # Faction: optional tag, yellow if present.
            if faction:
                faction_str = f" |y[{faction}]|n"
            else:
                faction_str = ""
            lines.append(f"  {rank_str}  {name_str}  {rating_str}{faction_str}")

        lines.append("|c╚════════════════════════════════════════╝|n")
        self.caller.msg("\n".join(lines))
