class Letter:
    '''
    A Letter class representing a letter on the scrabble board
    '''
    def __init__(self, char, player, x, y):
        self.char = char
        self.player = player
        self.x = x
        self.y = y

    def __str__(self):
        return self.char
