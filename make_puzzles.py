"""make_puzzles script
For making word search puzzles."""
import argparse
import sys
from decimal import Decimal, getcontext
from functools import partial
from os import path
from random import choice
from string import ascii_lowercase
from time import time
from typing import Any, Callable, Generator

import data_converters
from data_structures import Directions, LinkedListItemSingleLink
from process_managers import WriterProcessManager

getcontext().prec = 32
DECIMAL_ADJUSTMENT_FACTOR = Decimal(0.008)

# GLOB_PUZZLE_COUNT = 0

END_NODE = "END"
LOGGING_FILE = f"word_search_generation.{time()}.log"
DEFAULT_OUTPUT_FILE = f"puzzle_output.{time()}.txt"

NODE_COUNT = 0
LL_MEMORY_SIZE = 0
DEBUG = False

### TODO: figure out why -p sometimes creates less puzzles than expected. Could be floating point precision issue?

def get_wordlist(fname:str) -> list[str]:
    """Given a filename of a text file and assuming it contains a newline separated list of words,
    return the text contents as a list."""
    with open(fname) as fp:
        wordlist = [w.strip() for w in fp.readlines()]
    if wordlist[-1] == '':
        del wordlist[-1]
    return wordlist


def validator_non_overlapping(candidate_word_data, used_words_data, converter:Callable) -> bool:
    """Validation function to compare data representing words placed on a grid. Returns True if
    no words are overlapping or all overlapping words have the same letters at shared grid locations."""
    used_words_data = converter(used_words_data)
    candidate_word_data = converter(candidate_word_data, cache=False)
    conflicts = [w for w in candidate_word_data for u in used_words_data if w[0] == u[0] and w[1] == u[1] and w[2] != u[2]]
    return not conflicts


def word_candidates_gen(word:str, directions:tuple[Directions], width:int, height:int) -> Generator[list, Any, None]:
    """Generator function to create valid placements and directions of a given word in a hypothetical grid.
    Returns:    list[
                        (x,y)       coordinates
                        [d, ...]    immutable sequence of directions
    ]"""
    word_len = len(word)
    for y in range(height):
        for x in range(width):
            yield [(x,y), [d for d in directions if 0 <= x + d.value[0] * (word_len - 1) < width and 0 <= y + d.value[1] * (word_len - 1) < height]]


def find_word_candidates(new_word:str, used_word_data:tuple, valid_directions:tuple[Directions], validator_funcs:tuple, width:int, height:int) -> list:
    """High level function to find correct placements of a given word in a hypothetical grid, given
    other words that are already placed in said grid, and specific directions or orientations the word
    is allowed to be in."""
    generator = word_candidates_gen(new_word, valid_directions, width, height)
    candidates = []
    for item in generator:
        position:tuple = item[0]
        directions:list = item[1]
        for validate in validator_funcs:
            for j in range(len(directions)-1, -1, -1):
                d:Directions = directions[j]
                validation_data = ((position, d, new_word),)
                if not validate(validation_data, used_word_data):
                    del directions[j]
        if directions:
            candidates.append(item)
    return candidates


def find_valid_directions(word:str, width:int, height:int) -> tuple:
    """Finds the allowed directions or orientations of a given word, in a hypothetical grid."""
    word_len = len(word)
    valid_directions = [d for d in Directions]
    if word_len > width:
        valid_directions = [Directions.DOWN, Directions.UP]
    elif word_len > height:
        valid_directions = [Directions.RIGHT, Directions.LEFT]
    return tuple(valid_directions)


def random_fill_puzzle_grid(grid:tuple, placeholder = str|None) -> tuple:
    """Replaces empty grid places with random letters."""
    tmp_ = [[char for char in row] for row in grid]
    for j in range(len(tmp_)):
        row = tmp_[j]
        for i in range(len(row)):
            if row[i] == placeholder:
                row[i] = choice(ascii_lowercase)
    grid = tuple([tuple(row) for row in tmp_])
    return grid


