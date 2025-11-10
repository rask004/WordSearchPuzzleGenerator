import argparse
import os
import sys
from os import path

cwd = os.getcwd()
if "testing" in cwd:
    raise RuntimeError("ERROR: This should be executed from the base project directory as 'pytest testing\\tests.py'")
sys.path.append(os.getcwd())
try:
    import make_puzzles
except ImportError:
    raise ImportError("Could not import make_puzzles module - are you in the base project directory?")

OUTPUT_FILENAME = "testing\\output.txt"
INPUT_FILENAME = "testing\\test_wordlist.txt"
INPUT_FILENAME_COMPLEX = "testing\\test_wordlist_complex.txt"

EXPECTED_PUZZLES_15 = (
    (0, "******,*e****,*le***,*elr*o,**nuhw,***oft;"),
    (1, "******,******,o**l**,*wl***,*uteno,feerht;"),
    (14, "*e****,**e***,**lr**,*oelh*,**wnut,***tof;"),
)

EXPECTED_PUZZLES_1000 = (
    (0, "three*,******,**l***,*oel**,**wnu*,***tof;"),
    (1, "three*,******,******,**oe**,*wn***,tolluf;"),
    (11, "three*,******,**l***,**le**,**u*n*,**ftwo;"),
    (47, '*three,******,******,**oe**,*wn***,tolluf;'),
    (193, '*****t,****h*,***r*o,**ee*w,*e**nt,lluf*o;'),
    (277, '******,*three,******,**oe**,*w**n*,tfullo;'),
    (578, '****e*,***e**,**r***,*hoe**,twn***,tolluf;'),
    (726, 'e*****,*e****,**r***,**oh*e,*w**tn,tfullo;'),
    (999, '******,*e****,**e***,***r*o,fullhw,**enot;'),
)

COUNT_TESTS = True
LONG_TESTS = False

class MockProcessManager:
    def __init__(self):
        self.count = 0

    def add(self, item):
        self.count += 1

    def halt(self):
        pass


def setup():
    args = argparse.Namespace()
    args.wordlist = INPUT_FILENAME
    args.output_filename = OUTPUT_FILENAME
    args.width = 6
    args.height = 6
    args.DEBUG = False
    args.LOGGING = False
    args.output_filename = None
    args.create_all = False
    args.placeholder = "*"
    args.puzzle_count = 0
    args.incomplete = True
    args.sequential = True
    return {'args':args}


def tear_down() -> None:
    if path.exists(OUTPUT_FILENAME):
        os.unlink(OUTPUT_FILENAME)


def test_create_one_deterministic_puzzle():
    kwargs = setup()
    args = kwargs['args']
    args.puzzle_count = 1
    args.sequential = True
    output_puzzles = []
    make_puzzles.make_puzzles(args, output_puzzles.append)
    assert len(output_puzzles) == 1
    assert EXPECTED_PUZZLES_15[0][1] == output_puzzles[0]
    tear_down()


def test_create_two_deterministic_puzzles():
    kwargs = setup()
    args = kwargs['args']
    args.puzzle_count = 2
    args.sequential = True
    output_puzzles = []
    make_puzzles.make_puzzles(args, output_puzzles.append)
    assert len(output_puzzles) == 2
    assert EXPECTED_PUZZLES_15[0][1] == output_puzzles[0]
    assert EXPECTED_PUZZLES_15[1][1] == output_puzzles[1]
    tear_down()


def test_create_fifteen_deterministic_puzzles():
    kwargs = setup()
    args = kwargs['args']
    args.puzzle_count = 15
    args.sequential = True
    output_puzzles = []
    make_puzzles.make_puzzles(args, output_puzzles.append)
    assert len(output_puzzles) == 15
    for ndx, puzzle in EXPECTED_PUZZLES_15:
        assert puzzle == output_puzzles[ndx]
    tear_down()

