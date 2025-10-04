import argparse
import multiprocessing as mp
import sys
from enum import Enum
from functools import partial
from os import path
from random import choice
from string import ascii_lowercase
from time import time
from typing import Any, Callable

### TODO: figure out why

END_NODE = "END"
LOGGING_FILE = f"word_search_generation.{time()}.log"
DEFAULT_OUTPUT_FILE = f"puzzle_output.{time()}.txt"

NODE_COUNT = 0
LL_MEMORY_SIZE = 0
DEBUG = False

class ProcessManager:
    END_MSG_WRITE = '!!EOF'

    def __init__(self, filename:str, mode:str='a'):
        ctx = mp.get_context('spawn')
        self._queue:mp.Queue[str] = ctx.Queue()
        self._fname = filename
        self._fmode = mode
        self._process = ctx.Process(target=self.process_write_to_file)
        self._process.start()
        # print("Starting Process")

    def add(self, item):
        if self._queue is not None:
            self._queue.put(item)
            # print("Queued Item:", item)

    def process_write_to_file(self):
        while True:
            # print("Queue size:", self._queue.qsize())
            if not self._queue.empty():
                next_item = self._queue.get()
                if next_item == self.END_MSG_WRITE:
                    with open(self._fname, self._fmode) as fp:
                        fp.flush()
                    break
                with open(self._fname, self._fmode) as fp:
                    fp.write(next_item)
                    # print("Writing Item:", next_item)
        # print(">>> End of Process Func")

    def halt(self):
        self.add(self.END_MSG_WRITE)
        self._process.join()


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
        self._array:list[list[Any]] = [[None for _ in range(width)] for _ in range(height)]

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
        old_placeholder = self._placeholder
        self._placeholder = str(value)
        for i in range(self._width):
            for j in range(self._height):
                if self._array[j][i] == old_placeholder:
                    self._array[j][i] = str(value)


class LinkedListItemSingleLink:
    __slots__ = ('data', 'link')
    def __init__(self, data=None, link=None) -> None:
        self.data:Any = data
        self.link:LinkedListItemSingleLink|None = link

    def __str__(self) -> str:
        return f"<LinkedListItemSingleLink:data={self.data},link={self.link}>"


def get_wordlist(fname:str) -> list[str]:
    """Given a filename of a text file and assuming it contains a newline separated list of words,
    return the text contents as a list."""
    with open(fname) as fp:
        wordlist = [w.strip() for w in fp.readlines()]
    if wordlist[-1] == '':
        del wordlist[-1]
    return wordlist


def word_data_tuple_to_dict_adapter():
    """Returns an adapter closure for converting data representing word positions on grids, from
    a tuple format to a dict format. The closure uses a hashed cache to speed up repeat conversions."""
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
    """Validation function to compare data representing words placed on a grid. Returns True if
    no words are overlapping or all overlapping words have the same letters at shared grid locations."""
    used_words_data = adapter(used_words_data)
    candidate_word_data = adapter(candidate_word_data, cache=False)
    conflicts = [w for w in candidate_word_data for u in used_words_data if w[0] == u[0] and w[1] == u[1] and w[2] != u[2]]
    return not conflicts


def word_candidates_gen(word:str, directions:tuple[Directions], width:int, height:int):
    """Generator function to create valid placements and directions of a given word in a hypothetical grid."""
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
    """Finds the allowed directions or orientations of a given word, in a hypothetical grid."""
    word_len = len(word)
    valid_directions = [d for d in Directions]
    if word_len > width:
        valid_directions = [Directions.DOWN, Directions.UP]
    elif word_len > height:
        valid_directions = [Directions.RIGHT, Directions.LEFT]
    return tuple(valid_directions)


def random_fill_puzzle_grid(grid:Grid) -> Grid:
    """Replaces empty grid places with random letters."""
    for i in range(grid.width):
        for j in range(grid.height):
            if grid[i,j] == grid.placeholder:
                grid[i,j] = choice(ascii_lowercase)
    return grid


def send_puzzles_to_writer(start_nodes:list[LinkedListItemSingleLink], writer_func:Callable, adapter_func:Callable, grid_width:int, grid_height:int, complete_grids:bool, placeholder:str) -> None:
    """Given a set of starting nodes for puzzle combinations, generate each puzzle then send it to
    a file writer callback."""
    for node in start_nodes:
        word_data = [node.data]
        prev_link = node.link
        while prev_link is not None and prev_link.data != END_NODE:
            word_data.append(prev_link.data)
            prev_link = prev_link.link
        word_data = adapter_func(tuple(word_data))
        grid = Grid(width=grid_width, height=grid_height)
        grid.placeholder = placeholder
        for entry in word_data:
            x, y, c = entry
            grid[x, y] = c
        if complete_grids:
            grid = random_fill_puzzle_grid(grid)
        writer_func(str(grid))
        writer_func(';')


