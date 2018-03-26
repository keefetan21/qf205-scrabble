from sys import argv

from PyQt5.QtWidgets import QApplication

from common import Game, DEFAULT_LETTERSET
from scrabble_ui import Window, Human

import pandas as pd
import numpy as np

'''
Logic behind scoring
1. Check if all all adjacent words are valid
2. Confim with users that he/she wants to put the word in this location
3. Calculate double/triple letters
4. Calculate double/triple scores

'''

#load board multiplier from CSV file
df = pd.read_csv("data/board_multiplier.csv", header=None)

# print(df)
# print(board)






def run():

    game = Game(15, 15, 7, DEFAULT_LETTERSET)

    game.add_player(Human("Player1", game))
    game.add_player(Human("Player2", game))
    game.add_player(Human("Player3", game))
    game.add_player(Human("Player4", game))

    app = QApplication(argv)
    win = Window(game)
    app.exec_()
    # app.exec_()

if __name__ == '__main__':
    run()