def send_puzzles_to_writer(start_nodes:list[LinkedListItemSingleLink]|set[LinkedListItemSingleLink], writer_func:Callable, conversion_func:Callable, grid_width:int, grid_height:int, complete_grids:bool, placeholder:str) -> None:
    """Given a set of starting nodes for puzzle combinations, generate each puzzle then send it to
    a file writer callback.
    start_nodes:            collection of LinkedList nodes to start from.
    writer_func:            file writer callback function.
    adapter_func:           function to convert from LinkedList data to data used by puzzle Grid.
    grid_width:             width of puzzle grid, in letters.
    grid_height:            height of puzzle grid, in letters.
    complete_grids:         should unused grid locats be filled with random letters? otherwise use placeholder.
    placeholder:            placeholder character used by incomplete grids."""
    for node in start_nodes:
        word_data = [node.data]
        prev_link = node.link
        while prev_link is not None and prev_link.data != END_NODE:
            word_data.append(prev_link.data)
            prev_link = prev_link.link
        char_positions = conversion_func(tuple(word_data))
        grid:tuple = data_converters.char_position_to_letter_grid_converter(char_positions, grid_width, grid_height, placeholder)
        if complete_grids:
            grid = random_fill_puzzle_grid(grid)
        str_rows = ["".join(row) for row in grid]
        str_output = ",".join(str_rows)
        str_output = "".join([str_output, ";"])
        writer_func(str_output)


def recurse_update_linked_list(prev_item:LinkedListItemSingleLink, next_word_ndx:int, wordlist:list[str], candidates_func:Callable, directions_func:Callable, end_state_callback_func:Callable, item_limit:Decimal, is_sequential:bool) -> None:
    """Recursively build out the linked list tree for puzzle combinations. When a full combination is identified,
    pass it to a callback function for further processing.
    prev_item:              previous node to update from
    next_word_ndx:          index number for next word to use, from the wordlist
    wordlist:               list of word strings
    candidates_func:        function which finds candidate positions and directions of a given word
    directions_func:        function which finds valid directions a word in a given position, can have
    end_state_callback:     function to call, upon leaf nodes, when leaf nodes are identified
    new_item_limit:         counting limit, of new nodes to create
    is_sequential:          are nodes created in deterministic sequence? otherwise random"""
    if item_limit == 0:
        return

    if DEBUG:
        print(f"{'\t' * next_word_ndx}>>> recurse_update_linked_list:  {prev_item} {next_word_ndx} {wordlist[next_word_ndx]} {item_limit}")

    next_word = wordlist[next_word_ndx]
    prev_words_data = []
    if prev_item.data != END_NODE:
        prev_words_data.append(prev_item.data)
    prev_link = prev_item.link
    while prev_link is not None and prev_link.data != END_NODE:
        prev_words_data.append(prev_link.data)
        prev_link = prev_link.link
    prev_words_data = tuple(prev_words_data)
    directions = directions_func(next_word)
    candidates = candidates_func(next_word, prev_words_data, directions)

    items_data = [(pos, d, next_word) for pos, directions in candidates for d in directions]
    if not is_sequential:
        items_data = set(items_data)
    new_item_count = len(items_data)
    if DEBUG:
        print(f"\t{'\t' * next_word_ndx}>>> candidates count:  word={next_word} count={len(items_data)}")

    new_items = []
    differential = Decimal(0)
    if item_limit == 1:
        new_items.append(LinkedListItemSingleLink(items_data.pop(), prev_item))
        next_limit = Decimal(1)
    elif item_limit == -1:
        new_items = [LinkedListItemSingleLink(data, prev_item) for data in items_data]
        next_limit = Decimal(-1)
    elif item_limit >= new_item_count:
        new_items = [LinkedListItemSingleLink(data, prev_item) for data in items_data]
        differential = (Decimal(item_limit) + DECIMAL_ADJUSTMENT_FACTOR) / Decimal(new_item_count)
        next_limit = Decimal(int(differential))
    else:
        current_item_limit = int(item_limit)
        for _ in range(current_item_limit):
            data = items_data.pop()
            new_items.append(LinkedListItemSingleLink(data, prev_item))
        next_limit = Decimal(1)
    if not is_sequential:
        new_items = set(new_items)

    if DEBUG:
        global NODE_COUNT
        global LL_MEMORY_SIZE
        for item in new_items:
            NODE_COUNT += 1
            LL_MEMORY_SIZE += sys.getsizeof(item)

    if next_word_ndx + 1 >= len(wordlist):
        if DEBUG:
            print(f"\n\t\t{'\t' * next_word_ndx}----- END STATE:  write {len(new_items)} puzzles.\n")
        end_state_callback_func(new_items)
        # limits memory usage
        for item in new_items:
            item.link = None
        prev_item.link = None
    else:
        new_word_ndx = next_word_ndx + 1
        if not differential:
            for next_item in new_items:
                if DEBUG:
                    print(f"\t\t{'\t' * next_word_ndx}>>> future recursion:  next_limit={next_limit}, with no diff")
                recurse_update_linked_list(next_item, new_word_ndx, wordlist, candidates_func, directions_func, end_state_callback_func, next_limit, is_sequential)
        else:
            old_c, next_c = Decimal(0), differential
            for next_item in new_items:
                if DEBUG:
                        print(f"\t\t{'\t' * next_word_ndx}>>> future recursion:  next_limit={int(next_c) - int(old_c)}")
                next_count = Decimal(int(next_c) - int(old_c))
                recurse_update_linked_list(next_item, new_word_ndx, wordlist, candidates_func, directions_func, end_state_callback_func, next_count, is_sequential)
                old_c, next_c = next_c, next_c + differential