if COUNT_TESTS:
    def test_create_hundred_random_puzzles():
        kwargs = setup()
        args = kwargs['args']
        args.puzzle_count = 100
        args.sequential = False
        output_puzzles = []
        make_puzzles.make_puzzles(args, output_puzzles.append)
        assert len(output_puzzles) == 100
        tear_down()


    def test_create_thousand_deterministic_puzzles():
        kwargs = setup()
        args = kwargs['args']
        args.puzzle_count = 1000
        args.sequential = True
        output_puzzles = []
        make_puzzles.make_puzzles(args, output_puzzles.append)
        assert len(output_puzzles) == 1000
        for ndx, puzzle in EXPECTED_PUZZLES_1000:
            assert puzzle == output_puzzles[ndx]
        tear_down()


    def test_create_5000_random_puzzles():
        kwargs = setup()
        mock_writer = MockProcessManager()
        args = kwargs['args']
        args.puzzle_count = 5000
        args.sequential = False
        make_puzzles.make_puzzles(args, mock_writer.add)
        actual_puzzle_count = mock_writer.count
        assert actual_puzzle_count == 5000
        tear_down()


    def test_create_8000_random_puzzles():
        kwargs = setup()
        mock_writer = MockProcessManager()
        args = kwargs['args']
        args.puzzle_count = 8000
        args.sequential = False
        make_puzzles.make_puzzles(args, mock_writer.add)
        actual_puzzle_count = mock_writer.count
        assert actual_puzzle_count == 8000
        tear_down()


    def test_create_9125_random_puzzles():
        kwargs = setup()
        mock_writer = MockProcessManager()
        args = kwargs['args']
        args.puzzle_count = 9125
        args.sequential = False
        make_puzzles.make_puzzles(args, mock_writer.add)
        actual_puzzle_count = mock_writer.count
        assert actual_puzzle_count == 9125
        tear_down()


    def test_create_13857_random_puzzles():
        kwargs = setup()
        mock_writer = MockProcessManager()
        args = kwargs['args']
        args.puzzle_count = 13857
        args.sequential = False
        make_puzzles.make_puzzles(args, mock_writer.add)
        actual_puzzle_count = mock_writer.count
        assert actual_puzzle_count == 13857
        tear_down()


    def test_create_17777_deterministic_puzzles():
        kwargs = setup()
        mock_writer = MockProcessManager()
        args = kwargs['args']
        args.puzzle_count = 17777
        args.sequential = True
        make_puzzles.make_puzzles(args, mock_writer.add)
        actual_puzzle_count = mock_writer.count
        assert actual_puzzle_count == 17777
        tear_down()

    def test_create_various_puzzles():
        ### check an edge case regarding puzzle counts in 2 ^ n form
        kwargs = setup()
        args = kwargs['args']
        for n in range(6, 15):
            base_expected_puzzle_count = 2**n
            for offset in range(-3, 4):
                expected = base_expected_puzzle_count + offset
                args.puzzle_count = expected
                args.sequential = False
                mock_writer = MockProcessManager()
                make_puzzles.make_puzzles(args, mock_writer.add)
                actual_puzzle_count = mock_writer.count
                assert actual_puzzle_count == expected
                args.sequential = True
                mock_writer = MockProcessManager()
                make_puzzles.make_puzzles(args, mock_writer.add)
                actual_puzzle_count = mock_writer.count
                assert actual_puzzle_count == expected
        tear_down()

if LONG_TESTS:
    def test_create_all_puzzles():
        kwargs = setup()
        args = kwargs['args']
        args.create_all = True
        args.sequential = True
        mock_writer = MockProcessManager()
        make_puzzles.make_puzzles(args, mock_writer.add)
        actual_puzzle_count = mock_writer.count
        assert actual_puzzle_count == 14435776
        tear_down()


def test_create_complex_puzzles():
    kwargs = setup()
    args = kwargs['args']
    mock_writer = MockProcessManager()
    args.wordlist = INPUT_FILENAME_COMPLEX
    args.width = 16
    args.height = 24
    args.puzzle_count = 100
    args.sequential = True
    make_puzzles.make_puzzles(args, mock_writer.add)
    actual_puzzle_count = mock_writer.count
    assert actual_puzzle_count == 100
    tear_down()
