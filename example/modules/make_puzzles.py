"""For making word search puzzles."""
import argparse
from decimal import Decimal, getcontext
from functools import partial
from random import choice, seed
from string import ascii_lowercase
from time import time
from typing import Any, Callable, Generator

import data_converters
from data_structures import Direction, LinkedListItemSingleLink, Position

getcontext().prec = 32
DECIMAL_ADJUSTMENT_FACTOR = Decimal(0.008)

END_NODE = "END"


reseed = lambda _=0: seed(time())


def make_validator_check_overlapping_words(data_converter:Callable[[tuple[Position, Direction, str]], dict[Position, str]]):
    def validator_func(candidate:tuple[Position, Direction, str], existing_letters:dict[Position, str]) -> bool:
        """Validation function to compare data representing letters placed on a grid. Returns True if
        there are no letter placements overlapping, or all overlapping placements have the same letters at shared grid locations."""
        new_letters:dict = data_converter(candidate)
        overlaps = [p for p in existing_letters.keys() if p in new_letters.keys()]
        for position in overlaps:
            if new_letters[position] != existing_letters[position]:
                return False
        return True
    return validator_func


def make_candidates_generator_factory(directions:tuple[Direction, ...], width:int, height:int):
    def word_candidates_gen(word:str) -> Generator[list[tuple], Any, None]:
        """Generator function to create valid placements and directions of a given word in a hypothetical grid.
        Returns:    list[
                            (x,y)       coordinates
                            [d, ...]    immutable sequence of directions
        ]"""
        word_len = len(word)
        reseed()
        items:list =[((x,y), tuple([d for d in directions if 0 <= x + d.value[0] * (word_len - 1) < width and 0 <= y + d.value[1] * (word_len - 1) < height]),) for y in range(height) for x in range(width)]
        while items:
            i = choice(items)
            items.remove(i)
            yield i
    return word_candidates_gen


def find_word_candidates(new_word:str, existing_letters_data:dict, validators:tuple[Callable], generator_factory:Callable[[str], Generator[list[tuple], Any, None]], limit=-1) -> list|set:
    """High level function to find correct placements of a given word in a hypothetical grid, given
    data on existing placements, and means to create candidate placements and validate said candidates.

    new_word:               the new word to place.
    existing_letters:       dictionary of placement locations for the letters of placed words, in {(int, int): str} format.
    valid_directions:       immutable array of all allowed Direction when finding possible placements.
    validators:             immutable array of validator functions, to check if a possible placement is allowed.
    data_converter:         helper function to convert from ((int, int), Direction, str) format to {(int, int): str}.
    placement_generator:    Function, that returns a generator object that creates the initial possible placements.
    width:                  positive integer, width of hypothetical grid.
    height:                 positive integer, height of hypothetical grid.
    """

    generator = generator_factory(new_word)
    candidates = []
    count = 0
    for item in generator:
        if count == limit:
            break
        position:Position = item[0]
        directions:list[Direction] = list(item[1])
        for validator in validators:
            for j in range(len(directions)-1, -1, -1):
                d:Direction = directions[j]
                candidate = (position, d, new_word)
                if not validator(candidate, existing_letters_data):
                    del directions[j]
        for d in directions:
            candidates.append((position, d, new_word,))
            count += 1
            if count == limit:
                break
    return candidates


def random_fill_puzzle_grid(grid:tuple, placeholder = str) -> tuple:
    """Replaces empty grid places with random letters."""
    tmp_ = [[char for char in row] for row in grid]
    for j in range(len(tmp_)):
        row = tmp_[j]
        for i in range(len(row)):
            if row[i] == placeholder:
                row[i] = choice(ascii_lowercase)
    grid = tuple([tuple(row) for row in tmp_])
    return grid


def send_puzzles_to_callback(start_nodes:list[LinkedListItemSingleLink]|set[LinkedListItemSingleLink], writer_func:Callable, grid_width:int, grid_height:int, placeholder) -> None:
    """Given a set of starting nodes for puzzle combinations, generate each puzzle then send it to
    a file writer callback.
    start_nodes:            collection of LinkedList nodes to start from.
    writer_func:            file writer callback function.
    adapter_func:           function to convert from LinkedList data to data used by puzzle Grid.
    grid_width:             width of puzzle grid, in letters.
    grid_height:            height of puzzle grid, in letters.
    placeholder:            placeholder character used by incomplete grids."""

    for node in start_nodes:
        char_positions = dict(node.data)
        prev_link = node.link
        while prev_link is not None and prev_link.data != END_NODE:
            char_positions.update(prev_link.data)
            prev_link = prev_link.link
        grid:tuple = data_converters.char_position_to_letter_grid_converter(char_positions, grid_width, grid_height, placeholder)
        grid = random_fill_puzzle_grid(grid, placeholder=placeholder)
        str_rows = tuple(["".join(row) for row in grid])
        writer_func(str_rows)


