import argparse
import sys
from enum import Enum
from functools import partial
from os import path
from time import time
from typing import Any, Callable

START_NODE = "START"
END_NODE = "END"
NODE_ATTR_POSITION = "position"
NODE_ATTR_DIRECTION = "direction"
NODE_ATTR_DIMENSIONS = "x_y_dimensions"
NODE_ATTR_WORD = "word"
KEY_PREV_NODE = 'prev_node'
KEY_CURRENT_WORD = 'word'
KEY_HIERARCHY_DATA = 'used_words_data'
LOGGING_FILE = f"word_search_generation.{time()}.log"

NODE_COUNT = 0
LL_MEMORY_SIZE = 0
DEBUG = False


class Directions(Enum):
    UP = (0,-1)
    UP_RIGHT = (1,-1)
    RIGHT = (1,0)
    DOWN_RIGHT = (1,1)
    DOWN = (0,1)
    DOWN_LEFT = (-1,1)
    LEFT = (-1,0)
    UP_LEFT = (-1,-1)


class Grid:
    def __init__(self, width:int, height:int) -> None:
        self._width = width
        self._height = height
        self._placeholder = None
        self._array = [[None for _ in range(width)] for _ in range(height)]

    def __getitem__(self, key):
        x, y = key
        return self._array[y][x]

    def __setitem__(self, key, value) -> None:
        x, y = key
        self._array[y][x] = value

    def __delitem__(self, key) -> None:
        x, y = key
        self._array[y][x] = None

    def __str__(self) -> str:
        rows = []
        for r in self._array:
            new_row = []
            for x in r:
                if x is None:
                    new_row.append(str(self._placeholder))
                else:
                    new_row.append(str(x))
            rows.append(''.join(new_row))
        rows = ','.join(rows)
        return str(rows)

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def placeholder(self) -> str:
        return str(self._placeholder)

    @placeholder.setter
    def placeholder(self, value) -> None:
        self._placeholder = str(value)


class LinkedListItemSingleLink:
    __slots__ = ('data', 'link')
    def __init__(self, data=None, link=None) -> None:
        self.data:Any = data
        self.link:LinkedListItemSingleLink|None = link

    def __str__(self) -> str:
        return f"<LinkedListItemSingleLink:data={self.data},link={self.link}>"


def get_wordlist(fname:str) -> list[str]:
    with open(fname) as fp:
        wordlist = sorted([w.strip() for w in fp.readlines()], key=lambda x: len(x), reverse=True)
    return wordlist


def word_data_tuple_to_dict_adapter():
    func_cache = {}
    def func_(word_data, cache=True):
        hcode = hash(word_data)
        if cache and hcode in func_cache:
            return func_cache[hcode]
        tmp = set()
        for entry in word_data:
            p, d, w = entry
            if isinstance(d, Directions):
                d = d.value
            for i, c in enumerate(w):
                item = (p[0] + d[0] * i, p[1] + d[1] * i, c)
                tmp.add(item)
        tmp = tuple(sorted(tmp))
        if cache:
            func_cache[hcode] = tmp
        return tmp
    return func_


def validator_non_overlapping(candidate_word_data, used_words_data, adapter) -> bool:
    used_words_data = adapter(used_words_data)
    candidate_word_data = adapter(candidate_word_data, cache=False)
    conflicts = [w for w in candidate_word_data for u in used_words_data if w[0] == u[0] and w[1] == u[1] and w[2] != u[2]]
    return not conflicts


def word_candidates_gen(word:str, directions:tuple[Directions], width:int, height:int):
    word_len = len(word)
    for y in range(height):
        for x in range(width):
            yield [(x,y), [d for d in directions if 0 <= x + d.value[0] * (word_len - 1) < width and 0 <= y + d.value[1] * (word_len - 1) < height]]


def find_word_candidates(new_word:str, used_word_data:tuple, valid_directions:tuple[Directions], validator_funcs:tuple, width:int, height:int) -> list:
    generator = word_candidates_gen(new_word, valid_directions, width, height)
    candidates = []

    for item in generator:
        position, directions = item
        for validate in validator_funcs:
            for j in range(len(directions)-1, -1, -1):
                d = directions[j]
                validation_data = ((position, d, new_word),)
                if not validate(validation_data, used_word_data):
                    del directions[j]
        if directions:
            candidates.append(item)

    return candidates


def find_valid_directions(word:str, width:int, height:int) -> tuple:
    word_len = len(word)
    valid_directions = [d for d in Directions]
    if word_len > width:
        valid_directions = [Directions.DOWN, Directions.UP]
    elif word_len > height:
        valid_directions = [Directions.RIGHT, Directions.LEFT]
    return tuple(valid_directions)


def write_puzzles_to_output(start_nodes:list[LinkedListItemSingleLink], output_filename:str, adapter_func:Callable, grid_width:int, grid_height:int) -> None:
    for node in start_nodes:
        word_data = [node.data]
        prev_link = node.link
        while prev_link is not None and prev_link.data != END_NODE:
            word_data.append(prev_link.data)
            prev_link = prev_link.link
        word_data = adapter_func(tuple(word_data))
        grid = Grid(width=grid_width, height=grid_height)
        grid.placeholder = '*'
        for entry in word_data:
            x, y, c = entry
            grid[x, y] = c
        with open(output_filename, 'a') as fp:
            fp.write(str(grid))
            fp.write(';')


