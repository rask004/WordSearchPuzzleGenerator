# WordSearchPuzzleGenerator

A hobby project, as a script to create Word Search / Sopa de Palabra Puzzles.

## Forenote

As this is a hobby project, expect some spagettii coding, bugs, limited documentation and inefficiencies.

## Purpose

Generates a set of **randomised word search puzzle grids**, based at minimum from a text file containing a _list of words_.

## Requirements

At least Python 3.12

## Example

An example webapp can be found in the `examples` folder. The example app requires Flask. 

The App can be run with the command:

`
flask --app . --debug run
`

## Usage Details

This script is expected to be run from a terminal.

Use the `-h` or `--help` option for help details at the command prompt.

### Default Behaviour

python make_puzzles.py wordlist.txt

Creates one random puzzle, using the list of words existing in the `wordlist.txt` file, and writing the puzzle to the file `puzzle_output.???.txt` with the ??? as a POSIX timestamp. The puzzle grid is square shaped with a width the same as the length of the longest word in the wordlist. Grid places not used by words from the wordlist will be filled with random letters.

### Command Line Options

- `<wordlist.txt>`, required, a plain text file containing a list of words. Words must be separated by a new line (that is, one word per line). Words should be in lower case. There should be no blank lines in the file.

- `-w WIDTH`, Puzzle size, width. Must be a _positive whole number_. If not specified, the length of the longest word will be used. If smaller than this length, it will be increased to said length and a warning message will appear.

- `-l HEIGHT`, Puzzle size, height. Must be a _positive whole number_. If not specified, If not specified, the length of the longest word will be used. If smaller than this length, it will be increased to said length and a warning message will appear.

- `-p COUNT`, Puzzle count, to produce a fixed number of output puzzles. Must be a _positive whole number_.

- `-o FILENAME`, File to write puzzles to. `FILENAME` can include a path if the directory structure already exists. Default is to save to `output.txt` in the working directory. If the output file already exists, a new one is created using the format `<FILENAME>.1.txt`, `<FILENAME>.2.txt`, etc.

- `-c`, `--create_all`, Create all possible puzzles, Overrides `-p COUNT`.

- `--incomplete`, create incomplete puzzle grids, with a placeholder symbol in places not used by words from the wordlist.

- `--placeholder`, specifies what symbol to use as a placeholder in incomplete grids. Ignored if the `--incomplete` option is not used.

- `-s`, `--sequential`, create puzzles in a deterministic, ordered and repeatable manner. This can be useful for testing purposes, and studying the script behaviour with new wordlists.

- `--DEBUG` to show general debugging messages.

- `--DEBUG --LOGGING` to record debugging messages to a log file. Use with caution, debug messages will be more verbose and numerous, which can result in a large log file size.


## Output File

The output puzzles are written as uncompressed text. Puzzles are separated by semi-colons (`;`), puzzle grid rows are separated by commas (`,`) and puzzle grid positions not used by words from the input wordlist are filled with either random letters or a placeholder symbol. 

## Output file Example

`
*now,nioj,*nur,****;**wn,*o*u,n**r,nioj;n**j,u*o*,ri**,nnow;
`

This represents the following _incomplete_ 4 by 4 grids:

`*now    **wn    n**j`
`nioj    *o*u    u*o*`
`*nur    n**r    ri**`
`****    join    nnow`

If the grids were completely filled, then the * symbols would be replaced with random letters.

## Known Issues

Log files can become huge - the bigger the puzzle, the more likely this will happen.

A separate 'writer' process is used to handle writing the output puzzles. If the running script is killed before completion, the writer process might be left in memory.

## Running time

The more puzzles being produced, the more time is required.

Larger puzzles (bigger width or height) require more time.

Larger words, and longer wordlists, require more time.

