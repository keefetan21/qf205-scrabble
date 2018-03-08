from sys import argv

from PyQt5.QtWidgets import QApplication

from common import Game, DEFAULT_LETTERSET
from scrabble_ui import Window, Human


def run():

    game = Game(11, 11, 7, DEFAULT_LETTERSET)

    game.add_player(Human("Player1", game))
    game.add_player(Human("Player2", game))

    app = QApplication(argv)
    win = Window(game)
    app.exec_()
    # app.exec_()

if __name__ == '__main__':
    run()
