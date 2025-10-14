from typing import Callable

from data_structures import Directions


def make_word_placement_to_char_position_converter() -> Callable:
    """Returns a closure for converting a tuple representing word positions on grids, to
    a tuple of x, y letter locations."""
    func_cache = {}
    def func_(word_placement_data:tuple, cache=True) -> tuple:
        """adapter which converts between forms of data representing words on a grid.
            func_cache:         enclosed dict containing hash keys refering to word_placement items
                                (see below) and conversion values

            word_placement:          tuple[ ( (int,int), Direction, str), ...]
            cache:              should word_data be added to / searched for in, the cache?

        returns:                tuple[ (int, int, str[len=1]), ...]"""
        hcode = hash(word_placement_data)
        if cache and hcode in func_cache:
            return func_cache[hcode]
        char_position_data = set()
        for entry in word_placement_data:
            position, direction, word = entry
            if isinstance(direction, Directions):
                direction = direction.value
            for i, char in enumerate(word):
                item = (position[0] + direction[0] * i, position[1] + direction[1] * i, char)
                char_position_data.add(item)
        char_position_data = tuple(sorted(char_position_data))
        if cache:
            func_cache[hcode] = char_position_data
        return char_position_data
    return func_


def char_position_to_letter_grid_converter(char_position_data:tuple, width:int, height:int, placeholder:str|None = None) -> tuple:
    """Afunction for converting a tuple representing letter positions on a grid, to a
    filled 2D tuple of letters and placeholders.
        char_position_data:          tuple[ (int, int, str[len=1]), ...]
        width:                      grid width
        height:                     grid height
        placeholder:                symbol / object to use for empty positions
        cache:              should char_position_data be added to / searched for in, the cache?
    returns:                tuple[(int, int, str[len=1])]"""
    _array:list[list[str|None]] = [[placeholder for _ in range(width)] for _ in range(height)]
    for entry in char_position_data:
        x, y, char = entry
        _array[y][x] = char
    letter_grid = tuple([tuple(row) for row in _array])
    return letter_grid