def recurse_update_linked_list(prev_item:LinkedListItemSingleLink, next_word_ndx:int, wordlist:list[str], candidates_func:Callable, converter_func:Callable, directions:tuple[Direction, ...], end_state_callback_func:Callable) -> None:
    """Recursively build out the linked list tree for puzzle combinations. When a full combination is identified,
    pass it to a callback function for further processing.
    prev_item:              previous node to update from
    next_word_ndx:          index number for next word to use, from the wordlist
    wordlist:               list of word strings
    candidates_func:        function which finds list of candidate positions and directions of a given word
    directions:             list of all valid directions a word can have
    end_state_callback:     function to call, upon leaf nodes, when leaf nodes are identified"""
    item_limit = Decimal(1)

    next_word = wordlist[next_word_ndx]
    prev_words_data = {}
    if prev_item.data != END_NODE:
        prev_words_data.update(prev_item.data)
    prev_link = prev_item.link
    while prev_link is not None and prev_link.data != END_NODE:
        prev_words_data.update(prev_link.data)
        prev_link = prev_link.link
    candidates:list = candidates_func(next_word, prev_words_data, limit=int(item_limit))

    # if there are no suitable candidates, abandon this combination
    if not len(candidates):
        return
    new_item_count = len(candidates)

    new_items = [LinkedListItemSingleLink(converter_func(c), prev_item) for c in candidates]
    differential = 0

    if item_limit == -1:
        differential = -1
        next_limit = int(differential)
    elif item_limit >= new_item_count:
        differential = (Decimal(item_limit) + DECIMAL_ADJUSTMENT_FACTOR) / Decimal(new_item_count)
        next_limit = int(differential)
    else:
        next_limit = 1
    differential, next_limit = Decimal(differential), Decimal(next_limit)

    if next_word_ndx + 1 >= len(wordlist):
        end_state_callback_func(new_items)
        for item in new_items:
            item.link = None
        prev_item.link = None
    else:
        new_word_ndx = next_word_ndx + 1
        if not differential:
            for next_item in new_items:
                recurse_update_linked_list(next_item, new_word_ndx, wordlist, candidates_func, converter_func, directions, end_state_callback_func)
        else:
            for next_item in new_items:
                recurse_update_linked_list(next_item, new_word_ndx, wordlist, candidates_func, converter_func, directions, end_state_callback_func)


def make_puzzles(args:argparse.Namespace, wordlist:list[str], new_puzzle_callback:Callable) -> None:
    """Main function.
    args:                   command line arguments object.
    new_puzzle_callback:    callback function for when new puzzles are found."""
    wlist = sorted(wordlist, key=lambda x: len(x), reverse=True)
    greatest_length = len(wlist[0])

    if args.width is None:
        WORD_SEARCH_WIDTH = greatest_length
    elif args.width < greatest_length:
        WORD_SEARCH_WIDTH = greatest_length
    else:
        WORD_SEARCH_WIDTH = args.width

    if args.height is None:
        WORD_SEARCH_HEIGHT = greatest_length
    elif args.height < greatest_length:
        WORD_SEARCH_HEIGHT = greatest_length
    else:
        WORD_SEARCH_HEIGHT = args.height

    converter_ = data_converters.make_word_placement_to_char_position_converter()
    validator_non_overlapping = make_validator_check_overlapping_words(converter_)
    generator_factory_ = make_candidates_generator_factory(directions=tuple([d for d in Direction]), width=WORD_SEARCH_WIDTH, height=WORD_SEARCH_HEIGHT)
    get_word_candidates = partial(find_word_candidates, validators=(validator_non_overlapping,), generator_factory=generator_factory_)
    puzzle_writer_ = partial(send_puzzles_to_callback, writer_func=new_puzzle_callback, grid_width=WORD_SEARCH_WIDTH, grid_height=WORD_SEARCH_HEIGHT, placeholder=args.placeholder)
    recurse_create_puzzles = partial(recurse_update_linked_list, candidates_func=get_word_candidates, converter_func=converter_, directions=tuple([d for d in Direction]), end_state_callback_func=puzzle_writer_)

    ending_node = LinkedListItemSingleLink(END_NODE, None)
    start_word_ndx = 0

    recurse_create_puzzles(ending_node, start_word_ndx, wlist)
