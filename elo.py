"""Elo calculation"""
import math


def expected_score(rating_a, rating_b):
    """Returns the expetected score for a game between the specified players"""
    denom = 1 + math.pow(10, (rating_b - rating_a) / 400.)
    return 1 / denom


def get_k_factor(rating):
    """Returns the k-factor for updating Elo.

    Higher k-factor weights recent results more heavily.  The returned k-factor
    is the one used by USCF.
    """
    if rating < 2100:
        return 32
    elif rating < 2400:
        return 24
    else:
        return 16


def calculate_new_elos(rating_a, rating_b, score_a):
    """Calculates and returns the new Elo ratings for two players.

    score_a is 1 for a win by player A, 0 for a loss by player A, or 0.5 for a
    draw.
    """
    e_a = expected_score(rating_a, rating_b)
    e_b = 1 - e_a
    a_k = get_k_factor(rating_a)
    b_k = get_k_factor(rating_b)
    new_rating_a = rating_a + a_k * (score_a - e_a)
    score_b = 1.0 - score_a
    new_rating_b = rating_b + b_k * (score_b - e_b)
    return int(round(new_rating_a)), int(round(new_rating_b))
