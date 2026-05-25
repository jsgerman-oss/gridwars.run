"""
GridWars.run combat commands.

`strike <target>` — same-room PvP/PvE. Resolves target by name in caller's
room contents, refuses self / cross-room / non-Character targets,
deals BASE_DAMAGE + randint(0, RANDOM_BONUS_MAX) + disc.damage_bonus,
broadcasts messages. Cooldown enforced when a disc is equipped via
caller.db.equipped_disc; timestamp tracked in caller.db.last_strike_time.

On target.integrity == 0 → defeat flow: room derez message, move target
to Users' Sector via tag lookup, target.reset_for_respawn(...),
attacker.gain_experience(XP).

XP rules:
  PvP (target is a player Character): attacker.gain_experience(EXP_ON_VICTORY).
  PvE (target is a Daemon):
    - per-strike XP: gain_experience(strike_xp(daemon_level)) on every hit.
    - kill XP:       gain_experience(kill_xp(daemon_level, zone_band_min,
                     player_level)) on defeat (replaces EXP_ON_VICTORY).
  Disc XP is awarded separately via equipped.gain_xp() in both modes.

Characters are NEVER deleted.
"""
import time
from random import randint
from evennia import Command
from evennia.utils.search import search_tag

from world.combat import (
    BASE_DAMAGE, RANDOM_BONUS_MAX, EXP_ON_VICTORY, RESPAWN_INTEGRITY,
    USERS_SECTOR_TAG, USERS_SECTOR_CATEGORY,
)
from typeclasses.discs import XP_PER_STRIKE, XP_PER_KILL
from world.zones.exp import kill_xp as _kill_xp, strike_xp as _strike_xp


def _is_character(obj) -> bool:
    """Same-class check that works for the GridWars Character subclass."""
    return obj.is_typeclass("typeclasses.characters.Character", exact=False)


def _is_daemon(obj) -> bool:
    """Return True when obj is a Daemon NPC (any variant)."""
    return obj.is_typeclass("typeclasses.daemons.Daemon", exact=False)


def _daemon_level(daemon) -> int:
    """
    Read the daemon's current level from db.daemon_level (set by
    scale_to_level in e19.3 daemon variant typeclasses).  Defaults to 1
    when unset (tutorial / manually spawned daemons).
    """
    return max(1, int(daemon.db.daemon_level or 1))


def _zone_band_min(room) -> int:
    """
    Read the zone's minimum level band from the room's db.zone_band_min
    attribute (set by the repop ticker in e19.5).  Returns 1 when unset.
    """
    if room is None:
        return 1
    return max(1, int(room.db.zone_band_min or 1))


def _player_level(character) -> int:
    """
    Player level is not a first-class attribute yet (future Epic).
    Derive it from accumulated experience as a reasonable proxy so the
    soft cap works sensibly without blocking this feature on Epic 20.

    Thresholds: 0 XP = L1, 100 = L2, 300 = L3, 700 = L4, 1500 = L5, …
    Uses disc XP_THRESHOLDS as the canonical source; falls back to
    level 1 if the import fails.
    """
    try:
        from typeclasses.discs import XP_THRESHOLDS
        xp = max(0, int(character.experience or 0))
        # XP_THRESHOLDS = [0, 100, 300, 700, 1500]
        # Index 0 (=0) is disc baseline; player level brackets start at index 1.
        # Level 1: 0-99 XP (below threshold[1]=100)
        # Level 2: 100-299 XP, etc.
        brackets = XP_THRESHOLDS[1:]  # [100, 300, 700, 1500]
        for lvl, threshold in enumerate(brackets, start=2):
            if xp < threshold:
                return lvl - 1
        return len(brackets) + 1
    except Exception:
        return 1


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

        # Resolve target in current room only (search excludes everything else).
        # No typeclass filter here — Daemon subclasses have a different
        # db_typeclass_path so a typeclass= kwarg would exclude them.
        # _is_character() uses is_typeclass() with exact=False to handle the
        # full hierarchy (Character → Daemon → DaemonVariant).
        target = caller.search(
            arg,
            location=caller.location,
            quiet=True,
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

        # Cooldown gate — enforced when a disc is equipped.
        equipped = caller.db.equipped_disc
        now = time.time()
        last = caller.db.last_strike_time or 0.0
        cooldown = equipped.cooldown_seconds if equipped else 0
        if cooldown and (now - last) < cooldown:
            remaining = cooldown - (now - last)
            caller.msg(f"|yYour disc is still cycling — {remaining:.1f}s remaining.|n")
            return

        # Damage calc: base + jitter + disc bonus (0 when unequipped).
        bonus = equipped.damage_bonus if equipped else 0
        amount = BASE_DAMAGE + randint(0, RANDOM_BONUS_MAX) + bonus
        target.take_damage(amount)

        # Stamp cooldown timestamp.
        caller.db.last_strike_time = now

        if equipped:
            caller.msg(f"|wYou strike|n |c{target.key}|n |wwith|n {equipped.key} |wfor|n |y{amount}|n |wintegrity.|n")
        else:
            caller.msg(f"|wYou strike|n |c{target.key}|n |wfor|n |y{amount}|n |wintegrity.|n")
        target.msg(f"|c{caller.key}|n |rstrikes you for|n |y{amount}|n |rintegrity.|n")
        caller.location.msg_contents(
            f"|c{caller.key}|n strikes |c{target.key}|n!",
            exclude=[caller, target],
        )

        is_kill = target.integrity == 0
        if is_kill:
            self._defeat(caller, target)

        # Grant disc XP after defeat flow so level-up message arrives after respawn notice.
        if equipped:
            if is_kill:
                equipped.gain_xp(XP_PER_KILL)
            else:
                equipped.gain_xp(XP_PER_STRIKE)

        # PvE strike XP — granted on every hit against a daemon (not just kills).
        # Kill XP is handled separately inside _defeat() below.
        if not is_kill and _is_daemon(target):
            xp = _strike_xp(_daemon_level(target))
            caller.gain_experience(xp)
            caller.msg(f"|gStrike XP +{xp}|n (daemon L{_daemon_level(target)}). (Now: |g{caller.experience}|n)")

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

        # Compute XP before moving target (we need the room's zone metadata).
        if _is_daemon(target):
            dlvl = _daemon_level(target)
            bmin = _zone_band_min(target.location)
            plvl = _player_level(attacker)
            xp_award = _kill_xp(dlvl, bmin, plvl)
            xp_label = f"Daemon L{dlvl} kill XP"
        else:
            xp_award = EXP_ON_VICTORY
            xp_label = "Victory XP"

        # Move target to Users' Sector via tag lookup (no fragile dbref).
        spawn = search_tag(USERS_SECTOR_TAG, category=USERS_SECTOR_CATEGORY)
        if spawn:
            target.move_to(spawn[0], quiet=True)
        target.reset_for_respawn(min_integrity=RESPAWN_INTEGRITY)

        attacker.gain_experience(xp_award)
        target.msg(
            f"|wYou re-spawn in|n |cUsers' Sector|n|w with|n |g{target.integrity}|n |wintegrity.|n"
        )
        attacker.msg(
            f"|g{xp_label} +{xp_award}|n. (Now: |g{attacker.experience}|n)"
        )
