"""
GridWars.run combat commands.

`strike <target>` — same-room PvP. Resolves target by name in caller's
room contents, refuses self / cross-room / non-Character targets,
deals BASE_DAMAGE + randint(0, RANDOM_BONUS_MAX), broadcasts messages.
On target.integrity == 0 → defeat flow: room derez message, move target
to Users' Sector via tag lookup, target.reset_for_respawn(...),
attacker.gain_experience(EXP_ON_VICTORY).

Characters are NEVER deleted.
"""
from random import randint
from evennia import Command
from evennia.utils.search import search_tag

from world.combat import (
    BASE_DAMAGE, RANDOM_BONUS_MAX, EXP_ON_VICTORY, RESPAWN_INTEGRITY,
    USERS_SECTOR_TAG, USERS_SECTOR_CATEGORY,
)


def _is_character(obj) -> bool:
    """Same-class check that works for the GridWars Character subclass."""
    return obj.is_typeclass("typeclasses.characters.Character", exact=False)


class CmdStrike(Command):
    """
    Strike another program in your sector.

    Usage:
      strike <target>

    Damage = BASE_DAMAGE + jitter(0..RANDOM_BONUS_MAX). Defeat (integrity
    hits 0) sends the target back to Users' Sector with restored
    integrity. Attackers gain experience on victory. Strikes only work
    on Characters in your current sector — no cross-sector reach.
    """
    key = "strike"
    aliases = []
    locks = "cmd:all()"
    help_category = "GridWars"

    def func(self):
        caller = self.caller
        arg = self.args.strip()
        if not arg:
            caller.msg("|rUsage:|n |wstrike <target>|n")
            return

        # Resolve target in current room only (search excludes everything else)
        target = caller.search(
            arg,
            location=caller.location,
            quiet=True,
            typeclass="typeclasses.characters.Character",
        )
        # Evennia search returns list with quiet=True; normalize.
        if isinstance(target, list):
            target = target[0] if target else None
        if target is None:
            caller.msg(f"|rNo character named '{arg}' here.|n")
            return
        if target is caller:
            caller.msg("|rYou cannot strike yourself.|n")
            return
        if not _is_character(target):
            caller.msg("|rYou can only strike other characters.|n")
            return

        amount = BASE_DAMAGE + randint(0, RANDOM_BONUS_MAX)
        target.take_damage(amount)

        caller.msg(f"|wYou strike|n |c{target.key}|n |wfor|n |y{amount}|n |wintegrity.|n")
        target.msg(f"|c{caller.key}|n |rstrikes you for|n |y{amount}|n |rintegrity.|n")
        caller.location.msg_contents(
            f"|c{caller.key}|n strikes |c{target.key}|n!",
            exclude=[caller, target],
        )

        if target.integrity == 0:
            self._defeat(caller, target)

        # In-arena duel scoring — runs AFTER defeat flow so target may have
        # already been moved out by respawn; end_arena handles that gracefully.
        loc = caller.location
        if loc and loc.is_typeclass("typeclasses.duel_arenas.DuelArena", exact=False):
            from world.duels_score import handle_duel_strike
            handle_duel_strike(arena=loc, attacker=caller, target=target)

    def _defeat(self, attacker, target):
        # Room broadcast
        if target.location:
            target.location.msg_contents(
                f"|y{target.key}|n |rderezzes|n — sectors recycle the pattern.",
            )
        # Move target to Users' Sector via tag lookup (no fragile dbref)
        spawn = search_tag(USERS_SECTOR_TAG, category=USERS_SECTOR_CATEGORY)
        if spawn:
            target.move_to(spawn[0], quiet=True)
        target.reset_for_respawn(min_integrity=RESPAWN_INTEGRITY)
        attacker.gain_experience(EXP_ON_VICTORY)
        target.msg(
            f"|wYou re-spawn in|n |cUsers' Sector|n|w with|n |g{target.integrity}|n |wintegrity.|n"
        )
        attacker.msg(
            f"|gVictory.|n |wExperience +|n|g{EXP_ON_VICTORY}|n. (Now: |g{attacker.experience}|n)"
        )