def recurse_update_linked_list(prev_item:LinkedListItemSingleLink, next_word_ndx:int, wordlist:list[str], candidates_func:Callable, directions_func:Callable, puzzle_writer_func:Callable) -> None:
    next_word = wordlist[next_word_ndx]
    prev_words_data = []
    if prev_item.data != END_NODE:
        prev_words_data.append(prev_item.data)
    prev_link = prev_item.link
    while prev_link is not None and prev_link.data != END_NODE:
        prev_words_data.append(prev_link.data)
        prev_link = prev_link.link
    new_items = []
    directions = directions_func(next_word)
    candidates = candidates_func(next_word, tuple(prev_words_data), directions)
    items_data = [(pos, d, next_word) for pos, directions in candidates for d in directions]
    for data in items_data:
        new_items.append(LinkedListItemSingleLink(data, prev_item))
    if DEBUG:
        global NODE_COUNT
        global LL_MEMORY_SIZE
        for item in new_items:
            NODE_COUNT += 1
            LL_MEMORY_SIZE += sys.getsizeof(item)
    if next_word_ndx + 1 >= len(wordlist):
        puzzle_writer_func(new_items)
        for item in new_items:
            item.link = None
        prev_item.link = None
    else:
        for next_item in new_items:
            recurse_update_linked_list(next_item, next_word_ndx + 1, wordlist, candidates_func, directions_func, puzzle_writer_func)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('wordlist', help='Text file containing a list of words to use. Words must be separated by newlines and contain only letters.')
    parser.add_argument('-w', '--width', type=int, help='Width of the puzzle, in letters.')
    parser.add_argument('-l', '--height', type=int, help='Height of the puzzle, in letters.')
    parser.add_argument('-p', '--puzzle_count', type=int, default=0, help="Limit output to the number of puzzles given")
    parser.add_argument('-o', '--output_filename', default=None, help="Text File to save the resulting puzzles to.")
    parser.add_argument('--DEBUG', action='store_true', help="Show some simple debugging output to the screen.")
    parser.add_argument('--LOGGING', action='store_true', help="Write verbose info to a logging file. CAUTION -- file could become very big!!")
    parser.add_argument('--CYTOSCAPE', action='store_true', help="record graph data to a Cytoscape file for later analysis.")
    return parser.parse_args()


def main() -> None:
    start_time = time()
    args = parse_args()
    if args.DEBUG:
        global DEBUG
        DEBUG = True
    if not path.exists(args.wordlist):
        print(f"ERROR: file {args.wordlist} could not be found")
        return
    wlist = get_wordlist(args.wordlist)
    greatest_length = len(wlist[0])
    WORD_SEARCH_WIDTH = greatest_length
    WORD_SEARCH_HEIGHT = greatest_length
    if args.width < WORD_SEARCH_WIDTH:
        print("WARNING: specified width is shorter than the longest word. Increasing width to fit word.")
    else:
        WORD_SEARCH_WIDTH = args.width
    if args.height < WORD_SEARCH_HEIGHT:
        print("WARNING: specified height is shorter than the longest word. Increasing height to fit word.")
    else:
        WORD_SEARCH_HEIGHT = args.height
    NUM_PUZZLES:int = -1
    if args.puzzle_count > 0:
        NUM_PUZZLES = args.puzzle_count
    if args.output_filename is not None:
        OUTPUT_FILENAME = args.output_filename
    else:
        OUTPUT_FILENAME = f"puzzle_output.{time()}.txt"
    fname_counter = 0
    while path.exists(OUTPUT_FILENAME):
        OUTPUT_FILENAME = OUTPUT_FILENAME.rsplit(f".{fname_counter}.txt", 1)[0]
        fname_counter += 1
        OUTPUT_FILENAME = f"{OUTPUT_FILENAME}.{fname_counter}.txt"


    adapter_ = word_data_tuple_to_dict_adapter()
    validator_no_overlap = partial(validator_non_overlapping, adapter=adapter_)
    validators = tuple([validator_no_overlap])
    get_word_candidates = partial(find_word_candidates, validator_funcs=validators, width=WORD_SEARCH_WIDTH, height=WORD_SEARCH_HEIGHT)
    get_valid_directions = partial(find_valid_directions, width=WORD_SEARCH_WIDTH, height=WORD_SEARCH_HEIGHT)
    puzzle_writer_ = partial(write_puzzles_to_output, output_filename=OUTPUT_FILENAME, adapter_func=adapter_, grid_width=WORD_SEARCH_WIDTH, grid_height=WORD_SEARCH_HEIGHT)
    recurse_create_puzzles = partial(recurse_update_linked_list, wordlist=wlist, candidates_func=get_word_candidates, directions_func=get_valid_directions, puzzle_writer_func=puzzle_writer_)

    if args.DEBUG and args.LOGGING:
        with open(LOGGING_FILE, "a") as fp:
            fp.write("wordlist=")
            fp.write(str(wlist))
            fp.write("\n")

    if args.DEBUG:
        print(">>> beginning recursive puzzle generation.")
    end_node = LinkedListItemSingleLink(END_NODE, None)
    next_word_ndx = 0
    global NODE_COUNT
    NODE_COUNT += 1
    global LL_MEMORY_SIZE
    LL_MEMORY_SIZE += sys.getsizeof(end_node)
    recurse_create_puzzles(end_node, next_word_ndx)

    if args.DEBUG:
        print(">>> puzzle generation complete.")

    if args.DEBUG:
        print("TOTAL NODES ==", NODE_COUNT)
        print("MAX GRAPH MEMORY SIZE  ==", LL_MEMORY_SIZE, "bytes")
        total_time = int((time() - start_time) * 100) / 100
        print("TOTAL TIME  ==", total_time, "seconds")


if __name__ == "__main__":
    main()
