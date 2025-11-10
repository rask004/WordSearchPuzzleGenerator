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
    "threef,onet*u,***w*l,***o*l,******,******;",
    "tfullo,wh***n,o*r**e,***e**,****e*,******;",
    "tfullo,hw***n,r*o**e,e*****,e*****,******;",
    "fthree,ouw***,*nlo**,**el**,******,******;",
    "ftonet,*uh**w,**lr*o,***le*,*****e,******;",
    "ftone*,uhw***,lr*o**,le****,*e****,******;",
    "fotwo*,unh***,ler***,l*e***,**e***,******;",
    "fott**,unwh**,leor**,l**e**,***e**,******;",
    "fullto,***whn,**o*re,****e*,****e*,******;",
    "fullto,***hwn,**r*oe,*e****,e*****,******;",
    "eerhtf,one*wu,****ol,*****l,******,******;",
    "fullot,two*nh,****er,*****e,*****e,******;",
    "fullot,***nhw,**er*o,**e***,*e****,******;",
    "feerht,ou***w,*nl**o,**el**,******,******;",
    "full*o,threen,*w***e,**o***,******,******;",
)

EXPECTED_PUZZLES_1000 = (
    (0, "threef,onet*u,***w*l,***o*l,******,******;"),
    (1, "threef,onetu*,***lw*,**l**o,******,******;"),
    (11, "threeo,*w*f*n,**ou*e,***l**,***l**,******;"),
    (47, 'fthree,uonet*,l***w*,l***o*,******,******;'),
    (193, 'oneftt,**uwh*,*lor**,l*e***,*e****,******;'),
    (726, 'eone*f,te**u*,w*rl**,o*lh**,****t*,******;'),
    (999, 'onetwo,*efull,**e***,***r**,****h*,*****t;'),
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
    with open(INPUT_FILENAME) as fp:
        wordlist = [w for w in fp.read().split('\n') if w]
    args.wordlist_file = None
    args.output_filename = OUTPUT_FILENAME
    args.width = 6
    args.height = 6
    args.DEBUG = False
    args.LOGGING = False
    args.create_all = False
    args.placeholder = "*"
    args.puzzle_count = 0
    args.incomplete = True
    args.sequential = True
    return {'args':args, 'wordlist':wordlist}


def tear_down() -> None:
    if path.exists(OUTPUT_FILENAME):
        os.unlink(OUTPUT_FILENAME)


def test_create_15_deterministic_puzzles():
    kwargs = setup()
    test_args = kwargs['args']
    wordlist = kwargs['wordlist']
    test_args.puzzle_count = 15
    test_args.sequential = True
    output_puzzles = []
    make_puzzles.make_puzzles(test_args, wordlist, output_puzzles.append)
    assert len(output_puzzles) == 15
    for i in range(15):
        assert EXPECTED_PUZZLES_15[i] == output_puzzles[i]
    tear_down()


def test_create_thousand_deterministic_puzzles():
    kwargs = setup()
    test_args = kwargs['args']
    wordlist = kwargs['wordlist']
    test_args.puzzle_count = 1000
    test_args.sequential = True
    output_puzzles = []
    make_puzzles.make_puzzles(test_args, wordlist, output_puzzles.append)
    assert len(output_puzzles) == 1000
    for ndx, puzzle in EXPECTED_PUZZLES_1000:
        assert puzzle == output_puzzles[ndx]
    tear_down()


def test_create_hundred_random_puzzles():
    kwargs = setup()
    test_args = kwargs['args']
    wordlist = kwargs['wordlist']
    test_args.puzzle_count = 100
    test_args.sequential = False
    output_puzzles = []
    make_puzzles.make_puzzles(test_args, wordlist, output_puzzles.append)
    assert len(output_puzzles) == 100
    tear_down()


def test_create_5000_random_puzzles():
    kwargs = setup()
    mock_writer = MockProcessManager()
    test_args = kwargs['args']
    wordlist = kwargs['wordlist']
    test_args.puzzle_count = 5000
    test_args.sequential = False
    make_puzzles.make_puzzles(test_args, wordlist, mock_writer.add)
    actual_puzzle_count = mock_writer.count
    assert actual_puzzle_count == 5000
    tear_down()


def test_create_13857_random_puzzles():
    kwargs = setup()
    mock_writer = MockProcessManager()
    test_args = kwargs['args']
    wordlist = kwargs['wordlist']
    test_args.puzzle_count = 13857
    test_args.sequential = False
    make_puzzles.make_puzzles(test_args, wordlist,  mock_writer.add)
    actual_puzzle_count = mock_writer.count
    assert actual_puzzle_count == 13857
    tear_down()


def test_create_various_puzzles():
    ### check an edge case regarding puzzle counts in 2 ^ n form
    kwargs = setup()
    test_args = kwargs['args']
    wordlist = kwargs['wordlist']
    for n in range(6, 15):
        base_expected_puzzle_count = 2**n
        for offset in range(-3, 4):
            expected = base_expected_puzzle_count + offset
            test_args.puzzle_count = expected
            test_args.sequential = False
            mock_writer = MockProcessManager()
            make_puzzles.make_puzzles(test_args, wordlist, mock_writer.add)
            actual_puzzle_count = mock_writer.count
            assert actual_puzzle_count == expected
            test_args.sequential = True
            mock_writer = MockProcessManager()
            make_puzzles.make_puzzles(test_args, wordlist, mock_writer.add)
            actual_puzzle_count = mock_writer.count
            assert actual_puzzle_count == expected
    tear_down()


if LONG_TESTS:
    def test_create_all_puzzles():
        kwargs = setup()
        test_args = kwargs['args']
        wordlist = kwargs['wordlist']
        test_args.create_all = True
        test_args.sequential = True
        mock_writer = MockProcessManager()
        make_puzzles.make_puzzles(test_args, wordlist, mock_writer.add)
        actual_puzzle_count = mock_writer.count
        assert actual_puzzle_count == 14435776
        tear_down()


def test_create_complex_puzzles():
    first_puzzle = "pheasantsparrowf,kvcplwrm*eagleaa,heuhebaaacaowl*n,*asliaalvgrgc**t,**wttcctlepou**a,***krukoroniwl*i,*****erecow*e*ll,******lenks*****,****************,****************,****************,****************,****************,****************,****************,****************,****************,****************,****************,****************,****************,****************,****************,****************"
    last_puzzle = "albatroswallowfk,vulturepfowleape,c*mh*aravenanhes,*haag*lrc*gte*at,*wiugc*r*laa**cr,k*lcopooeis***oe,*l*nkwiwla****cl,*****e*en*****k*,******nt********,****************,****************,****************,****************,****************,****************,****************,****************,****************,****************,****************,****************,****************,****************,****************"
    kwargs = setup()
    test_args = kwargs['args']
    with open(INPUT_FILENAME_COMPLEX) as fp:
        wordlist = [w for w in fp.read().split('\n') if w]
    output_puzzles = []
    test_args.wordlist_file = INPUT_FILENAME_COMPLEX
    test_args.width = 16
    test_args.height = 24
    test_args.puzzle_count = 100
    test_args.sequential = True
    make_puzzles.make_puzzles(test_args, wordlist, output_puzzles.append)
    actual_puzzle_count = len(output_puzzles)
    assert actual_puzzle_count == 100
    assert first_puzzle in output_puzzles[0]
    assert last_puzzle in output_puzzles[-1]
    tear_down()
