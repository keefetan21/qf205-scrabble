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