def recurse_update_linked_list(prev_item:LinkedListItemSingleLink, next_word_ndx:int, wordlist:list[str], candidates_func:Callable, directions_func:Callable, end_state_callback_func:Callable, new_item_limit:int) -> None:
    """Recursively build out the linked list tree for puzzle combinations. When a full combination is identified,
    pass it to a callback function for further processing."""
    if new_item_limit == 0:
        return
    next_word = wordlist[next_word_ndx]
    prev_words_data = []
    if prev_item.data != END_NODE:
        prev_words_data.append(prev_item.data)
    prev_link = prev_item.link
    while prev_link is not None and prev_link.data != END_NODE:
        prev_words_data.append(prev_link.data)
        prev_link = prev_link.link
    prev_words_data = tuple(prev_words_data)
    new_items = []
    directions = directions_func(next_word)
    candidates = candidates_func(next_word, prev_words_data, directions)
    items_data:set[tuple[tuple, Directions, str]] = set([(pos, d, next_word) for pos, directions in candidates for d in directions])
    next_limit = new_item_limit
    differential = 0
    if new_item_limit == 1:
        new_items.append(LinkedListItemSingleLink(items_data.pop(), prev_item))
    elif new_item_limit == -1 or new_item_limit >= len(items_data):
        new_items = [LinkedListItemSingleLink(data, prev_item) for data in items_data]
        if new_item_limit != -1:
            next_limit = new_item_limit / len(items_data)
            if next_limit <= 1:
                next_limit = 1
            else:
                differential = next_limit - int(next_limit)
                next_limit = int(next_limit) + 1
    else:
        for _ in range(new_item_limit):
            data = items_data.pop()
            new_items.append(LinkedListItemSingleLink(data, prev_item))
        next_limit = 1

    if DEBUG:
        global NODE_COUNT
        global LL_MEMORY_SIZE
        for item in new_items:
            NODE_COUNT += 1
            LL_MEMORY_SIZE += sys.getsizeof(item)

    if next_word_ndx + 1 >= len(wordlist):
        end_state_callback_func(new_items)
        # limits memory usage
        for item in new_items:
            item.link = None
        prev_item.link = None
    else:
        if not differential:
            for next_item in new_items:
                recurse_update_linked_list(next_item, next_word_ndx + 1, wordlist, candidates_func, directions_func, end_state_callback_func, new_item_limit=next_limit)
        else:
            tmp_ = 0
            for next_item in new_items[:-1]:
                tmp_ += differential
                if tmp_ < 1:
                    recurse_update_linked_list(next_item, next_word_ndx + 1, wordlist, candidates_func, directions_func, end_state_callback_func, new_item_limit=next_limit - 1)
                else:
                    recurse_update_linked_list(next_item, next_word_ndx + 1, wordlist, candidates_func, directions_func, end_state_callback_func, new_item_limit=next_limit)
                    tmp_ -= 1
            next_item = new_items[-1]
            recurse_update_linked_list(next_item, next_word_ndx + 1, wordlist, candidates_func, directions_func, end_state_callback_func, new_item_limit=next_limit)


def parse_args():
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
    parser.add_argument('--DEBUG', action='store_true', help="Show some simple debugging output to the screen.")
    parser.add_argument('--LOGGING', action='store_true', help="Write verbose info to a logging file. The --DEBUG option must also be specified.  CAUTION -- logging file could become very big!!")
    return parser.parse_args()


def main() -> None:
    "Main function."
    start_time = time()
    args = parse_args()
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
    OUTPUT_FILENAME = args.output_filename
    fname_counter = 0
    while path.exists(OUTPUT_FILENAME):
        OUTPUT_FILENAME = OUTPUT_FILENAME.rsplit(f".{fname_counter}.txt", 1)[0]
        fname_counter += 1
        OUTPUT_FILENAME = f"{OUTPUT_FILENAME}.{fname_counter}.txt"
    COMPLETE_GRIDS = not args.incomplete
    GRID_PLACEHOLDER = args.placeholder


    adapter_ = word_data_tuple_to_dict_adapter()
    validator_no_overlap = partial(validator_non_overlapping, adapter=adapter_)
    validators = tuple([validator_no_overlap])
    get_word_candidates = partial(find_word_candidates, validator_funcs=validators, width=WORD_SEARCH_WIDTH, height=WORD_SEARCH_HEIGHT)
    get_valid_directions = partial(find_valid_directions, width=WORD_SEARCH_WIDTH, height=WORD_SEARCH_HEIGHT)
    writerProcess = ProcessManager(OUTPUT_FILENAME)
    puzzle_writer_ = partial(send_puzzles_to_writer, writer_func=writerProcess.add, adapter_func=adapter_, grid_width=WORD_SEARCH_WIDTH, grid_height=WORD_SEARCH_HEIGHT, placeholder=GRID_PLACEHOLDER, complete_grids=COMPLETE_GRIDS)

    recurse_create_puzzles = partial(recurse_update_linked_list, wordlist=wlist, candidates_func=get_word_candidates, directions_func=get_valid_directions, end_state_callback_func=puzzle_writer_)

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
    recurse_create_puzzles(end_node, next_word_ndx, new_item_limit=NUM_PUZZLES)

    if args.DEBUG:
        print(">>> puzzle generation complete.")
        print(">>> waiting for writer process to finish...")

    writerProcess.halt()

    if args.DEBUG:
        print(">>> Writer process halted.")
        print("TOTAL NODES ==", NODE_COUNT)
        print("MAX GRAPH MEMORY SIZE  ==", LL_MEMORY_SIZE, "bytes")
        total_time = int((time() - start_time) * 100) / 100
        print("TOTAL TIME  ==", total_time, "seconds")
        with open(OUTPUT_FILENAME) as fp:
            data = fp.read()
            print("output puzzle count =", len(data.split(";")[:-1]))
            print("output file size =", len(data), "bytes")


if __name__ == "__main__":
    main()
