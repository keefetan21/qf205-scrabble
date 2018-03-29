from sys import argv
from PyQt5.QtWidgets import QApplication
from core.game import Game
from ui.window_ui import WindowUI
from ui.player_ui import PlayerUI

def run():

    # Initialise Game
    game = Game(15, 15, 7)

    # Add players
    game.add_player(PlayerUI("Player 1", game))
    game.add_player(PlayerUI("Player 2", game))
    game.add_player(PlayerUI("Player 3", game))
    game.add_player(PlayerUI("Player 4", game))

    # Execute PyQt5
    app = QApplication(argv)
    win = WindowUI(game)
    app.exec_()

if __name__ == '__main__':
    run()
