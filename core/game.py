from .board import Board
from .letterset import LetterSet
from .letter import Letter
from .player import Player

import numpy as np

class Game:
    '''
    A basic Game model which holds all information about a game and runs it
    by the implemented scrabble logic.
    '''
    RUNNING = 'running'
    GAME_OVER = 'gameover'

    def __init__(self, width, height, rack_size):
        ''' Construct a new Game object '''
        self.width = width
        self.height = height
        self.rack_size = rack_size
        self.board = Board(width, height)
        self.letters = LetterSet()
        self.players = []
        self.current_player = None
        self.moves = []
        self.get_letters = self.letters.random_letters
        self.lap = 0
        self.turn = 0
        self.empty = True


    def state(self):
        ''' The state of the game '''
        last_moves = self.moves[-4:]
        if (len(last_moves) == 4 and all(m[0] != Player.PLACE_WORD for p,m
                                         in last_moves)) or \
           (self.letters.remaining_letters == 0 and any(not p.letters for p
                                                        in self.players)):
            return self.GAME_OVER
        return self.RUNNING

    def add_player(self, player):
        '''Add a new player to the list of players'''
        self.players.append(player)
        np.random.shuffle(self.players)


    def next_player(self):
        ''' Set and return the next player '''
        assert self.state() == self.RUNNING
        self.turn += 1
        self.lap = int((self.turn - 1) / len(self.players)) + 1
        self.current_player = self.players[(self.turn - 1) % len(self.players)]
        return self.current_player

    def check_move(self, x, y, direction, word):
        return True

    def add_word(self, player, x, y, direction, word):
        letters = [(x if direction == 'down' else x + i, y if direction ==
                    'right' else y + i, word[i]) for i in range(len(word))]

        player.score += self.board.get_word_score(self.letters, x, y,
                                                  direction, word)

        for x, y, c in letters:
            if self.board.get_letter(x, y) is None:
                self.board.add_letter(Letter(c, player, x, y))
                pos = player.letters.index(c)
                player.letters = player.letters[:pos] + player.letters[pos+1:]

    def finish_score(self):
        assert self.state() == self.GAME_OVER
        if self.moves[-1][1][0] == Player.PLACE_WORD:
            winner = self.moves[-1][0]
            for player in self.players:
                if player != winner:
                    score = sum(self.letters.get_score(c) for c in
                                player.letters)
                    player.score -= score
                    winner.score += score
        else:
            for player in self.players:
                score = sum(self.letters.get_score(c) for c in player.letters)
                player.score -= score