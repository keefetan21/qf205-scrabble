from operator import attrgetter
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QGraphicsScene, QGroupBox, QLabel, QPushButton, \
    QMessageBox, QInputDialog
from PyQt5.QtGui import QColor, QBrush

from core.player import Player
from .board_ui import BoardUI
from .racktile_ui import RackTileUI
from .lettertile_ui import LetterTileUI
from .board_scale_ui import BoardScaleUI
from .player_ui import PlayerUI

class WindowUI(QWidget):
    ''' The MainWindow widget '''

    def __init__(self, game):
        super().__init__()

        self.game = game
        self.game.ui = self

        self.setWindowTitle('Scrabble')
        self.resize(1000, 800)
        self.setStyleSheet('QGroupBox { border:0; font:bold;' +
                           'padding:20px 10px; min-width:220px; }')

        self.board = BoardUI(game.width, game.height)
        self.rack = RackTileUI(game.rack_size, game.width, game.height)
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QBrush(QColor('#fff')))
        self.scene.addItem(self.board)
        self.scene.addItem(self.rack)
        self.scene.setSceneRect(self.scene.itemsBoundingRect())
        self.view = BoardScaleUI(self.scene, self)
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
                        for i, player in
                        enumerate(sorted(self.game.players, reverse=True,
                                         key=attrgetter('score')))))
        self.statistics.setText(('Total Players: %i\n' +
                                 'Placed Words: %i\n' +
                                 'Remaining Letters: %i') %
                                (len(self.game.players),
                                 len(list(self.game.board.get_words())),
                                 self.game.letters.remaining_letters))
        moves = []
        for i, (player, move) in list(enumerate(self.game.moves))[-10:]:
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
                               if type(l) is LetterTileUI and l.selected)
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

        for i, letter in enumerate(player.letters):
            item = LetterTileUI(letter, self.game.letters.get_score(letter),
                              player.color)
            item.own(self.rack, i, move=False)
            self.scene.addItem(item)

        self.update()
        player.played_cb = self.playerDone
        player.play()

    def continueClicked(self):
        if self.board.validateWord():
            if type(self.game.current_player) is PlayerUI:
                self.board.currentWord = ''
                try:
                    self.game.current_player.continue_cb()
                except:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Critical)
                    msg.setText("Oops! First word must be placed on the star spin in the centre of the board.")
                    msg.setInformativeText("Please try again")
                    msg.setWindowTitle("Foul play")
                    msg.exec_()
                    pass
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Oops! Invalid word")
            msg.setInformativeText("Please try again")
            msg.setWindowTitle("Invalid word")
            msg.exec_()
            pass

    def passClicked(self):
        if type(self.game.current_player) is PlayerUI:
            self.game.current_player.pass_cb()

    def exchangeClicked(self):
        if type(self.game.current_player) is PlayerUI:
            self.game.current_player.exchange_cb()

    def playerDone(self, player, move, *args):
        self.exchange_button.setEnabled(False)
        self.exchange_button.setText('Exchange')
        self.pass_button.setEnabled(False)
        self.continue_button.setEnabled(False)

        for item in self.scene.items():
            if type(item) is LetterTileUI and not item.is_safe and \
                    not item.deleted:
                item.own(None)
                item.fade()

        for x, y, letter in self.game.board:
            if not self.board.getLetter(x, y):
                item = LetterTileUI(letter.char,
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
            text, ok = QInputDialog.getText(self, 'New Letters',
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