#!/usr/bin/env python
# -*- coding: utf-8 -*-

from itertools import product, takewhile
from operator import attrgetter

from PyQt5.QtCore import Qt, QRect, QRectF, QSizeF, QPointF, pyqtSignal, QPropertyAnimation
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QGraphicsItem, QGraphicsScene, QGraphicsView, QGroupBox, QLabel, \
                        QPushButton,QGraphicsWidget, QMessageBox, QInputDialog
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont
from os.path import abspath, join, dirname
from common import Player
import pandas as pd
PROJECT_PATH = dirname(abspath(__file__))
DEFAULT_WORDS_PATH = join(PROJECT_PATH, 'data', 'words.csv')
class LetterItem(QGraphicsWidget):
    '''
    A dragable objects which represents a game tile and is used as
    an intuitive way of interaction
    '''
    LETTER_SIZE = 50
    LETTER_FONT = QFont('Sans', 50/2, QFont.DemiBold)
    LETTER_PEN = QPen(QColor('#444444'), 1, Qt.SolidLine)
    SCORE_FONT = QFont('Sans', 50/6)
    SCORE_PEN = QPen(QColor('#666666'), 1, Qt.SolidLine)
    LETTER_CENTER = QPointF(25, 25)
    BOUNDING_RECT = QRectF(0, 0, 50, 50)

    def __init__(self, char, score, color, safe=False):
        ''' Construct a new visual representation of a tile '''
        super().__init__()
        self.owner = None
        self.char = char.upper()
        self.score = str(score)
        self.is_safe = safe
        self.color_border = QColor(color).lighter(100)
        self.color_bg = QColor(color).lighter(150)
        self.normal_pen = QPen(self.color_border, 1, Qt.SolidLine)
        self.safe_pen = QPen(self.color_border, 2, Qt.SolidLine)
        self.selected_pen = QPen(self.color_border, 3, Qt.DashLine)
        self.normal_brush = self.color_bg.lighter(110)
        self.safe_brush = self.color_bg
        self.hovers = set()
        self.selected = False
        self.view = None
        self.animation = None
        self.deleted = False
        self.size = QSizeF(self.LETTER_SIZE, self.LETTER_SIZE)
        self.setFlag(self.ItemIsMovable, not safe)
        self.setFlag(self.ItemSendsGeometryChanges, not safe)
        self.setCursor(Qt.ArrowCursor if safe else Qt.OpenHandCursor)
        self.setZValue(1)
        self.setOpacity(0)

    def boundingRect(self):
        ''' Required by QGraphicsItem '''
        return self.BOUNDING_RECT

    def paint(self, painter, objects, widget):
        ''' Required by QGraphicsItem '''
        painter.setBrush(self.safe_brush if self.is_safe else self.normal_brush)
        if self.selected:
            painter.setPen(self.selected_pen)
        elif self.is_safe:
            painter.setPen(self.safe_pen)
        else:
            painter.setPen(self.normal_pen)
        painter.drawRoundedRect(0, 0, self.LETTER_SIZE, self.LETTER_SIZE,
                                self.LETTER_SIZE/8, self.LETTER_SIZE/8)

        painter.setFont(self.LETTER_FONT)
        painter.setPen(self.LETTER_PEN)
        painter.drawText(QRect(0, 0, self.LETTER_SIZE, self.LETTER_SIZE),
                         Qt.AlignCenter, self.char)

        painter.setFont(self.SCORE_FONT)
        painter.setPen(self.SCORE_PEN)
        painter.drawText(QRect(0, 0, self.LETTER_SIZE-3, self.LETTER_SIZE-1),
                         Qt.AlignRight | Qt.AlignBottom, self.score)

    def itemChange(self, change, value):
        ''' Item change event to control item movement '''
        if not self.view and self.scene() and self.scene().views():
            self.view = self.scene().views()[0]
        if change == self.ItemPositionChange and self.view:
            rect = self.view.viewport().geometry()
            rect.moveTo(0, 0)
            rect = self.view.mapToScene(rect).boundingRect()
            if not rect.contains(QRectF(value, self.size)):
                value.setX(min(max(value.x(), rect.left()), rect.right() -
                               self.LETTER_SIZE))
                value.setY(min(max(value.y(), rect.top()), rect.bottom() -
                               self.LETTER_SIZE))
                return value
        elif change == self.ItemVisibleChange and self.isVisible() and \
             not self.deleted:
            self.animation = QPropertyAnimation(self, b'opacity')
            self.animation.setDuration(250)
            self.animation.setStartValue(0)
            self.animation.setEndValue(1)
            self.animation.start()
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        ''' Fired when the LetterItem is pressed '''
        self.last_valid_position = self.scenePos()
        self.hovers = set()
        self.setZValue(1000)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        '''
        Fired when the LetterItem is moved, propagates a custom letter event
        to underlying RackItem and BoardItem objects
        '''
        super().mouseMoveEvent(event)
        pos = self.scenePos() + self.LETTER_CENTER
        items = set(item for item in self.scene().items(pos)
                    if type(item) in (RackItem, BoardItem))
        for item in items:
            item.letterMoveEvent(self)
        for item in self.hovers:
            if item not in items:
                item.letterMoveOutEvent(self)
        self.hovers = items

    def mouseReleaseEvent(self, event):
        '''
        Fired when the LetterItem is released, propagates a custom letter event
        to underlying RackItem and BoardItem objects
        '''
        self.setZValue(1)
        super().mouseReleaseEvent(event)
        if self.last_valid_position == self.scenePos() and not self.is_safe:
            self.selected = not self.selected
            if self.scene() and self.scene().views():
                self.scene().views()[0].letterChanged.emit()
        else:
            items = self.scene().items(self.scenePos() + self.LETTER_CENTER)
            for item in items:
                if type(item) in (RackItem, BoardItem):
                    return item.letterReleaseEvent(self)
            self.move(self.last_valid_position)

    def undo(self):
        ''' Moves the LetterItem back to the last valid position '''
        self.move(self.last_valid_position)

    def own(self, new_owner, *args, **kwargs):
        '''
        Removes the Letter from a maybe existing owner and calls the new
        owners addLetter routine
        '''
        if self.owner:
            self.owner.removeLetter(self, *self.owner_args,
                                    **self.owner_kwargs)
        if new_owner:
            self.owner = new_owner
            self.owner_args = args
            self.owner_kwargs = kwargs
            self.owner.addLetter(self, *args, **kwargs)

            if self.scene() and self.scene().views():
                self.scene().views()[0].letterChanged.emit()

    def move(self, pos):
        ''' A simple animation to move the letter '''
        self.animation = QPropertyAnimation(self, b'pos')
        self.animation.setDuration(100)
        self.animation.setStartValue(self.scenePos())
        self.animation.setEndValue(pos)
        self.animation.start()

    def center(self):
        ''' Get the center position of the Letter '''
        return self.scenePos() + self.LETTER_CENTER

    def remove(self):
        self.scene().removeItem(self)
        del self

    def fade(self):
        if self.animation:
            self.animation.stop()
        self.deleted = True
        self.animation = QPropertyAnimation(self, b'opacity')
        self.animation.setDuration(250)
        self.animation.setStartValue(self.opacity())
        self.animation.setEndValue(0)
        self.animation.finished.connect(self.remove)
        self.animation.start()