def parse_args() -> argparse.Namespace:
    """Command line arguments."""
    parser = argparse.ArgumentParser(epilog="""Default Behaviour: Creates a single random puzzle, incomplete, as a square grid the width of the longest word.
    Grid places not filled with letters have a `*` symbol as a placeholder.""")
    parser.add_argument('wordlist', help='Text file containing a list of words to use. Words must be separated by newlines and contain only letters.')
    parser.add_argument('-w', '--width', type=int, help='Width of the puzzle grid. Must be a whole number. Defaults to the length of the longest word.')
    parser.add_argument('-l', '--height', type=int, help='Height of the puzzle grid. Must be a whole number. Defaults to the length of the longest word.')
    parser.add_argument('-p', '--puzzle_count', type=int, default=1, help="The number of puzzles to create.")
    parser.add_argument('-c', '--create_all', action='store_true', help="create all possible puzzle combinations. Overrides -p and --puzzle_count")
    parser.add_argument('--incomplete', action='store_true', help='Save the resulting puzzles as incomplete grids, with a placeholder symbol for places not used by words.')
    parser.add_argument('--placeholder', type=str, default='*', help='Symbol to use as a placeholder when making incomplete puzzles. Ignored if --incomplete is not specified.')
    parser.add_argument('-o', '--output_filename', type=str, default=DEFAULT_OUTPUT_FILE, help="Text File to save the resulting puzzles to. The default is 'output.txt'. If the specified (or default) file exists, a new file is created instead.")
    parser.add_argument('-s', '--sequential', action='store_true', help='Generate the puzzles in a predictable, repeatable order. Useful for testing and for study with new wordlists.')
    parser.add_argument('--DEBUG', action='store_true', help="Show some simple debugging output to the screen.")
    parser.add_argument('--LOGGING', action='store_true', help="Write verbose info to a logging file. The --DEBUG option must also be specified.  CAUTION -- logging file could become very big!!")
    return parser.parse_args()


