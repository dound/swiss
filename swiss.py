"""Computes swiss pairings"""
import random


class PlayerStanding(object):
    """Info about a given player in the swiss tournament"""
    def __init__(self, player):
        self.player = player
        self.match_points = 0
        self.game_points = 0
        self.previous_opponents = []

    def record_match(self, other_player, game_wins, game_losses, game_draws):
        """Record a match result between this player and another player"""
        my_game_points = 3 * game_wins + game_draws
        self.game_points += my_game_points

        other_game_points = 3 * game_losses + game_draws
        other_player.game_points += other_game_points

        if my_game_points > other_game_points:
            self.match_points += 3
        elif my_game_points == other_game_points:
            self.match_points += 1
            other_player.match_points += 1
        else:
            other_player.match_points += 3

        self.previous_opponents.append(other_player)
        other_player.previous_opponents.append(self)

    def record_bye(self, game_points_earned):
        """Record a BYE for this player (like a clean sweep win)"""
        self.game_points += game_points_earned
        self.match_points += 3
        self.previous_opponents.append('BYE')

    def __cmp__(self, other):
        """Higher standings come first"""
        return -cmp((self.match_points, self.game_points),
                    (other.match_points, other.game_points))

    def __eq__(self, other):
        if not isinstance(other, PlayerStanding):
            return False
        return self.__cmp__(other) and self.player == other.player

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        fmt = '%s: MP=%d gp=%d prev_opponents=[%s]'
        return fmt % (self.player, self.match_points,
                      self.game_points,
                      ','.join(str(p == 'BYE' and 'BYE' or p.player)
                               for p in self.previous_opponents))


def assign_pairings(player_standings):
    """Given the current standings, return a list of 2-tuples of who should play
    who in the next round.  Raises an exception if a pairing is not found (this
    does not mean a pairing does not exist - retry and it might find one).

    Swiss pairing:
      * Players will not play an opponent they have previously played
      * Players will not receive more than one BYE
      * Players with similar match points will be paired, as much as possible based
        on the above two constraints.
    """
    # produce all VALID combinations of players
    if len(player_standings) % 2:
        player_standings = player_standings + ['BYE']
    possible_pairings = []
    for i in xrange(len(player_standings) - 1):
        for j in xrange(i + 1, len(player_standings)):
            p1 = player_standings[i]  # never 'BYE' since 'BYE' is the last element in group
            p2 = player_standings[j]
            if p2 in p1.previous_opponents:
                continue
            if p2 != 'BYE':
                if p1 in p2.previous_opponents:
                    continue
                attractiveness = abs(p1.match_points - p2.match_points)
            else:
                attractiveness = -1
            possible_pairings.append((attractiveness, p1, p2))

    # group combinations by attractiveness
    cur_group = []
    cur_group_attractiveness = possible_pairings[0][0]
    groups = [cur_group]
    for p in possible_pairings:
        if p[0] == cur_group_attractiveness:
            cur_group.append(p)
        else:
            cur_group = [p]
            cur_group_attractiveness = p[0]
            groups.append(cur_group)

    # shuffle each group and recreate possible pairings ... now ordered by
    # attractiveness, with ties randomly ordered
    possible_pairings = []
    for group in groups:
        random.shuffle(group)
        possible_pairings += group

    # brute force solver
    for first_choice_idx in xrange(len(possible_pairings)):
        unassigned_players = dict((p, True) for p in player_standings)
        pairings = []
        for i in xrange(first_choice_idx, len(possible_pairings)):
            attractiveness, p1, p2 = possible_pairings[i]
            if p1 in unassigned_players and p2 in unassigned_players:
                del unassigned_players[p1]
                del unassigned_players[p2]
                pairings.append((p1, p2))
            if not unassigned_players:
                return pairings  # everyone got assigned!
    raise Exception("failed to find a valid pairing")