class BoardItem(QGraphicsItem):
    '''
    A graphical representation of a scrabble board. It also keeps track of
    all LetterItems 'placed' on it.
    '''
    CELL_SIZE = LetterItem.LETTER_SIZE + 10
    LEGEND_SIZE = int((LetterItem.LETTER_SIZE + 10) / 2)
    COLOR_EVEN = QColor(245, 245, 245)
    COLOR_ODD = QColor(240, 240, 240)
    COLOR_HIGHLIGHT = QColor('#fff5a6')
    PEN_GRID = QPen(QColor(204, 204, 204), 1, Qt.SolidLine)
    FONT_LEGEND = QFont('Sans', int((LetterItem.LETTER_SIZE + 10) / 5))
    PEN_LEGEND = QPen(QColor('#888888'), 1, Qt.SolidLine)

    def __init__(self, width, height):
        ''' Construct a new BoardItem '''
        super().__init__()

        #load csv here 
        
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
        for y,x in product(range(self.height), range(self.width)):
            painter.setPen(self.PEN_GRID)
            if self.highlight == (x, y):
                painter.setBrush(self.COLOR_HIGHLIGHT)
            else:
                painter.setBrush(self.COLOR_ODD if (x + y) % 2 != 0 else
                                 self.COLOR_EVEN)
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
                                       0, self.CELL_SIZE, self.LEGEND_SIZE -2),
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
        for i,l in enumerate(self.letters):
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
                

        if(self.letters[112] == None):
            return False

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
        x,y = self.getLetterPosition(word[0])

        return self.getLetterPosition(word[0]) + \
               (direction, ''.join(l.char for l in word).lower())
        


