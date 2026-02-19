from typing import Callable

from data_structures import Direction, Position


def make_word_placement_to_char_position_converter() -> Callable[[tuple[Position, Direction, str]], dict[Position, str]]:
    """Returns a closure for converting a tuple representing word positions on grids, to
    a tuple of x, y letter locations."""
    func_cache = {}
    def func_(word_placement_data:tuple[Position, Direction, str]) -> dict[Position, str]:
        """adapter which converts between forms of data representing words on a grid.
            func_cache:         enclosed dict containing hash keys refering to word_placement items
                                (see below) and conversion values

            word_placement:          tuple[(int,int), Direction, str[len=1]]
            cache:              should word_data be added to / searched for in, the cache?

        returns:                dict[ (int, int): str[len=1], ...]"""
        hcode = hash(word_placement_data)
        if hcode in func_cache:
            return func_cache[hcode]
        char_position_data = dict()
        position:Position = word_placement_data[0]
        direction = word_placement_data[1]
        word:str = word_placement_data[2]
        if isinstance(direction, Direction):
            direction_values:tuple = direction.value
        else:
            direction_values:tuple = direction
        for i, char in enumerate(word):
            loc = (position[0] + direction_values[0] * i, position[1] + direction_values[1] * i)
            char_position_data[loc] = char
        if hcode not in func_cache:
            func_cache[hcode] = char_position_data
        return char_position_data
    return func_


def char_position_to_letter_grid_converter(char_position_data:dict, width:int, height:int, placeholder:str|None = None) -> tuple:
    """Afunction for converting a tuple representing letter positions on a grid, to a
    filled 2D tuple of letters and placeholders.
        char_position_data:          tuple[ (int, int, str[len=1]), ...]
        width:                      grid width
        height:                     grid height
        placeholder:                symbol / object to use for empty positions
        cache:              should char_position_data be added to / searched for in, the cache?
    returns:                tuple[(int, int, str[len=1])]"""
    _array:list[list[str|None]] = [[placeholder for _ in range(width)] for _ in range(height)]
    for key in char_position_data:
        x, y = key
        c = char_position_data[key]
        _array[y][x] = c
    letter_grid = tuple([tuple(row) for row in _array])
    return letter_grid
