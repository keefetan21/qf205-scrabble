from .letter import Letter
from itertools import chain
import pandas as pd
import os

# Absolute path of Board Multiplier CSV
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
BOARD_MULTIPLIER_PATH = os.path.join(BASE_DIR, 'data', 'board_multiplier.csv')

class Board:
    '''
    Board class which contains information about the Scrabble Board
    '''

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.board = [None for _ in range(0, width * height)]

        # Read Board Multiplier CSV
        self.board_score = pd.read_csv(BOARD_MULTIPLIER_PATH, header=None)

    def __iter__(self):
        '''
        Define Board as an Iterator
        '''
        for i, c in enumerate(self.board):
            if c is not None:
                yield (i % self.width, int(i / self.width), c)

    def add_letter(self, letter):
        '''
        Add a new Letter to the board
        '''
        pos = letter.y * self.width + letter.x
        self.board[pos] = letter

    # DEPRECATE - NOT USED
    # def add_word(self, x, y, direction, word, player=None):
    #     '''
    #     Add a new word to the board
    #     '''
    #     for i, c in enumerate(word):
    #         xi = x + i if direction == 'right' else x
    #         yi = y + i if direction == 'down' else y
    #         if self.get_letter(xi, yi) is not None:
    #             continue
    #         self.add_letter(Letter(c, player, xi, yi))

    def get_letter(self, x, y):
        '''
        Get the Letter object at the specified position
        '''
        return self.board[y * self.width + x]

    def get_rows(self):
        '''
        Get all rows on the Board
        '''
        return (self.board[y * self.width:(y + 1) * self.width] for y in range(0, self.height))

    def get_columns(self):
        '''
        Get all columns on the Board
        '''
        return ((self.get_letter(x, y) for y in range(0, self.height)) for x in range(0, self.width))

    def get_words(self):
        '''
        Returns a generator which yields all words on the board
        '''
        for line in chain(self.get_rows(), self.get_columns()):
            word = []
            for letter in line:
                if letter is None:
                    if len(word) > 1:
                        yield (word[0].x, word[0].y, 'right' if word[0].x != word[1].x else 'down',
                               ''.join(l.char for l in word))
                    word = []
                else:
                    word.append(letter)

            if len(word) > 1:
                yield (word[0].x, word[0].y, 'right' if word[0].x != word[1].x else 'down',
                       ''.join(l.char for l in word))

    def get_word_score(self, letter_set, x, y, direction, word):
        '''
        Calculate Word Score
        Logic behind scoring:
        1. Check if all adjacent words are valid
        2. Confirm with users that he/she wants to put the word in this location
        3. Calculate double/triple letters
        4. Calculate double/triple scores
        '''
        letters = [(x if direction == 'down' else x + i,
                    y if direction == 'right' else y + i, word[i]) for i in range(len(word))]
        new_letters = []
        for x, y, c in letters:
            if self.get_letter(x, y) is None:
                new_letters.append((x, y, c))

        old_words = list(w for w in self.get_words())
        for x, y, c in new_letters:
            self.add_letter(Letter(c, None, x, y))
        new_words = list(w for w in self.get_words())

        really_new_words = []
        for w in new_words:
            if w not in old_words:
                really_new_words.append(w)

        for x, y, c in new_letters:
            self.board[y * self.width + x] = None

        formula = self.score_with_bonus(letter_set, really_new_words)

        return eval(formula)

    def score_with_bonus(self, letter_set, really_new_words):
        '''
        Calculate Bonus Score
        '''
        board_bonus = {"m": "*2", "w2": "*2", "w3": "*3", "l2": "2", "l3": "3"}

        start = really_new_words[0][0]
        end = really_new_words[0][1]
        formula = "("
        word_multiplier = ""
        word = really_new_words[0][3]

        for i in range(len(word)):
            if really_new_words[0][2] == "down":
                bonus_tile = self.board_score.loc[start, end + i]
            else:
                bonus_tile = self.board_score.loc[start + i, end]

            multiplier = str(board_bonus.get(bonus_tile, "1"))

            if "w" in bonus_tile or "m" in bonus_tile:
                multiplier = "1"
                word_multiplier += board_bonus.get(bonus_tile)

            formula += str(letter_set.get_score(word[i])) + "*" + multiplier

            if i < len(word) - 1:
                formula += ("+")
            else:
                formula += ")" + word_multiplier

        return formula
