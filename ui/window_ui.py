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

class WindowUI(QWidget):
    '''
    The Main Window
    '''

    def __init__(self, game):
        super().__init__()

        self.game = game
        self.game.ui = self

        # Set window title
        self.setWindowTitle('Scrabble')

        # Set window size
        self.resize(1000, 800)

        # Set background color, size, padding, font for the side bar
        self.setStyleSheet('QGroupBox { background-color: #fff; border:0; font:bold;' +
                           'padding:20px 20px; min-width:250px; }' 
                            + 'QGroupBox::title{ font-size: 100px; }')
        
        self.board = BoardUI(game.width, game.height)
        self.rack = RackTileUI(game.rack_size, game.width, game.height)
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QBrush(QColor('#fff')))
        self.scene.addItem(self.board)
        self.scene.addItem(self.rack)
        self.scene.setSceneRect(self.scene.itemsBoundingRect())
        self.view = BoardScaleUI(self.scene, self)
        self.view.letterChanged.connect(self.letterChanged)
        
        # Create a box called Ranking
        self.ranking = QGroupBox('Rankings')
        self.rankings = QLabel()
        rankings = QVBoxLayout()
        rankings.addWidget(self.rankings)
        self.ranking.setLayout(rankings)
        
        # Create a box called Statistics
        self.statistic = QGroupBox('Statistics')
        self.statistics = QLabel()
        statistics = QVBoxLayout()
        statistics.addWidget(self.statistics)
        self.statistic.setLayout(statistics)
        
        # Create a box called Last 10 Moves
        self.move = QGroupBox('Last 10 Moves')
        self.moves = QLabel()
        moves = QVBoxLayout()
        moves.addWidget(self.moves)
        self.move.setLayout(moves)
        
        # Create buttons and set the specification for the buttons
        self.buttons = QVBoxLayout()
        self.buttons.setSpacing(3)
        self.place_word_button = QPushButton('Place &Word')
        self.place_word_button.setEnabled(False)
        self.place_word_button.setFixedSize(200, 50)
        self.place_word_button.clicked.connect(self.continueClicked)
        self.pass_button = QPushButton('&Pass')
        self.pass_button.setEnabled(False)
        self.pass_button.setFixedSize(200, 50)
        self.pass_button.clicked.connect(self.passClicked)
        self.exchange_button = QPushButton('&Exchange')
        self.exchange_button.setEnabled(False)
        self.exchange_button.setFixedSize(200, 50)
        self.exchange_button.clicked.connect(self.exchangeClicked)
        self.end_game_button = QPushButton('&End Game')
        self.end_game_button.setEnabled(True)
        self.end_game_button.setFixedSize(200, 50)
        self.end_game_button.clicked.connect(self.endGameClicked)
        self.buttons.addWidget(self.end_game_button, alignment=Qt.AlignCenter)
        self.buttons.addWidget(self.exchange_button, alignment=Qt.AlignCenter)
        self.buttons.addWidget(self.pass_button, alignment=Qt.AlignCenter)
        self.buttons.addWidget(self.place_word_button, alignment=Qt.AlignCenter)

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
        '''
        Whenever player clicks a button, this method will update the UI
        '''
        self.rankings.setText(
            '<br>'.join('<font size=8>%i.</font> <font size=8 color=%s>%s</font> <font size=8>(%i points)</font>' %
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
        '''
        As soon as a letter changes we need to enable/disable all controls
        '''
        self.exchange_button.setEnabled(False)
        self.exchange_button.setText('Exchange')
        if self.game.letters.remaining_letters >= self.game.rack_size:
            selected = ''.join(l.char for l in self.scene.items()
                               if type(l) is LetterTileUI and l.selected)
            if selected:
                self.exchange_button.setText('Exchange: %s' % selected)
                self.exchange_button.setEnabled(True)
        self.pass_button.setEnabled(True)
        self.place_word_button.setEnabled(True if self.board.validNewWord() else
                                        False)

    def playerNext(self):
        '''
        Get next player and modify UI to display correct player information
        '''
        self.game.set_next_player()
        player = self.game.get_next_player()

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

    def playerDone(self, player, move, *args):
        '''
        Complete player's turn
        '''
        self.exchange_button.setEnabled(False)
        self.exchange_button.setText('Exchange')
        self.pass_button.setEnabled(False)
        self.place_word_button.setEnabled(False)

        for item in self.scene.items():
            if type(item) is LetterTileUI and not item.is_safe and not item.deleted:
                item.own(None)
                item.fade()

        for x, y, letter in self.game.board:
            if not self.board.getLetter(x, y):
                item = LetterTileUI(letter.char, self.game.letters.get_score(letter), letter.player.color, safe=True)
                item.own(self.board, x, y, move=False)
                self.scene.addItem(item)

        self.update()

        if self.game.get_state() == self.game.RUNNING:
            self.game.current_player.update_letters()
            self.playerNext()
        else:
            self.update()
            self.gameOver()

    def continueClicked(self):
        '''
        Function that gets called when 'Place Word' is clicked
        Validates word and calculates player's score
        Also checks that the first word placed on the board has to be in the center tile
        '''
        if self.board.validateWord():
            if type(self.game.current_player) is Player:
                self.board.currentWord = ''
                try:
                    self.game.current_player.place_word()
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
        '''
        Function that gets called when 'Pass' is clicked
        '''
        if type(self.game.current_player) is Player:
            self.game.current_player.pass_turn()

    def endGameClicked(self):
        '''
        Function that gets called when 'End Game' is clicked
        '''
        if type(self.game.current_player) is Player:
            self.update()
            self.gameOver()

    def exchangeClicked(self):
        '''
        Function that gets called when 'Exchange' is clicked
        '''
        if type(self.game.current_player) is Player:
            self.game.current_player.exchange_letters()

    def gameOver(self):
        '''
        Function that determines the winner and ends the game
        '''
        winner = sorted(self.game.players, reverse=True, key=attrgetter('score'))[0]
        self.dialog = QMessageBox(QMessageBox.Information, 'Game Over',
                                  ('<b>Game Over!</b><br><br>The player ' +
                                   '<b><font color=%s>%s</font></b> has won!') %
                                  (winner.color, winner.name),
                                  QMessageBox.Ok, self)
        result = self.dialog.exec_()
        if (result == QMessageBox.Ok or result == QMessageBox.Close):
            exit()

    # DEPRECATE
    # def getLetters(self, count, msg=''):
    #     print('random letters: %s' % self.game.get_letters_old(count))
    #     while True:
    #         text, ok = QInputDialog.getText(self, 'New Letters',
    #                                         'Player: <font color=%s>%s</font><br>' % (
    #                                             self.game.current_player.color, self.game.current_player.name)
    #                                         + msg + 'Tell me %i new letters in order to continue..' % count)
    #
    #         text = ''.join(filter(lambda x: x in self.game.letters.letters,
    #                               text.lower()))
    #
    #         if len(text) == count and all(self.game.letters.is_available(c) for c
    #                                       in text):
    #             return text