class RackItem(QGraphicsItem):
    '''
    A graphical representation of a scrabble rack. It also keeps track of
    all LetterItems 'placed' on it.
    '''
    CELL_SIZE = LetterItem.LETTER_SIZE + 10
    CELL_PEN = QPen(QColor(204,204,204), 1, Qt.SolidLine)
    CELL_BRUSH = QColor(245,245,245)
    LEGEND_SIZE = int((LetterItem.LETTER_SIZE + 10) * 3 / 4)
    FONT = QFont('Sans', int(LetterItem.LETTER_SIZE/4))
    COLOR_HIGHLIGHT = QColor('#fff5a6')

    def __init__(self, size, width, height):
        ''' Construct a new RackItem '''
        super().__init__()
        self.name = 'Unknown'
        self.color = '#000000'
        self.size = size
        self.width = size * self.CELL_SIZE
        self.height = int(self.CELL_SIZE * 7 / 4)
        self.rect = QRectF(0, 0, self.width, self.height)
        self.highlight = None
        self.letters = [None for _ in range(size)]
        self.setPos((max(self.width, width * 60 + 30) - self.width) / 2, 60 * height + 30)

    def boundingRect(self):
        ''' Required by QGraphicsItem '''
        return self.rect

    def paint(self, painter, objects, widget):
        ''' Required by QGraphicsItem '''
        painter.setPen(self.CELL_PEN)
        painter.setBrush(self.CELL_BRUSH)
        painter.drawRoundedRect(0, int(self.CELL_SIZE * 3 / 4), self.width,
                                self.CELL_SIZE, int(self.CELL_SIZE/8),
                                int(self.CELL_SIZE/8))
        if self.highlight is not None:
            painter.setBrush(self.COLOR_HIGHLIGHT)
            painter.drawRect(self.CELL_SIZE * self.highlight,
                             int(self.CELL_SIZE * 3 / 4), self.CELL_SIZE,
                             self.CELL_SIZE)
        for i in range(1, self.size):
            x = i * self.CELL_SIZE
            painter.drawLine(x, int(self.CELL_SIZE * 3 / 4), x, self.height)
        painter.setPen(QPen(QColor(self.color), 1, Qt.SolidLine))
        painter.setFont(self.FONT)
        painter.drawText(QRect(0, 0, self.width, int(self.CELL_SIZE * 3 / 4
                                                     - 4)),
                         Qt.AlignCenter | Qt.AlignBottom,
                         '%s\'s Rack:' % self.name)

    def position(self, letter):
        ''' Get the position of the letter referring to the rack '''
        position = self.mapFromScene(letter.center())
        x = position.x()
        y = position.y() - self.LEGEND_SIZE
        if x < 0 or y < 0 or x > self.width or y > self.CELL_SIZE or \
           self.letters[int(x / self.CELL_SIZE)] is not None:
            return None
        else:
            return int(x / self.CELL_SIZE)

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
        letter.undo() if pos is None else letter.own(self, pos)
        self.highlight = None
        self.update(self.rect)

    def addLetter(self, letter, position, move=True):
        ''' Gets call'd to place a letter on the board '''
        assert self.letters[position] is None
        self.letters[position] = letter
        pos = QPointF(position * self.CELL_SIZE + int((self.CELL_SIZE -
                      letter.LETTER_SIZE) / 2), int(self.CELL_SIZE * 3 / 4) +
                      int((self.CELL_SIZE - letter.LETTER_SIZE) / 2))
        (letter.move if move else letter.setPos)(self.mapToScene(pos))

    def removeLetter(self, letter, position, move=True):
        ''' Gets call'd to remove a letter from the board '''
        assert self.letters[position] == letter
        self.letters[position] = None


