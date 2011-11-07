"""
Adapted from: http://forrst.com/posts/An_Elo_Rating_function_in_Python_written_for_foo-hQl#comment-481138
"""
import math

def calculate_elo_rank(winner_rank, loser_rank, penalize_loser=True):
    rank_diff = winner_rank - loser_rank
    exp = (rank_diff * -1) / 400
    odds = 1 / (1 + math.pow(10, exp))
    if winner_rank < 2100:
        k = 32
    elif winner_rank >= 2100 and winner_rank < 2400:
        k = 24
    else:
        k = 16
    new_winner_rank = int(round(winner_rank + (k * (1 - odds))))
    if penalize_loser:
        new_rank_diff = new_winner_rank - winner_rank
        new_loser_rank = loser_rank - new_rank_diff
    else:
        new_loser_rank = loser_rank
    if new_loser_rank < 1:
        new_loser_rank = 1
    return (new_winner_rank, new_loser_rank)
