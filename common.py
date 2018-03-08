from abc import ABCMeta, abstractmethod
from csv import reader
from itertools import chain
from os.path import abspath, join, dirname
from random import seed, randrange


PROJECT_PATH = dirname(abspath(__file__))
DEFAULT_LETTERSET = join(PROJECT_PATH, 'data', 'letters.csv')
COLORS = ['#b94cb0', '#6d9629', '#44529b', '#b46261']


class LetterSet:
    '''
    A class to store information about the letter chips in the game like
    score and count.
    '''

    def __init__(self, filename=None):
        '''
        Construct a new LetterSet while loading the initial state from a csv
        file specified by filename
        '''
        self.letters = {}
        self.remaining_letters = 0
        if filename is not None:
            self.load_file(filename)

    def __iter__(self):
        ''' Iterate over all existing letters '''
        for x in sorted(self.letters.items()):
            yield x

    def load_file(self, filename):
        ''' Loading the letters specified in a csv file '''
        count = 0
        with open(filename, 'r', newline='', encoding='utf-8') as f:
            for row in reader(f):
                self.letters[row[0]] = [int(row[1]), int(row[2])]
                self.remaining_letters += int(row[2])
                count += 1
        return count

    def get_score(self, letter):
        ''' Get the score value to a letter '''
        return self.letters[str(letter)][0]

    def get_count(self, letter):
        ''' Get the total amount of letters '''
        return self.letters[str(letter)][1]

    def incr_count(self, letter):
        ''' Increase the amount of available copies '''
        self.letters[str(letter)][1] += 1
        self.remaining_letters += 1

    def decr_count(self, letter):
        ''' Decrease the amount of available copies '''
        assert self.letters[str(letter)][1] > 0 and self.remaining_letters > 0
        self.letters[str(letter)][1] -= 1
        self.remaining_letters -= 1

    def available(self, letter):
        ''' Checks if the supplied letter is still available '''
        return str(letter) in self.letters and self.get_count(letter) > 0
    
    def random_letters(self, count, msg=None):
        seed()
        count = min(count, self.remaining_letters)
        ret = ''
        available = ''.join(k * v[1] for k,v in self.letters.items()
                            if v[1] > 0)
        while len(ret) < count:
            p = randrange(0, len(available))
            ret = ret + available[p]
            available = available[:p] + available[p+1:]
        return ret


class Letter:
    '''
    A connection between a simple char on the board and the player who placed
    it there.
    '''
    def __init__(self, char, player, x, y):
        self.char = char
        self.player = player
        self.x = x
        self.y = y

    def __str__(self):
        return self.char


class Board:
    '''
    Store the placed letters while providing auxilary functions.
    '''
    def __init__(self, width, height):
        assert width > 0 and height > 0
        self.width = width
        self.height = height
        self.board = [None for _ in range(0, width * height)]

    def __iter__(self):
        for i,c in enumerate(self.board):
            if c is not None:
                yield (i % self.width, int(i / self.width), c)

    def add_letter(self, letter):
        ''' Add a new letter to the board '''
        pos = letter.y * self.width + letter.x
        assert letter.y >= 0 and letter.y < self.height and letter.x >= 0 \
               and letter.x < self.width and self.board[pos] is None and \
               type(letter) is Letter
        self.board[pos] = letter

    def add_word(self, x, y, direction, word, player=None):
        ''' Add a new word to the board '''
        for i,c in enumerate(word):
            xi = x + i if direction == 'right' else x
            yi = y + i if direction == 'down' else y
            if self.get_letter(xi, yi) is not None:
                continue
            self.add_letter(Letter(c, player, xi, yi))

    def get_letter(self, x, y):
        ''' Get the Letter object at the specified position or None '''
        assert x >= 0 and x <= self.width and y >= 0 and y < self.height
        return self.board[y * self.width + x]
    
    def get_rows(self):
        ''' Get each row '''
        return (self.board[y * self.width:(y + 1) * self.width]
                for y in range(0, self.height))

    def get_columns(self):
        ''' Get each column '''
        return ((self.get_letter(x, y) for y in range(0, self.height))
                for x in range(0, self.width))
    
    def get_words(self):
        ''' Returns a generator which yields all words on the board '''
        for line in chain(self.get_rows(), self.get_columns()):
            word = []
            for letter in line:
                if letter is None:
                    if len(word) > 1:
                        yield (word[0].x, word[0].y, 'right' if word[0].x !=
                               word[1].x else 'down', ''.join(l.char for l in
                               word))
                    word = []
                else:
                    word.append(letter)

            if len(word) > 1:
                yield (word[0].x, word[0].y, 'right' if word[0].x !=
                       word[1].x else 'down', ''.join(l.char for l in word))

    def get_word_score(self, letter_set, x, y, direction, word):
        letters = [(x if direction == 'down' else x + i, y if direction ==
                    'right' else y + i, word[i]) for i in range(len(word))]
        new_letters = []
        for x, y, c in letters:
            if self.get_letter(x, y) is None:
                new_letters.append((x, y, c))

        old_words = list(w for w in self.get_words())
        for x, y, c in new_letters:
            self.add_letter(Letter(c, None, x, y))
        new_words = list(w for w in self.get_words())

        really_new_words = []
        for w in new_words:
            if w not in old_words:
                really_new_words.append(w)

        for x, y, c in new_letters:
            self.board[y * self.width + x] = None

        return sum(sum(letter_set.get_score(c) for c in w[3]) for w
                   in really_new_words)


