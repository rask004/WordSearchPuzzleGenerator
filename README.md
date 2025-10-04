# WordSearchPuzzleGenerator

A hobby project, as a script to create Word Search / Sopa de Palabra Puzzles

## Forenote

As this is a hobby project, expect some spagettii coding, bugs, limited documentation and inefficiencies. You have been warned

## Purpose

Generates a set of **randomised, partially filled word search puzzle grids**, based at minimum on a _pair of dimensions_ and a text file containing a _list of words_

## Requirements

At least Python 3.12

## Usage Details

This script is expected to be run from a terminal.

Use `-h` o `--help` option for help details at the command prompt

### Default Behaviour

python make_puzzles.py wordlist.txt

Creates one random puzzle, written to the file `puzzle_output.???.txt` with the ??? as a POSIX timestamp. The puzzle grid is square shaped with a width the same as the length of the longest word in the wordlist. Grid places not used by words from the wordlist will be filled with random letters.

### Commandline Options

- Input filename, of a plain text file containing a list of words. This input filename is mandatory. Words must be separated by a new line (that is, one word per line). Words should be in lower case. There should be no blank lines in the file.
- Puzzle size, width `-w WIDTH` and height `-l HEIGHT` as options. `WIDTH` and `HEIGHT` must be _positive whole numbers_. If not specified, a square grid the size of the longest word is used. If either dimension is smaller than the length of the longest word, a warning should appear and the affected dimension is increased to match the longest word length.
- Puzzle count, `-p COUNT` as option, to produce a fixed number of output puzzles.
- Output puzzle file, `-o FILENAME` as option. `FILENAME` can include a path provided the directory structure already exists. Default is to save to `output.txt` in the working directory. If the output file already exists, a new one is created using the format `<FILENAME>.1.txt`, `<FILENAME>.2.txt`, etc.
- `--DEBUG` to show general debugging messages.
- `--LOGGING` to record debugging messages to a log file. The `--DEBUG`  flag mus be present too. All logged debugging messages are more verbose. Depending on how many puzzles are being produced, the log file can become quite large
- `-c`, or `--create_all` to create all puzzle combinations possible. Overrides the Puzzle Count option, `-p COUNT`.
- `--incomplete` to create incomplete puzzle grids, with a placeholder symbol in places not used by words from the wordlist.
- `--placeholder` to specify what symbol to use as a placeholder in incomplete grids. This does nothing if the `--incomplete` option is not used.

## Output File

The output puzzles are written as uncompressed text. Puzzles are separated by semi-colons (`;`), puzzle grid rows are separated by commas (`,`) and puzzle grid positions not used by words from the input wordlist are filled with random letters, or a placeholder symbol. For example, pretend the input wordlist is `join run now` and we create 3 _incomplete_ puzzles each with 4x4 dimensions, and using `*` as a placeholder. If the output file contains the text:

`
*now,nioj,*nur,****;**wn,*o*u,n**r,nioj;n**j,u*o*,ri**,nnow;
`

Then this represents the following incompletely filled 4x4 grids:

`*now    **wn    n**j`
`nioj    *o*u    u*o*`
`*nur    n**r    ri**`
`****    join    nnow`

If the grids were completely filled, then the * symbols would be replaced with random letters.

## Known Issues

Log files can become huge - the bigger the puzzle, the more likely this will happen.

Currently, all output is randomized.

When specifying a puzzle count limit, it _might_ produce up to _5% less or more_ than the specified limit. This seems to be happening with puzzle counts greater than 20,000.

Large or complex puzzles _will_ take a _long time_ to produce. Generating _all possible_ puzzle combos or a _large number of puzzles_ _definitely_ will take a _very long time_ to complete, especially if the puzzle is complex or large
