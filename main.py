from sys import argv
from PyQt5.QtWidgets import QApplication
from core.game import Game
from ui.window_ui import WindowUI
from ui.player_ui import PlayerUI
def run():

    game = Game(15, 15, 7)

    game.add_player(PlayerUI("Player1", game))
    game.add_player(PlayerUI("Player2", game))
    game.add_player(PlayerUI("Player3", game))
    game.add_player(PlayerUI("Player4", game))

    app = QApplication(argv)
    win = WindowUI(game)
    app.exec_()

if __name__ == '__main__':
    run()
