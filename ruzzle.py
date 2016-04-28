"""This is a bit of experimental code to model Ruzzle.

   Ruzzle is a video game developed by MAG Interactive for iOS, Android and 
   Windows Phone 8 devices. The application was published on Apple Store in
   March 2012.

   The game mechanism is inspired by the board games Boggle and Scrabble.
"""

import codecs
import logging
import string
import os

import datrie

from vars import CHAR_POINTS, CHAR_COLOURS


class Vocabulary(object):
    """It contains the recognised words in the game."""

    def __init__(self, language='english'):
        """A vocabulary is a collection of words in a specific language."""
        self.data_folder = 'data'
        self.language = language.lower()
        self.words = datrie.Trie(string.ascii_lowercase)
        try:
            self._unpickle()
        except IOError:
            self._load_from_file()
            self._pickle()

    def _load_from_file(self):
        """Load the vocabulary by reading a text file."""
        from unidecode import unidecode
        path = os.path.join(('vocabularies'), self.language)
        try:
            with codecs.open(path, 'r', encoding='utf-8') as lines:
                for word in lines:
                    word = unicode(unidecode(word.strip()))
                    self.words[word] = True
        except IOError:
            logging.error('Vocabulary not found at {}'.format(path))
        logging.info('Vocabulary loaded from text.')

    def _unpickle(self):
        """Load the trie from disk."""
        path = os.path.join(self.data_folder, self.language)
        self.words = datrie.Trie.load(path)
        logging.info('Vocabulary unpickled.')

    def _pickle(self):
        """Dump the trie on disk."""
        path = os.path.join(self.data_folder, self.language)
        self.words.save(path)
        logging.info('Vocabulary saved.')

    def __contains__(self, item):
        """Check whether a word is in the vocabulary."""
        return item in self.words


class Tile(object):
    def __init__(self, char, colour='', position=None):
        assert char.lower() in CHAR_POINTS.keys(), 'Invalid character'
        assert colour in CHAR_COLOURS, 'Invalid tile colour'
        self.char = char.lower()
        self._char_score = CHAR_POINTS[self.char]
        self.colour = colour
        self.position = position

    @property
    def points(self):
        """Return the points of the tile, by taking into account bonuses."""
        if self.colour == 'G':
            return self._char_score * 2
        if self.colour == 'B':
            return self._char_score * 3
        return self._char_score

    @property
    def is_double_word(self):
        """Return whether the tile has Double Word bonus."""
        return self.colour == 'Y'

    @property
    def is_triple_word(self):
        """Return whether the tile has Triple Word bonus."""
        return self.colour == 'R'

    def neighbours(self):
        neighbours = set()
        if self.position[0] >= 1:
            neighbours.add((self.position[0]-1, self.position[1]))
        if self.position[0] <= 2:
            neighbours.add((self.position[0]+1, self.position[1]))
        if self.position[1] >= 1:
            neighbours.add((self.position[0], self.position[1]-1))
        if self.position[1] <= 2:
            neighbours.add((self.position[0], self.position[1]+1))
        if self.position[0] >= 1 and self.position[1] >= 1:
            neighbours.add((self.position[0]-1, self.position[1]-1))
        if self.position[0] >= 1 and self.position[1] <= 2:
            neighbours.add((self.position[0]-1, self.position[1]+1))
        if self.position[0] <= 2 and self.position[1] >= 1:
            neighbours.add((self.position[0]+1, self.position[1]-1))
        if self.position[0] <= 2 and self.position[1] <= 2:
            neighbours.add((self.position[0]+1, self.position[1]+1))
        return neighbours

    def __repr__(self):
        return self.char


class Board(object):
    """It represents the Ruzzle board."""

    def __init__(self, tiles, vocabulary, grid_size=4):
        """Builds a board with 16 tiles and a specific vocabulary.

        Args:
            tiles (list): flat 16-tile long
            vocabulary (Vocabulary): vocabulary
        """
        self.GRID_SIZE = grid_size
        self.grid = {}
        self.vocabulary = vocabulary
        for pos, tile in enumerate(tiles):
            row, col = pos / self.GRID_SIZE, pos % self.GRID_SIZE
            tile.position = (row, col)
            self.grid[row, col] = tile

    def tile(self, position):
        """Return the tile object at the specified position."""
        assert position[0] < self.GRID_SIZE
        assert position[1] < self.GRID_SIZE
        return self.grid[position]

    def points(self, path):
        """Compute the total points obtained by following the letter path.

        Args:
            path (list): grid coordinates [(x,y) ... (x,y)]

        Returns:

        """
        total = sum([self.tile(pos).points for pos in path])
        n_double_w = len(['' for pos in path if self.tile(pos).is_double_word])
        n_triple_w = len(['' for pos in path if self.tile(pos).is_triple_word])
        return total * (2**n_double_w) * (3**n_triple_w)

    def possible_words(self):
        """Returns the list of all the words which can be made using the
           current board.
        """
        words = dict()
        for row in xrange(self.GRID_SIZE):
            for col in xrange(self.GRID_SIZE):
                for wrd_path in self._explore(self.tile((row, col)), []):
                    wrd_form = self.path2word(wrd_path)
                    wrd_points = self.points(wrd_path)
                    words[wrd_form] = (wrd_path, wrd_points)
        words = words.items()
        words.sort(key=lambda x: x[1][1], reverse=True)
        return words

    def _explore(self, tile, path):
        path = list(path)
        path.append(tile.position)
        word_form = self.path2word(path)
        explorable_neighbours = tile.neighbours() - set(path)
        for pos in explorable_neighbours:
            if self.vocabulary.words.keys(word_form):
                for wrd_path in self._explore(self.tile(pos), path):
                    yield wrd_path
        if word_form in self.vocabulary.words:
            yield path

    def path2word(self, path):
        return u''.join([self.tile(pos).char for pos in path])


def main():
    """Example code."""
    test_voc = Vocabulary('italian')
    tiles = [Tile(c) for c in 'BAASSTRGAALANODI']
    tiles[3].colour = 'Y'
    tiles[4].colour = 'G'
    tiles[8].colour = 'R'
    tiles[9].colour = 'B'
    tiles[13].colour = 'B'
    tiles[14].colour = 'Y'
    board = Board(tiles, test_voc)
    dic = board.possible_words()
    for key, (path, points) in dic:
        print '{:>5} {:<16} {}'.format(points, key.upper(), path)


if __name__ == '__main__':
    main()
