from .board import Board
from .letterset import LetterSet
from .letter import Letter

import numpy as np

class Game:
    '''
    A Game class which contains all information with regards to the Scrabble game
    '''
    RUNNING = 'running'
    GAME_OVER = 'gameover'

    def __init__(self, width, height, rack_size):
        '''
        Construct a new Game object
        '''
        self.width = width
        self.height = height
        self.rack_size = rack_size
        self.board = Board(width, height)
        self.letters = LetterSet()
        self.players = []
        self.current_player = None
        self.moves = []
        self.get_letters = self.letters.get_random_letters
        self.lap = 0
        self.turn = 0
        self.empty = True

    def get_state(self):
        '''
        Returns the state of the game
        '''

        # Retrieve last 4 moves
        last_moves = self.moves[-4:]

        if (self.letters.remaining_letters == 0 and any(not p.letters for p in self.players)):
            return self.GAME_OVER
        return self.RUNNING

    def add_player(self, player):
        '''
        Add a new player to the list of players
        '''
        self.players.append(player)

        # Shuffle the order of play
        np.random.shuffle(self.players)


    def set_next_player(self):
        '''
        Set the next player
        '''
        assert self.get_state() == self.RUNNING
        self.turn += 1
        self.lap = int((self.turn - 1) / len(self.players)) + 1
        self.current_player = self.players[(self.turn - 1) % len(self.players)]

    def get_next_player(self):
        '''
        Get next player
        '''
        return self.current_player

    def add_word_by_current_player(self, player, x, y, direction, word):
        '''
        Retrieve letters placed by current player and calculate score achieved. Remove letters that were used for
        current player
        '''

        # Retrieve letters placed by current player
        letters_placed_by_current_player = [(x if direction == 'down' else x + i, y if direction ==
                    'right' else y + i, word[i]) for i in range(len(word))]

        # Calculate score achieved by current player for letters placed
        player.score += self.board.get_word_score(self.letters, x, y, direction, word)

        # Removed used letters for current player
        for x, y, c in letters_placed_by_current_player:
            if self.board.get_letter(x, y) is None:
                self.board.add_letter(Letter(c, player, x, y))
                pos = player.letters.index(c)
                player.letters = player.letters[:pos] + player.letters[pos+1:]

    # Deprecate
    # def finish_score(self):
        # assert self.get_state() == self.GAME_OVER
        # print(self.moves)
        # if self.moves[-1][1][0] == Player.PLACE_WORD:
        #     print('MOVES', self.moves[-1][1][0])
        #     winner = self.moves[-1][0]
        #     print('Winner', winner)
        #     for player in self.players:
        #         if player != winner:
        #             score = sum(self.letters.get_score(c) for c in
        #                         player.letters)
        #             player.score -= score
        #             winner.score += score
        #             print('SCORE OF ', player, ': ', score)
        # else:
        #     for player in self.players:
        #         score = sum(self.letters.get_score(c) for c in player.letters)
        #         player.score -= score
        #         print('Player\'s Letters', player.letters)
        #         print('SCORE OF ', player, ': ', score)