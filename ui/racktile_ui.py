from PyQt5.QtCore import Qt, QRect, QRectF, QPointF
from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtGui import QColor, QPen, QFont

from .lettertile_ui import LetterTileUI

class RackTileUI(QGraphicsItem):
    '''
    A graphical representation of a scrabble rack. It also keeps track of
    all LetterItems 'placed' on it.
    '''
    CELL_SIZE = LetterTileUI.LETTER_SIZE + 10
    CELL_PEN = QPen(QColor(204,204,204), 1, Qt.SolidLine)
    CELL_BRUSH = QColor(245,245,245)
    LEGEND_SIZE = int((LetterTileUI.LETTER_SIZE + 10) * 3 / 4)
    FONT = QFont('Sans', int(LetterTileUI.LETTER_SIZE/4))
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