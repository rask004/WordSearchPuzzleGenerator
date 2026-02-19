import os
import sys
from argparse import Namespace as argNamespace
from collections import namedtuple
from pathlib import Path

sys.path.append(str(Path("./modules").resolve()))

from flask import Flask, render_template

from .modules.make_puzzles import make_puzzles

DATA_PATH = "data"

PuzzleContext = namedtuple('PuzzleContext', ['words', 'width', 'height', 'puzzle'])

puzzle_results:list[str] = []

def puzzle_creation_callback(puzzle: list) -> None:
    puzzle_results.extend([c for row in puzzle for c in row])


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.instance_path = os.path.abspath(os.path.dirname(__file__))
    if test_config is None:
        app.config.from_pyfile(os.path.join(app.instance_path, 'config.py'))
    else:
        ## load the test config if passed in
        app.config.from_mapping(test_config)

    @app.get('/')
    def index():
        wordlist_names = [n.split('.', 1)[0] for n in os.listdir(DATA_PATH) if n]
        return render_template("index.html", names=wordlist_names)

    @app.get('/api/')
    def api():
        return render_template("api-help.html")

    @app.get('/api/v1/<wordlist>/')
    def load_puzzle(wordlist:str|None=None):
        puzzle_results.clear()
        wordlist_path = Path(f"{DATA_PATH}/{str(wordlist)}.list")
        if wordlist is None or not wordlist_path.exists():
            return render_template("puzzle-404.html", wordlist=wordlist)
        with open(wordlist_path) as fp:
            listdata = [l.strip() for l in fp.readlines() if l]
        longest = 0
        for word in listdata:
            if len(word) > longest:
                longest = len(word)
        args = argNamespace(width=longest + 4, height=longest + 2, placeholder='*')
        make_puzzles(args=args, wordlist=listdata, new_puzzle_callback=puzzle_creation_callback)
        context = PuzzleContext(tuple(listdata), args.width, args.height, tuple(puzzle_results))

        return render_template("puzzle.html", puzzle_context=context)

    return app
