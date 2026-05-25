"""
Pure ELO rating math. No side effects beyond mutating the
passed-in characters' .rating attribute.

Epic 17.3 — rating primitive only.
Post-duel wiring happens in Epic 17.4 (duels_score.py).
"""


def update_rating(winner, loser, k: int = 32) -> tuple[int, int]:
    """
    Apply one ELO update to winner and loser in place.

    Args:
        winner: Character (or any object with a .rating int attribute)
                that won the duel.
        loser:  Character that lost the duel.
        k (int): K-factor controlling rating volatility. Default 32.

    Returns:
        tuple[int, int]: (new_winner_rating, new_loser_rating) after the
        update. Both values are floored at 0 — ratings never go negative.

    Side effects:
        winner.rating and loser.rating are mutated in place.
    """
    expected_w = 1 / (1 + 10 ** ((loser.rating - winner.rating) / 400))
    delta = k * (1 - expected_w)
    new_w = max(0, round(winner.rating + delta))
    new_l = max(0, round(loser.rating - delta))
    winner.rating = new_w
    loser.rating = new_l
    return new_w, new_l
