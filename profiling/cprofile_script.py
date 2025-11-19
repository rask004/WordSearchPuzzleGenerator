import argparse
import cProfile
import os
import sys

cwd = os.getcwd()
if "testing" in cwd:
    raise RuntimeError("ERROR: This should be executed from the base project directory as 'python testing\\cProfile_script.py'")
sys.path.append(os.getcwd())

try:
    import make_puzzles
except ImportError:
    raise ImportError("Could not import make_puzzles module - are you in the base project directory?")

INPUT_FILENAME = "testing\\test_wordlist_complex.txt"
CPROFILE_OUTPUT = "profiling\\cprofile_results.txt"

args = argparse.Namespace()
with open(INPUT_FILENAME) as fp:
    wordlist = [w for w in fp.read().split('\n') if w]
args.wordlist = None
args.output_filename = None
args.width = 24
args.height = 24
args.DEBUG = False
args.LOGGING = False
args.TIMING = False
args.create_all = False
args.placeholder = "*"
args.puzzle_count = 100
args.incomplete = False
args.sequential = True

print(f"\n>>> PROFILING -> wordlist={",".join(wordlist)};  count={args.puzzle_count};  dimensions={args.width}x{args.height}\n\n")
output_puzzles = []

cProfile.run(statement="make_puzzles.make_puzzles(args, wordlist, output_puzzles.append)", sort='cumtime')
