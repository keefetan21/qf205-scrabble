from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QGraphicsView
from PyQt5.QtGui import QPainter

class BoardScaleUI(QGraphicsView):
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