from PyQt5.QtCore import Qt, QRect, QRectF, QPointF
from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtGui import QColor, QPen, QFont
from itertools import product, takewhile
import os

from .lettertile_ui import LetterTileUI

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DEFAULT_WORDS_PATH = os.path.join(BASE_DIR, 'data', 'words.csv')

class BoardUI(QGraphicsItem):
    '''
    A graphical representation of a scrabble board. It also keeps track of
    all LetterItems 'placed' on it.
    '''
    CELL_SIZE = LetterTileUI.LETTER_SIZE + 1.5
    LEGEND_SIZE = int((LetterTileUI.LETTER_SIZE + 5) / 2)
    COLOR_EVEN = QColor(245, 245, 245)
    COLOR_ODD = QColor(240, 240, 240)
    COLOR_HIGHLIGHT = QColor('#fff5a6')
    PEN_GRID = QPen(QColor(204, 204, 204), 1, Qt.SolidLine)
    FONT_LEGEND = QFont('Sans', int((LetterTileUI.LETTER_SIZE + 10) / 5))
    PEN_LEGEND = QPen(QColor('#fff'), 1, Qt.SolidLine)
    df = pd.read_csv("data/board_multiplier.csv", header=None)

    def __init__(self, width, height):
        ''' Construct a new BoardItem '''
        super().__init__()

        # load csv here

        self.words = pd.read_csv(
            DEFAULT_WORDS_PATH, sep=',', header=None).values
        self.width = width
        self.height = height
        self.rect = QRectF(0, 0, width * self.CELL_SIZE + self.LEGEND_SIZE,
                           height * self.CELL_SIZE + self.LEGEND_SIZE)
        self.letters = [None for _ in range(width * height)]
        self.highlight = None

    def boundingRect(self):
        ''' Required by QGraphicsItem '''
        return self.rect

    def paint(self, painter, objects, widget):
        ''' Required by QGraphicsItem '''
        painter.setFont(self.FONT_LEGEND)

        for y, x in product(range(self.height), range(self.width)):

            painter.setPen(self.PEN_GRID)
            if self.highlight == (x, y):
                painter.setBrush(self.COLOR_HIGHLIGHT)
            else:
                currentGrid = self.df.loc[x, y]

                colorDict = {'w3': QColor(241, 63, 63), 'w2': QColor(249, 187, 190), \
                             'l3': QColor(8, 170, 253), 'l2': QColor(95, 224, 255), \
                             '1': QColor(11, 158, 129), 'm': QColor(249, 187, 190)}
                painter.setBrush(colorDict.get(currentGrid))

            #               painter.setBrush(self.COLOR_ODD if (x + y) % 2 != 0 else
            #                                 self.COLOR_EVEN)

            painter.drawRect(self.LEGEND_SIZE + x * self.CELL_SIZE,
                             self.LEGEND_SIZE + y * self.CELL_SIZE,
                             self.CELL_SIZE, self.CELL_SIZE)

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

    def position(self, letter):
        ''' Get the x and y position of the letter referring to the board '''
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
        ''' Custom letter event '''
        self.highlight = self.position(letter)
        self.update(self.rect)

    def letterMoveOutEvent(self, letter):
        ''' Custom letter event '''
        self.highlight = None
        self.update(self.rect)

    def letterReleaseEvent(self, letter):
        ''' Custom letter event '''
        pos = self.position(letter)
        letter.own(self, *pos) if pos else letter.undo()
        self.highlight = None
        self.update(self.rect)

    def addLetter(self, letter, x, y, move=True):
        ''' Gets call'd to place a letter on the board '''
        assert self.letters[y * self.width + x] is None
        self.letters[y * self.width + x] = letter
        pos = QPointF(self.LEGEND_SIZE + x * self.CELL_SIZE +
                      int((self.CELL_SIZE - letter.LETTER_SIZE) / 2),
                      self.LEGEND_SIZE + y * self.CELL_SIZE +
                      int((self.CELL_SIZE - letter.LETTER_SIZE) / 2))
        (letter.move if move else letter.setPos)(self.mapToScene(pos))

    def removeLetter(self, letter, x, y, move=True):
        ''' Gets call'd to remove a letter from the board '''
        assert self.letters[y * self.height + x] == letter
        self.letters[y * self.height + x] = None

    def getLetter(self, x, y):
        ''' Get the letter at position (x, y) '''
        assert x >= 0 and x < self.width and y >= 0 and y < self.height
        return self.letters[y * self.height + x]

    def getLetterPosition(self, letter):
        ''' Get the position of a letter '''
        for i, l in enumerate(self.letters):
            if letter == l:
                return (i % self.width, int(i / self.width))

    def validateWord(self):
        return self.currentWord in self.words

    def validNewWord(self):
        # pass
        ''' Checks if there is one valid new word on the board '''
        letters_ = [l for l in self.letters if l and not l.is_safe]
        letters = [self.getLetterPosition(l) for l in letters_]
        old_letters = [l for l in self.letters if l and l.is_safe]
        # if(not all (elem is None for elem in letters)):
        #     if(self.letters[112] == None):
        #         raise Exception("Please start at the center")

        # if(self.letters[112] == None):
        #     return False

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
        ''' Gets the new word '''
        assert self.validNewWord()
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
