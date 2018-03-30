from PyQt5.QtCore import Qt, QRect, QRectF, QPointF
from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtGui import QColor, QPen, QFont
from itertools import product, takewhile
import os

from .lettertile_ui import LetterTileUI

import pandas as pd

# Read words.csv file for words.csv that act a dictionary for the game
# Read board_multiplier.csv file for assigning colors and score labels
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DEFAULT_WORDS_PATH = os.path.join(BASE_DIR, 'data', 'words.csv')
BOARD_MULTIPLIER_PATH = os.path.join(BASE_DIR, 'data', 'board_multiplier.csv')

class BoardUI(QGraphicsItem):
    '''
    A graphical representation of a scrabble board. It also keeps track of
    all Letters 'placed' on it.
    '''

    CELL_SIZE = LetterTileUI.LETTER_SIZE + 1.5
    LEGEND_SIZE = int((LetterTileUI.LETTER_SIZE + 5) / 2)
    COLOR_EVEN = QColor(245, 245, 245)
    COLOR_ODD = QColor(240, 240, 240)
    COLOR_HIGHLIGHT = QColor('#fff5a6')
    PEN_GRID = QPen(QColor(204, 204, 204), 1, Qt.SolidLine)
    FONT_LEGEND = QFont('Sans', int((LetterTileUI.LETTER_SIZE + 10) / 5))
    PEN_LEGEND = QPen(QColor('#000'), 1, Qt.SolidLine)

    # Read Board Multiplier CSV
    df = pd.read_csv(BOARD_MULTIPLIER_PATH, header=None)

    def __init__(self, width, height):
        '''
        Construct a new BoardUI
        '''
        super().__init__()

        # Read Words CSV
        self.words = pd.read_csv(DEFAULT_WORDS_PATH, sep=',', header=None).values
        self.width = width
        self.height = height
        self.rect = QRectF(0, 0, width * self.CELL_SIZE + self.LEGEND_SIZE, height * self.CELL_SIZE + self.LEGEND_SIZE)
        self.letters = [None for _ in range(width * height)]
        self.highlight = None

    def boundingRect(self):
        '''
        Required by QGraphicsItem
        '''
        return self.rect

    def paint(self, painter, objects, widget):
        '''
        Required by QGraphicsItem
        '''
        painter.setFont(self.FONT_LEGEND)
        
        for y, x in product(range(self.height), range(self.width)):

            painter.setPen(self.PEN_GRID)
            currentGrid = self.df.loc[x, y]

            # Using Python Dictionary to map the score labels and colors
            colorDict = {'w3': QColor(241, 63, 63), 'w2': QColor(249, 187, 190),
                         'l3': QColor(8, 170, 253), 'l2': QColor(95, 224, 255),
                         '1': QColor(11, 158, 129), 'm': QColor(249, 187, 190)}
            textDict = {'w3': 'Triple\nWord', 'w2': 'Double\nWord',
                        'l3': 'Triple\nLetter', 'l2': 'Double\nLetter',
                        '1': "", 'm': ""}
            
            painter.setBrush(colorDict.get(currentGrid))

            painter.drawRect(self.LEGEND_SIZE + x * self.CELL_SIZE,
                             self.LEGEND_SIZE + y * self.CELL_SIZE,
                             self.CELL_SIZE, self.CELL_SIZE)
            
            painter.setPen(QPen(QColor('#000'), Qt.SolidLine))

            painter.drawText(QRect(self.LEGEND_SIZE + x * self.CELL_SIZE,
                             self.LEGEND_SIZE + y * self.CELL_SIZE,
                             self.CELL_SIZE, self.CELL_SIZE),Qt.AlignCenter,str(textDict.get(currentGrid)))
            
            if x == 0:
                painter.setPen(self.PEN_LEGEND)
                painter.drawText(QRect(0, self.LEGEND_SIZE + y *
                                       self.CELL_SIZE, self.LEGEND_SIZE - 4,
                                       self.CELL_SIZE),
                                 Qt.AlignCenter | Qt.AlignRight, str(y))
            if y == 0:
                painter.setPen(self.PEN_LEGEND)
                painter.drawText(QRect(self.LEGEND_SIZE + x * self.CELL_SIZE,
                                       0, self.CELL_SIZE, self.LEGEND_SIZE - 2),
                                 Qt.AlignCenter | Qt.AlignBottom, str(x))

    def get_position(self, letter):
        '''
        Get the coordinates of the letter on the board
        '''
        position = self.mapFromScene(letter.center())
        x = position.x() - self.LEGEND_SIZE
        y = position.y() - self.LEGEND_SIZE
        ix = int(x / self.CELL_SIZE)
        iy = int(y / self.CELL_SIZE)
        if x < 0 or y < 0 or x > self.width * self.CELL_SIZE or \
                y > self.height * self.CELL_SIZE or \
                self.letters[iy * self.width + ix] is not None:
            return None
        else:
            return (ix, iy)

    def letterMoveEvent(self, letter):
        '''
        Event that occurs when letter is moved
        '''
        self.highlight = self.get_position(letter)
        self.update(self.rect)

    def letterMoveOutEvent(self, letter):
        '''
        Event that occurs when letter is moved out
        '''
        self.highlight = None
        self.update(self.rect)

    def letterReleaseEvent(self, letter):
        '''
        Event that occurs when a letter is released
        '''
        pos = self.get_position(letter)
        letter.own(self, *pos) if pos else letter.undo()
        self.highlight = None
        self.update(self.rect)

    def addLetter(self, letter, x, y, move=True):
        '''
        Places a letter on the board
        '''
        self.letters[y * self.width + x] = letter
        pos = QPointF(self.LEGEND_SIZE + x * self.CELL_SIZE +
                      int((self.CELL_SIZE - letter.LETTER_SIZE) / 2),
                      self.LEGEND_SIZE + y * self.CELL_SIZE +
                      int((self.CELL_SIZE - letter.LETTER_SIZE) / 2))
        (letter.move if move else letter.setPos)(self.mapToScene(pos))

    def removeLetter(self, letter, x, y, move=True):
        '''
        Removes a letter on the board
        '''
        self.letters[y * self.height + x] = None

    def getLetter(self, x, y):
        '''
        Get the letter at position (x, y)
        '''
        return self.letters[y * self.height + x]

    def getLetterPosition(self, letter):
        '''
        Get the position of a letter
        '''
        for i, l in enumerate(self.letters):
            if letter == l:
                return (i % self.width, int(i / self.width))

    def validateWord(self):
        '''
        Validate word
        '''
        return self.currentWord in self.words

    def validNewWord(self):
        '''
        Checks if there is one valid new word on the board
        '''
        letters_ = [l for l in self.letters if l and not l.is_safe]
        letters = [self.getLetterPosition(l) for l in letters_]
        old_letters = [l for l in self.letters if l and l.is_safe]

        if len(letters) == 0 or \
                not (len(set(l[0] for l in letters)) == 1 or
                     len(set(l[1] for l in letters)) == 1):
            return False

        letter = letters[0]
        direction = 'right'

        if len(letters) == 1:
            l = letters[0]
            if (l[1] - 1 >= 0 and self.getLetter(l[0], l[1] - 1)) or \
                    (l[1] + 1 < self.height and self.getLetter(l[0], l[1] + 1)):
                direction = 'down'
        elif letters[0][0] == letters[-1][0]:
            direction = 'down'

        if direction == 'right':
            row = [self.getLetter(x, letter[1]) for x in range(self.width)]
            pivot = letter[0]
        else:
            row = [self.getLetter(letter[0], y) for y in range(self.height)]
            pivot = letter[1]

        word_right = list(takewhile(lambda x: x, row[pivot:]))
        word_left = row[:pivot]
        word_left.reverse()
        word_left = list(takewhile(lambda x: x, word_left))
        word_left.reverse()
        word = word_left + word_right

        wordStr = ''
        for letterItem in word:
            wordStr += letterItem.char.lower()
        self.currentWord = wordStr

        return all(l is not None for l in word) and \
               (not old_letters or any(l.is_safe for l in word)) and \
               all(l in word for l in letters_)

    def getNewWord(self):
        '''
        Gets the new word placed on board
        '''
        letters = [self.getLetterPosition(l) for l in self.letters if l and not l.is_safe]
        letter = letters[0]
        direction = 'right'

        if len(letters) == 1:
            l = letters[0]
            if (l[1] - 1 >= 0 and self.getLetter(l[0], l[1] - 1)) or \
                    (l[1] + 1 < self.height and self.getLetter(l[0], l[1] + 1)):
                direction = 'down'
        elif letters[0][0] == letters[-1][0]:
            direction = 'down'

        if direction == 'right':
            row = [self.getLetter(x, letter[1]) for x in range(self.width)]
            pivot = letter[0]
        else:
            row = [self.getLetter(letter[0], y) for y in range(self.height)]
            pivot = letter[1]

        word_right = list(takewhile(lambda x: x, row[pivot:]))
        word_left = row[:pivot]
        word_left.reverse()
        word_left = list(takewhile(lambda x: x, word_left))
        word_left.reverse()
        word = word_left + word_right
        x, y = self.getLetterPosition(word[0])

        return self.getLetterPosition(word[0]) + \
               (direction, ''.join(l.char for l in word).lower())