class BoardView(QGraphicsView):
    '''
    A custom QGraphicsView class which scales the scene to always fit the
    viewport.
    '''
    letterChanged = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setRenderHint(QPainter.HighQualityAntialiasing)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        scene_max = max(self.scene().sceneRect().height(),
                        self.scene().sceneRect().width()) + 50
        widget_min = min(event.size().height(), event.size().width())
        scale = widget_min / scene_max
        self.resetTransform()
        # self.resetMatrix()
        self.scale(1, 1) if scale > 1 else self.scale(scale, scale)


class Human(Player):
    '''
    A simple Player class which is a layer between the game api and the
    user interface.
    '''
    def play(self):
        pass

    def pass_cb(self):
        ''' Pass button clicked '''
        self.skip()

    def exchange_cb(self):
        ''' Exchange button clicked '''
        self.exchange_letters(
            ''.join(l.char for l in self.game.ui.scene.items()
                    if type(l) is LetterItem and l.selected).lower())

    def continue_cb(self):
        ''' Place word button clicked '''
        word = self.game.ui.board.getNewWord()
        self.place_word(*word)
        self.game.ui.update()


class Window(QWidget):
    ''' The MainWindow widget '''
    def __init__(self, game):
        super().__init__()

        self.game = game
        self.game.ui = self

        self.setWindowTitle('Scrabble')
        self.resize(1000, 800)
        self.setStyleSheet('QGroupBox { border:0; font:bold;' +
                           'padding:20px 10px; min-width:220px; }')

        self.board = BoardItem(game.width, game.height)
        self.rack = RackItem(game.rack_size, game.width, game.height)
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QBrush(QColor('#f9ece0')))
        self.scene.addItem(self.board)
        self.scene.addItem(self.rack)
        self.scene.setSceneRect(self.scene.itemsBoundingRect())
        self.view = BoardView(self.scene, self)
        self.view.letterChanged.connect(self.letterChanged)

        self.ranking = QGroupBox('Rankings')
        self.rankings = QLabel()
        rankings = QVBoxLayout()
        rankings.addWidget(self.rankings)
        self.ranking.setLayout(rankings)

        self.statistic = QGroupBox('Statistics')
        self.statistics = QLabel()
        statistics = QVBoxLayout()
        statistics.addWidget(self.statistics)
        self.statistic.setLayout(statistics)

        self.move = QGroupBox('Last 10 Moves')
        self.moves = QLabel()
        moves = QVBoxLayout()
        moves.addWidget(self.moves)
        self.move.setLayout(moves)

        self.buttons = QVBoxLayout()
        self.buttons.setSpacing(3)
        self.continue_button = QPushButton('Place &Word')
        self.continue_button.setEnabled(False)
        self.continue_button.setFixedSize(130, 25)
        self.continue_button.clicked.connect(self.continueClicked)
        self.pass_button = QPushButton('&Pass')
        self.pass_button.setEnabled(False)
        self.pass_button.setFixedSize(130, 25)
        self.pass_button.clicked.connect(self.passClicked)
        self.exchange_button = QPushButton('&Exchange')
        self.exchange_button.setEnabled(False)
        self.exchange_button.setFixedSize(130, 25)
        self.exchange_button.clicked.connect(self.exchangeClicked)
        self.buttons.addWidget(self.exchange_button, alignment=Qt.AlignCenter)
        self.buttons.addWidget(self.pass_button, alignment=Qt.AlignCenter)
        self.buttons.addWidget(self.continue_button, alignment=Qt.AlignCenter)

        information = QVBoxLayout()
        # newly add in
        information.setContentsMargins(20, 20, 20, 20)
        # information.setMargin(20)
        information.setSpacing(20)
        information.addWidget(self.ranking)
        information.addWidget(self.statistic)
        information.addWidget(self.move)
        information.addStretch()
        information.addLayout(self.buttons)

        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)
        layout.addLayout(information)

        self.setLayout(layout)
        self.show()

        for player in self.game.players:
            player.played_cb = self.playerDone
        self.playerNext()

    def update(self, *args, **kwargs):
        self.rankings.setText(
            '<br>'.join('%i. <font color=%s>%s</font> (%i points)' %
                        (i + 1, player.color, player.name, player.score)
                        for i,player in
                        enumerate(sorted(self.game.players, reverse=True,
                                         key=attrgetter('score')))))
        self.statistics.setText(('Total Players: %i\n' +
                                 'Placed Words: %i\n' +
                                 'Remaining Letters: %i') %
                                (len(self.game.players),
                                 len(list(self.game.board.get_words())),
                                 self.game.letters.remaining_letters))
        moves = []
        for i,(player,move) in list(enumerate(self.game.moves))[-10:]:
            if move[0] == Player.PASS:
                desc = 'Pass'
            elif move[0] == Player.EXCHANGE_LETTERS:
                desc = 'Exchange (%s,%s)' % move[1:]
            else:
                desc = 'Word (%i,%i,%s,%s,%i)' % move[1:]
            moves.append('%i. <font color=%s>%s</font>' % (i + 1, player.color,
                                                           desc))
        self.moves.setText('<br>'.join(moves))

        super().update(*args, **kwargs)

    def letterChanged(self):
        ''' As soon as a letter changes we need to en/disable all controls '''
        self.exchange_button.setEnabled(False)
        self.exchange_button.setText('Exchange')
        if self.game.letters.remaining_letters >= self.game.rack_size:
            selected = ''.join(l.char for l in self.scene.items()
                               if type(l) is LetterItem and l.selected)
            if selected:
                self.exchange_button.setText('Exchange: %s' % selected)
                self.exchange_button.setEnabled(True)
        self.pass_button.setEnabled(True)
        self.continue_button.setEnabled(True if self.board.validNewWord() else
                                        False)

    def playerNext(self):
        player = self.game.next_player()

        self.letterChanged()
        self.update()
        player.update_letters()

        self.rack.name = self.game.current_player.name
        self.rack.color = self.game.current_player.color

        for i,letter in enumerate(player.letters):
            item = LetterItem(letter, self.game.letters.get_score(letter),
                              player.color)
            item.own(self.rack, i, move=False)
            self.scene.addItem(item)

        self.update()
        player.played_cb = self.playerDone
        player.play()

    def continueClicked(self):
        if self.board.validateWord():
            if type(self.game.current_player) is Human:
                self.board.currentWord = ''
                self.game.current_player.continue_cb()
        else: 
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Oops! Invalid word")
            msg.setInformativeText("Please try again")
            msg.setWindowTitle("Invalid word")
            msg.exec_()
            pass

      
    def passClicked(self):
        if type(self.game.current_player) is Human:
            self.game.current_player.pass_cb()

    def exchangeClicked(self):
        if type(self.game.current_player) is Human:
            self.game.current_player.exchange_cb()

    def playerDone(self, player, move, *args):
        self.exchange_button.setEnabled(False)
        self.exchange_button.setText('Exchange')
        self.pass_button.setEnabled(False)
        self.continue_button.setEnabled(False)

        for item in self.scene.items():
            if type(item) is LetterItem and not item.is_safe and \
               not item.deleted:
                item.own(None)
                item.fade()

        for x,y,letter in self.game.board:
            if not self.board.getLetter(x, y):
                item = LetterItem(letter.char,
                                  self.game.letters.get_score(letter),
                                  letter.player.color, safe=True)
                item.own(self.board, x, y, move=False)
                self.scene.addItem(item)

        self.update()

        if self.game.state() == self.game.RUNNING:
            self.game.current_player.update_letters()
            self.playerNext()
        else:
            self.game.finish_score()
            self.update()
            self.gameOver()
        
    def getLetters(self, count, msg=''):
        print('random letters: %s' % self.game.get_letters_old(count))
        while True:
            text,ok = QInputDialog.getText(self, 'New Letters',
                'Player: <font color=%s>%s</font><br>' % (
                self.game.current_player.color, self.game.current_player.name)
                + msg + 'Tell me %i new letters in order to continue..' % count)

            text = ''.join(filter(lambda x: x in self.game.letters.letters,
                                  text.lower()))

            if len(text) == count and all(self.game.letters.available(c) for c
                                          in text):
                return text

    def gameOver(self):
        winner = sorted(self.game.players, reverse=True,
                        key=attrgetter('score'))[0]
        self.dialog = QMessageBox(QMessageBox.Information, 'Game Over',
            ('<b>Game Over!</b><br><br>The player ' +
             '<b><font color=%s>%s</font></b> has won!') %
            (winner.color, winner.name),
            QMessageBox.Ok, self)
        self.dialog.show()
