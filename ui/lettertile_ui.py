from PyQt5.QtCore import Qt, QRect, QRectF, QSizeF, QPointF, QPropertyAnimation
from PyQt5.QtWidgets import QGraphicsWidget
from PyQt5.QtGui import QColor, QPen, QFont

class LetterTileUI(QGraphicsWidget):
    '''
    A dragable objects which represents a game tile and is used as
    an intuitive way of interaction
    '''
    LETTER_SIZE = 60
    LETTER_FONT = QFont('Sans', 60/2, QFont.DemiBold)
    LETTER_PEN = QPen(QColor('#444444'), 1, Qt.SolidLine)
    SCORE_FONT = QFont('Sans', 60/4)
    SCORE_PEN = QPen(QColor('#666666'), 1, Qt.SolidLine)
    LETTER_CENTER = QPointF(25, 25)
    BOUNDING_RECT = QRectF(0, 0, 70, 70)

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

        # Import statements placed here to prevent circular dependency of imports
        from .racktile_ui import RackTileUI
        from .board_ui import BoardUI

        super().mouseMoveEvent(event)
        pos = self.scenePos() + self.LETTER_CENTER
        items = set(item for item in self.scene().items(pos)
                    if type(item) in (RackTileUI, BoardUI))
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

        # Import statements placed here to prevent circular dependency of imports
        from .racktile_ui import RackTileUI
        from .board_ui import BoardUI

        self.setZValue(1)
        super().mouseReleaseEvent(event)
        if self.last_valid_position == self.scenePos() and not self.is_safe:
            self.selected = not self.selected
            if self.scene() and self.scene().views():
                self.scene().views()[0].letterChanged.emit()
        else:
            items = self.scene().items(self.scenePos() + self.LETTER_CENTER)
            for item in items:
                if type(item) in (RackTileUI, BoardUI):
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