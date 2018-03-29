from ui.lettertile_ui import LetterTileUI

# Color hex code for each player
COLORS = ['#b94cb0', '#6d9629', '#44529b', '#b46261']

class Player():
    '''
    A meta class which defines the interface for Players
    '''
    PASS = 'pass'
    PLACE_WORD = 'place'
    EXCHANGE_LETTERS = 'exchange'

    def __init__(self, name, game, color=None):
        ''' Construct a new Player object '''
        self.name = name
        self.color = COLORS.pop() if color is None else color
        self.score = 0
        self.letters = ''
        self.moves = []
        self.game = game
        self.played_cb = None

    def play(self):
        '''
        Time for the player to generate a move. Should react using the methods
        pass(), exchange_letters() or place_word().
        '''
        pass

    def skip(self):
        ''' A pass-move to get called in play() '''
        self.played(self.PASS, )

    def exchange_letters(self, letters):
        ''' A exchange-letters-move to get called in play() '''
        if self.game.rack_size > self.game.letters.remaining_letters:
            return self.played(self.EXCHANGE_LETTERS, '', '')
        new_letters = self.game.get_letters(len(letters), msg=
        'Exchanging letters %s<br>' % letters.upper())
        for c in letters:
            pos = self.letters.find(c)
            self.letters = self.letters[:pos] + self.letters[pos + 1:]
            self.game.letters.increase_count(c)
        for c in new_letters:
            self.game.letters.decrease_count(c)
        self.letters += new_letters
        self.played(self.EXCHANGE_LETTERS, letters, new_letters)

    def place_word(self, x, y, direction, word):
        ''' A place-word-move to get called in play() '''
        score = self.game.board.get_word_score(self.game.letters, x, y,
                                               direction, word)
        self.game.add_word_by_current_player(self, x, y, direction, word)
        self.played(self.PLACE_WORD, x, y, direction, word, score)

    def played(self, *move):
        ''' Add the move to a list and call the played_cb '''
        self.game.moves.append((self, move))
        if self.played_cb:
            self.played_cb(self, *move)

    def update_letters(self):
        ''' Updates the players letters if neccessary and possible '''
        if len(self.letters) < self.game.rack_size and \
                self.game.letters.remaining_letters > 0:
            count = min(self.game.rack_size - len(self.letters),
                        self.game.letters.remaining_letters)
            new_letters = self.game.get_letters(count)
            self.letters += new_letters
            for c in new_letters:
                self.game.letters.decrease_count(c)

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
            raise Exception()

        self.place_word(*word)
        self.game.ui.update()