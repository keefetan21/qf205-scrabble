from core.player import Player
from .lettertile_ui import LetterTileUI

class PlayerUI(Player):
    '''
    A simple Player class which is a layer between the game api and the
    user interface.
    '''

    def play(self):
        pass

    def pass_cb(self):
        ''' Pass button clicked '''
        self.skip()

    def exchange_cb(self):
        ''' Exchange button clicked '''
        self.exchange_letters(
            ''.join(l.char for l in self.game.ui.scene.items()
                    if type(l) is LetterTileUI and l.selected).lower())

    def continue_cb(self):
        ''' Place word button clicked '''

        word = self.game.ui.board.getNewWord()

        if (self.game.ui.board.letters[112] == None):
            raise Exception("Please start at the center")

        self.place_word(*word)
        self.game.ui.update()