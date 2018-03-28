from sys import argv
from PyQt5.QtWidgets import QApplication
from core.game import Game
from scrabble_ui import Window, Human

def run():

    game = Game(15, 15, 7)

    game.add_player(Human("Player1", game))
    game.add_player(Human("Player2", game))
    game.add_player(Human("Player3", game))
    game.add_player(Human("Player4", game))

    app = QApplication(argv)
    win = Window(game)
    app.exec_()

if __name__ == '__main__':
    run()
