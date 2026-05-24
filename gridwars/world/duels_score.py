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
"""
from world.combat import EXP_ON_VICTORY
from world.duels import end_arena

STRIKES_TO_WIN = 3


def handle_duel_strike(arena, attacker, target):
    """Record a successful strike and declare a winner when threshold reached.

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
        attacker.msg(
            f"|gVictory!|n You won the duel ({scores[aid]} strikes)."
        )
        target.msg(
            f"|rDefeat.|n You lost the duel ({scores[aid]} strikes to "
            f"{scores.get(str(target.id), 0)} or fewer)."
        )
        attacker.gain_experience(EXP_ON_VICTORY)
        end_arena(arena, winner=attacker)
