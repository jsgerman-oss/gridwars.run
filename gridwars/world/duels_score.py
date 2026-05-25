"""
In-arena duel scoring + win declaration.

Called from CmdStrike when the attacker is inside a DuelArena.
Tracks per-attacker strike count on the arena; first to STRIKES_TO_WIN
successful strikes triggers end_arena and awards attacker XP.

Defeat-before-win: if the target's integrity hits 0 the existing defeat
flow in CmdStrike._defeat fires first (target moves out via respawn).
This function then runs; if the score threshold is met, end_arena still
fires cleanly — end_arena.origins iterates by stored ID and move_to
works from wherever the character currently is.

Epic 17.4: on win, both players' ELO ratings are updated via update_rating,
winner gets +10 bonus XP on top of EXP_ON_VICTORY, messages include new
ratings, and the winner's equipped disc gains XP.
"""
import logging

from world.combat import EXP_ON_VICTORY
from world.duels import end_arena
from world.rating import update_rating

logger = logging.getLogger(__name__)

STRIKES_TO_WIN = 3
BONUS_XP_ON_WIN = 10


def handle_duel_strike(arena, attacker, target):
    """Record a successful strike and declare a winner when threshold reached.

    On win:
    - Both characters' ELO ratings updated via update_rating(winner, loser).
    - Winner gets EXP_ON_VICTORY + BONUS_XP_ON_WIN experience.
    - Victory/defeat messages include each player's new rating.
    - Winner's equipped disc gains XP (if one is equipped).
    - A log line is emitted for ops.

    Args:
        arena:    DuelArena Room where the strike occurred.
        attacker: Character who landed the strike.
        target:   Character who was struck.
    """
    scores = arena.db.duel_scores or {}
    aid = str(attacker.id)
    scores[aid] = scores.get(aid, 0) + 1
    arena.db.duel_scores = scores

    if scores[aid] >= STRIKES_TO_WIN:
        # Snapshot ratings before mutation for the log line.
        old_w = attacker.rating
        old_l = target.rating

        # Update ELO ratings in place; returns (new_winner, new_loser).
        new_w, new_l = update_rating(attacker, target)

        # Award winner experience: base victory XP + flat bonus.
        attacker.gain_experience(EXP_ON_VICTORY + BONUS_XP_ON_WIN)

        # Send result messages with updated ratings.
        attacker.msg(
            f"|gVictory!|n You won the duel ({scores[aid]} strikes). "
            f"(rating: {new_w})"
        )
        target.msg(
            f"|rDefeat.|n You lost the duel ({scores[aid]} strikes to "
            f"{scores.get(str(target.id), 0)} or fewer). "
            f"(rating: {new_l})"
        )

        # Feed disc XP if the winner has a disc equipped.
        equipped = attacker.db.equipped_disc
        if equipped is not None:
            from typeclasses.discs import XP_PER_KILL
            equipped.gain_xp(XP_PER_KILL)

        # Ops log: old → new ratings for both sides.
        logger.info(
            "[duel-end] %s (%d→%d) defeated %s (%d→%d)",
            attacker.key, old_w, new_w,
            target.key, old_l, new_l,
        )

        end_arena(arena, winner=attacker)
