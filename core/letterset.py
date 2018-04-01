from csv import reader
from random import seed, randrange
import os

# Absolute path of Letters CSV
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DEFAULT_LETTERSET = os.path.join(BASE_DIR, 'data', 'letters.csv')

class LetterSet:
    '''
    A class to store information about the letter chips in the game like score and count.
    '''

    def __init__(self, filename=DEFAULT_LETTERSET):
        '''
        Construct a new LetterSet while loading the initial state from a csv file specified by filename
        '''
        self.letters = {}
        self.remaining_letters = 0
        if filename is not None:
            self.load_file(filename)

    def load_file(self, filename):
        '''
        Load the letters specified in a csv file into a dictionary
        '''
        with open(filename, 'r', newline='', encoding='utf-8') as f:
            for row in reader(f):
                self.letters[row[0]] = [int(row[1]), int(row[2])]
                self.remaining_letters += int(row[2])

    def __iter__(self):
        '''
        Define LetterSet as an Iterator
        '''
        for x in sorted(self.letters.items()):
            yield x

    def get_score(self, letter):
        '''
        Get the score value to a letter
        '''
        return self.letters[str(letter)][0]

    def get_count(self, letter):
        '''
        Get the total amount of letters
        '''
        return self.letters[str(letter)][1]

    def increase_count(self, letter):
        '''
        Increase the amount of available copies for a particular Letter
        '''
        self.letters[str(letter)][1] += 1
        self.remaining_letters += 1

    def decrease_count(self, letter):
        '''
        Decrease the amount of available copies for a particular Letter
        '''
        self.letters[str(letter)][1] -= 1
        self.remaining_letters -= 1

    def is_available(self, letter):
        '''
        Check if the supplied Letter is still available
        '''
        return str(letter) in self.letters and self.get_count(letter) > 0

    def get_random_letters(self, count, msg=None):
        '''
        Retrieve count number of random letters from LetterSet
        '''
        seed()
        count = min(count, self.remaining_letters)
        random_letters = ''
        available = ''.join(k * v[1] for k, v in self.letters.items() if v[1] > 0)
        while len(random_letters) < count:
            p = randrange(0, len(available))
            random_letters = random_letters + available[p]
            available = available[:p] + available[p + 1:]
        return random_letters
