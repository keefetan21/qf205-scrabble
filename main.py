from sys import argv
from PyQt5.QtWidgets import QApplication
from core.game import Game
from ui.window_ui import WindowUI
from core.player import Player

def run():

    # Initialise Game
    game = Game(15, 15, 7)

    # Add players
    game.add_player(Player("Player 1", game))
    game.add_player(Player("Player 2", game))
    game.add_player(Player("Player 3", game))
    game.add_player(Player("Player 4", game))

    # Execute PyQt5
    app = QApplication(argv)
    win = WindowUI(game)
    app.exec_()

if __name__ == '__main__':
    run()