class Game:
    '''
    A basic Game model which holds all information about a game and runs it
    by the implemented scrabble logic.
    '''
    RUNNING = 'running'
    GAME_OVER = 'gameover'

    def __init__(self, width, height, rack_size, letters=DEFAULT_LETTERSET):
        ''' Construct a new Game object '''
        self.width = width
        self.height = height
        self.rack_size = rack_size
        self.board = Board(width, height)
        self.letters = LetterSet(letters)
        self.players = []
        self.current_player = None
        self.moves = []
        self.get_letters = self.letters.random_letters
        self.lap = 0
        self.turn = 0
        self.empty = True

    def state(self):
        ''' The state of the game '''
        last_moves = self.moves[-4:]
        if (len(last_moves) == 4 and all(m[0] != Player.PLACE_WORD for p,m
                                         in last_moves)) or \
           (self.letters.remaining_letters == 0 and any(not p.letters for p
                                                        in self.players)):
            return self.GAME_OVER
        return self.RUNNING

    def add_player(self, player):
        '''Add a new player to the list of players'''
        self.players.append(player)



    def next_player(self):
        ''' Set and return the next player '''
        assert self.state() == self.RUNNING
        self.turn += 1
        self.lap = int((self.turn - 1) / len(self.players)) + 1
        self.current_player = self.players[(self.turn - 1) % len(self.players)]
        return self.current_player

    def check_move(self, x, y, direction, word):
        return True

    def add_word(self, player, x, y, direction, word):
        letters = [(x if direction == 'down' else x + i, y if direction ==
                    'right' else y + i, word[i]) for i in range(len(word))]

        player.score += self.board.get_word_score(self.letters, x, y,
                                                  direction, word)

        for x, y, c in letters:
            if self.board.get_letter(x, y) is None:
                self.board.add_letter(Letter(c, player, x, y))
                pos = player.letters.index(c)
                player.letters = player.letters[:pos] + player.letters[pos+1:]

    def finish_score(self):
        assert self.state() == self.GAME_OVER
        if self.moves[-1][1][0] == Player.PLACE_WORD:
            winner = self.moves[-1][0]
            for player in self.players:
                if player != winner:
                    score = sum(self.letters.get_score(c) for c in
                                player.letters)
                    player.score -= score
                    winner.score += score
        else:
            for player in self.players:
                score = sum(self.letters.get_score(c) for c in player.letters)
                player.score -= score



class Player(metaclass=ABCMeta):
    '''
    A meta class which defines the interface for Players. Each possible player
    like a Human or a Bot should implement/inherit this class.
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

    @abstractmethod
    def play(self):
        '''
        Time for the player to generate a move. Should react using the methods
        pass(), exchange_letters() or place_word().
        '''
        pass
    
    def skip(self):
        ''' A pass-move to get called in play() '''
        self.played(self.PASS,)

    def exchange_letters(self, letters):
        ''' A exchange-letters-move to get called in play() '''
        if self.game.rack_size > self.game.letters.remaining_letters:
            return self.played(self.EXCHANGE_LETTERS, '', '')
        new_letters = self.game.get_letters(len(letters), msg=
            'Exchanging letters %s<br>' % letters.upper())
        for c in letters:
            pos = self.letters.find(c)
            self.letters = self.letters[:pos] + self.letters[pos+1:]
            self.game.letters.incr_count(c)
        for c in new_letters:
            self.game.letters.decr_count(c)
        self.letters += new_letters
        self.played(self.EXCHANGE_LETTERS, letters, new_letters)

    def place_word(self, x, y, direction, word):
        ''' A place-word-move to get called in play() '''
        score = self.game.board.get_word_score(self.game.letters, x, y,
                                               direction, word)
        self.game.add_word(self, x, y, direction, word)
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
                self.game.letters.decr_count(c)


# vim: set expandtab shiftwidth=4 softtabstop=4 textwidth=79:
