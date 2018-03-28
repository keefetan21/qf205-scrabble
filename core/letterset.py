from csv import reader
from random import seed, randrange
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DEFAULT_LETTERSET = os.path.join(BASE_DIR, 'data', 'letters.csv')

class LetterSet:
    '''
    A class to store information about the letter chips in the game like
    score and count.
    '''

    def __init__(self, filename=DEFAULT_LETTERSET):
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
        available = ''.join(k * v[1] for k, v in self.letters.items()
                            if v[1] > 0)
        while len(ret) < count:
            p = randrange(0, len(available))
            ret = ret + available[p]
            available = available[:p] + available[p + 1:]
        return ret