"""Computes swiss pairings"""
import random

from elo import calculate_new_elos

GAME_POINTS_PER_BYE = 6
STANDINGS = {}


class PlayerStanding(object):
    """Info about a given player in the swiss tournament"""
    def __init__(self, player, rating=1400, pod=-1):
        self.player = player
        self.rating = rating
        self.pod = pod
        self.match_points = 0
        self.game_points = 0
        self.games_played = 0
        self.previous_opponents = []
        STANDINGS[player] = self

    def record_match(self, other_player, game_wins, game_losses, game_draws):
        """Record a match result between this player and another player"""
        num_games = game_wins + game_losses + game_draws
        my_game_points = 3 * game_wins + game_draws
        self.game_points += my_game_points
        self.games_played += num_games

        other_game_points = 3 * game_losses + game_draws
        other_player.game_points += other_game_points
        other_player.games_played += num_games

        if my_game_points > other_game_points:
            self.match_points += 3
        elif my_game_points == other_game_points:
            self.match_points += 1
            other_player.match_points += 1
        else:
            other_player.match_points += 3

        self.previous_opponents.append(other_player)
        other_player.previous_opponents.append(self)

        if game_wins > game_losses:
            score = 1.0
        elif game_wins < game_losses:
            score = 0.0
        else:
            score = 0.5
        r1, r2 = calculate_new_elos(self.rating, other_player.rating, score)
        print '%s rating: %d -> %d' % (self.player, self.rating, r1)
        print '%s rating: %d -> %d' % (other_player.player, other_player.rating, r2)
        self.rating = r1
        other_player.rating = r2

    def record_bye(self, game_points_earned=GAME_POINTS_PER_BYE):
        """Record a BYE for this player (like a clean sweep win)"""
        self.game_points += game_points_earned
        self.match_points += 3
        self.previous_opponents.append('BYE')

    def record_forfeit_win(self, other_player,
                       game_points_earned=GAME_POINTS_PER_BYE):
        """Record a BYE for this player (like a clean sweep win)"""
        self.game_points += game_points_earned
        self.match_points += 3
        self.previous_opponents.append(other_player)
        other_player.previous_opponents.append(self)

    def match_win_percentage(self, omit_bye=True):
        """Return the percentage of matches won (minimum 0.33) excluding BYEs"""
        n = float(len(self.previous_opponents))
        mp = self.match_points
        if omit_bye and 'BYE' in self.previous_opponents:
            mp -= 3
            n -= 1
        return max(0.33, mp / (3 * n or -1))

    def game_win_percentage(self, game_points_for_bye=GAME_POINTS_PER_BYE, omit_bye=True):
        """Return the percentage of games won (minimum 0.33) excluding BYEs"""
        n = float(self.games_played)
        gp = self.game_points
        if omit_bye and 'BYE' in self.previous_opponents:
            gp -= game_points_for_bye
        return max(0.33, gp / (3 * n or -1))

    def opponent_match_win_percentage(self, standings=STANDINGS):
        """Return the average match win percentage of opponents played"""
        tot = 0
        n = 0
        for opp in self.get_opponents(standings):
            n += 1
            tot += opp.match_win_percentage()
        return tot / (n or -1)

    def opponent_game_win_percentage(self, standings=STANDINGS):
        """Return the average game win percentage of opponents played"""
        tot = 0
        n = 0
        for opp in self.get_opponents(standings):
            n += 1
            tot += opp.game_win_percentage()
        return tot / (n or -1)

    def get_opponents(self, standings=STANDINGS):
        """Gets the PlayerStanding objects for players this player has played against"""
        return [standings[player_or_bye(p)] for p in self.previous_opponents if p != 'BYE']

    def standing_tuple(self):
        """Returns a tuple which has metrics for evaluating rank in priority order"""
        return (self.match_points,
                self.opponent_match_win_percentage(),
                self.game_win_percentage(),
                self.opponent_game_win_percentage())

    def __cmp__(self, other):
        """Higher standings come first"""
        ret = -cmp(self.standing_tuple(), other.standing_tuple())
        if ret == 0:
            return cmp(self.player, other.player)
        return ret

    def __eq__(self, other):
        if not isinstance(other, PlayerStanding):
            return False
        return self.__cmp__(other) and self.player == other.player

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        fmt = '%010s    MP=%2d    OMW%%=%.3f    gp=%2d    OGW%%=%.2f  MW%%=%.2f  GW%%=%.2f  #GP=%2d  Elo=%d  opp=[%s]'
        prev_opp_str = ','.join(str(player_or_bye(p))
                               for p in sorted(self.previous_opponents,
                                               key=lambda p : player_or_bye(p)))
        return fmt % (self.player,
                      self.match_points,
                      self.opponent_match_win_percentage(),
                      self.game_points,
                      self.opponent_game_win_percentage(),
                      self.match_win_percentage(),
                      self.game_win_percentage(),
                      self.games_played,
                      self.rating,
                      prev_opp_str)

def player_or_bye(p):
    """Return the player's name (or BYE if p is a BYE)"""
    if p == 'BYE':
        return p
    return p.player


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
    player_standings.sort()
    if len(player_standings) % 2:
        # give a BYE to the lowest ranked player who has not received a BYE
        for player in player_standings[::-1]:
            if 'BYE' not in player.previous_opponents:
                break
        bye_player = player
        player_standings.remove(player)
        assert len(player_standings) % 2 == 0
    else:
        bye_player = None

    tries = 100
    while True:
        pairings = _random_pairings(player_standings)
        if pairings:
            if bye_player:
                pairings.append((bye_player, 'BYE'))
            return pairings
        elif tries:
            tries -= 1
            if not tries:
                raise Exception("no pairings found")


def _random_pairings(player_standings):
    """Helper function which attempts to assign pairings to a specified group of
    players.  Must be an even number of players.
    """
    assert len(player_standings) % 2 == 0
    # Assign pairings from the top-down -- start with undefeated players.
    pairings = []
    leftover_player = None
    while player_standings:
        print len(player_standings), 'left to pair'

        # get the players in the top remaining group
        cur_match_points = player_standings[0].match_points
        next_mp_idx = 0
        while next_mp_idx < len(player_standings) and \
                player_standings[next_mp_idx].match_points == cur_match_points:
            next_mp_idx += 1
        players_in_group = player_standings[:next_mp_idx]
        player_standings = player_standings[next_mp_idx:]

        # if only 1 player in this group and no leftovers, then defer them to
        # the next group (nobody to pair with yet)
        if len(players_in_group) == 1:
            if not leftover_player:
                leftover_player = players_in_group[0]
                continue

        # randomly pair up those in this group along with any leftover
        # player from the last group
        group_pairing_tries = 100
        while True:
            ret = _random_group_pairings(players_in_group[:], leftover_player)
            if not ret:
                group_pairing_tries -= 1
                if not group_pairing_tries:
                    return None
            else:
                pairings += ret[0]
                leftover_player = ret[1]
                break  # successfully paired the group
    return pairings


def _random_group_pairings(players_in_group, leftover_player=None):
    """Randomly pair up the players in players_in_group, plus leftover_player if
    provided.  leftover_player MUST be paired when provided.

    Returns 2-tuple of (list of 2-tuples of players paired, leftover_player).
    None is returned if the random pairing failed.  This does not mean there is
    NO pairing, just that the random pairing attempted was invalid (e.g., it
    tried to pair two players who had played before).
    """
    random.shuffle(players_in_group)
    # leftover player always first in line to ensure they aren't leftover again
    if leftover_player:
        players_to_pair = [leftover_player] + players_in_group
    else:
        players_to_pair = players_in_group

    new_leftover_player = None
    group_pairings = []
    while players_to_pair:
        p1 = players_to_pair.pop(0)
        if not players_to_pair:
            new_leftover_player = p1
            break
        else:
            paired = False
            for p2 in players_to_pair:
                if p1 not in p2.previous_opponents:
                    players_to_pair.remove(p2)
                    group_pairings.append((p1, p2))
                    paired = True
                    break
            if not paired:
                # oops, couldn't pair p1 with anyone ... could do actual
                # backtracking here until we're sure no possible pairing exists,
                # but let's be lazy ...
                return None
    return group_pairings, new_leftover_player