def make_puzzles(args:argparse.Namespace, new_puzzle_callback:Callable) -> None:
    """Main function.
    args:                   command line arguments object.
    new_puzzle_callback:    callback function for when new puzzles are found."""
    start_time = time()
    if args.DEBUG:
        global DEBUG
        DEBUG = True
    if not path.exists(args.wordlist):
        print(f"ERROR: the filepath '{args.wordlist}' could not be found.")
        return
    wlist = get_wordlist(args.wordlist)
    wlist = sorted(wlist, key=lambda x: len(x), reverse=True)
    greatest_length = len(wlist[0])

    if args.width is None:
        WORD_SEARCH_WIDTH = greatest_length
    elif args.width < greatest_length:
        print("WARNING: specified width is shorter than the longest word. Increasing width to fit word.")
        WORD_SEARCH_WIDTH = greatest_length
    else:
        WORD_SEARCH_WIDTH = args.width

    if args.height is None:
        WORD_SEARCH_HEIGHT = greatest_length
    elif args.height < greatest_length:
        print("WARNING: specified height is shorter than the longest word. Increasing height to fit word.")
        WORD_SEARCH_HEIGHT = greatest_length
    else:
        WORD_SEARCH_HEIGHT = args.height
    NUM_PUZZLES = args.puzzle_count
    if args.create_all:
        NUM_PUZZLES = -1
    NUM_PUZZLES = Decimal(NUM_PUZZLES)
    MAKE_COMPLETE_GRIDS = not args.incomplete
    GRID_PLACEHOLDER = args.placeholder
    IS_SEQUENTIAL = args.sequential


    converter_ = data_converters.make_word_placement_to_char_position_converter()
    validator_no_overlap = partial(validator_non_overlapping, converter=converter_)
    validators = tuple([validator_no_overlap])
    get_word_candidates = partial(find_word_candidates, validator_funcs=validators, width=WORD_SEARCH_WIDTH, height=WORD_SEARCH_HEIGHT)
    get_valid_directions = partial(find_valid_directions, width=WORD_SEARCH_WIDTH, height=WORD_SEARCH_HEIGHT)
    puzzle_writer_ = partial(send_puzzles_to_writer, writer_func=new_puzzle_callback, conversion_func=converter_, grid_width=WORD_SEARCH_WIDTH, grid_height=WORD_SEARCH_HEIGHT, placeholder=GRID_PLACEHOLDER, complete_grids=MAKE_COMPLETE_GRIDS)

    recurse_create_puzzles = partial(recurse_update_linked_list, candidates_func=get_word_candidates, directions_func=get_valid_directions, end_state_callback_func=puzzle_writer_)

    if args.DEBUG and args.LOGGING:
        with open(LOGGING_FILE, "a") as fp:
            fp.write("wordlist=")
            fp.write(str(wlist))
            fp.write("\n")

    if args.DEBUG:
        print(">>> beginning recursive puzzle generation.")
    ending_node = LinkedListItemSingleLink(END_NODE, None)
    start_word_ndx = 0
    if DEBUG:
        global NODE_COUNT
        NODE_COUNT += 1
        global LL_MEMORY_SIZE
        LL_MEMORY_SIZE += sys.getsizeof(ending_node)
    recurse_create_puzzles(ending_node, start_word_ndx, wlist, item_limit=NUM_PUZZLES, is_sequential=IS_SEQUENTIAL)

    if args.DEBUG:
        print(">>> puzzle generation complete.")

    if args.DEBUG:
        print("TOTAL NODES ==", NODE_COUNT)
        print("MAX GRAPH MEMORY SIZE  ==", LL_MEMORY_SIZE, "bytes")
        total_time = int((time() - start_time) * 100) / 100
        print("TOTAL TIME (GENERATION)  ==", total_time, "seconds")


if __name__ == "__main__":
    start_total_time = 0
    args = parse_args()
    if args.DEBUG:
        start_total_time = time()
    OUTPUT_FILENAME = args.output_filename
    fname_counter = 0
    while path.exists(OUTPUT_FILENAME):
        OUTPUT_FILENAME = OUTPUT_FILENAME.rsplit(f".{fname_counter}.txt", 1)[0]
        fname_counter += 1
        OUTPUT_FILENAME = f"{OUTPUT_FILENAME}.{fname_counter}.txt"
    writerProcess = WriterProcessManager(OUTPUT_FILENAME)
    try:
        make_puzzles(args, writerProcess.add)
    except KeyboardInterrupt:
        print("forcing program to halt...")
    if args.DEBUG:
        print(">>> Waiting for writer process to halt...")
    writerProcess.halt()
    if args.DEBUG:
        print(">>> Writer Process Halted.")
        with open(OUTPUT_FILENAME) as fp:
            data = fp.read()
            print("\t\toutput puzzle count =", len(data.split(";")[:-1]))
            print("\t\toutput file size =", len(data), "bytes")
            print("\t\tTOTAL TIME (WRITING) =", int((time() - start_total_time) * 100) / 100)
