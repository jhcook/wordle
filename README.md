# TL;DR

This is a command-line implementation of Wordle® developed and tested on
macOS. If you are on Linux, `yum install words` will make this game usable.
If you are an any other platform, you will need to use a list of words
provided.

This started as a personal project after I read a post online. In just a couple
hours, I started adding functionality, and I do believe the solver is one of
the best available -- fast and efficient.

I run it in a-shell on my iPhone ;)

## Wordle

It took social media by storm, and then NY Times bought it!

This is my ascii terminal version for mere mortals -- or you may like it if
you're a command-line warrior.

You can see below the command line and options available. By default,
it uses the dictionary available on your system. You can download and use
any dictionary you feel comfortable with.

```bash
$ ./wordle.py -h
usage: wordle.py [options]

The game of Wordle.

optional arguments:
  -h, --help            show this help message and exit
  -a, --assistance      give word hints
  -v, --verbose         increase verbosity
  -w WORDS, --words WORDS
                        path to dictionary

Use "?" in guess for suggestions
```

Here is an invocation using the standard dictionary -- and it adawes you with
stimulating intellectual exercise.

```bash
$ ./wordle.py
Enter 1st word: toter
 T  O  T  E  R
Enter 2nd word: ?
Suggestions: roust, rowty, corta, rocta, dorts
Enter 2nd word: roust
 R  O  U  S  T
Enter 3rd word: rowty
 R  O  W  T  Y
Enter 4th word: rorty
 R  O  R  T  Y
Enter 5th word: rooty
 R  O  O  T  Y
Good job!
```

If you want a little help, you can use the assist option to provide a list of
words that match the hints provided by the success/failure of your current
guesses.

```bash
$ ./wordle.py -a
Enter 1st word: crude
 C  R  U  D  E
Suggestions: dutch, duchy, dunch, lucid, mucid
Enter 2nd word: dutch
 D  U  T  C  H
Suggestions: ducal
Enter 3rd word: ducal
 D  U  C  A  L
Good job!
```

## Wordle Solver

This tool uses a dictionary of words with hints provided and suggests possible
answers matching the hints. It's pretty clever indeed.

```bash
$ ./wsolver.py -h
usage: wsolver.py [options]

A tool to help solve Wordle.

options:
  -h, --help            show this help message and exit
  -a FIRST, --first FIRST
                        1st character hint
  -b SECOND, --second SECOND
                        2nd character hint
  -c THIRD, --third THIRD
                        3rd character hint
  -d FOURTH, --fourth FOURTH
                        4th character hint
  -e FIFTH, --fifth FIFTH
                        5th character hint
  -i, --interactive     interactive session
  -v, --verbose         increase verbosity
  -w WORDS, --words WORDS
                        path to dictionary
  -z DUD, --dud DUD     characters not in word

...just like that!
```

Potential candidates are sorted by [letter frequency](https://artofproblemsolving.com/news/articles/the-math-of-winning-wordle).
[More information](https://www.dictionary.com/e/wordle/) on letter distribution and frequency is used to weigh potential words.

[Words on AoPS Online](https://artofproblemsolving.com/texer/vxeinejf) is a great source. Using this list, we see grouping of letters.

As seen below, `a, e, r` are the highest occuring followed by `o,t,l,i,s` and
`n` on its lonesome. Therefore, `wsolver.py` has the ability to _study_ the
dictionary and optimise the algorithm. However, the default is to use the most
common letters of previous official Wordle® results. If you prefer, use the
`-s` command-line option when using a custom dictionary.

```bash
$ for c in {a..z} ; do echo -n "$c: " ; awk "/$c/{print$0}" wwords | wc -l ; done | sort -rk2
e:     1056
a:      909
r:      837
o:      673
t:      667
l:      648
i:      647
s:      618
n:      550
...
```

In the example below, the `!` character is used to
mark the character as yellow, i.e., used in the word but not that position.
Green characters are marked as just the letter for that position and duds are
known black out or letters known not to be used in the word. The following is a
real-world example with the answer being _caulk_ in Wordle 242. The dictionary
can be found on [Github](https://raw.githubusercontent.com/dwyl/english-words/master/words.txt).

The first word was _lunch_. The hints provided the following suggestions
and the second word choice was _oculi_. The hints provided fewer suggestions
with _caulk_ selected as the correct final choice. Use `-v` command-line option
for an exhaustive list of potential words.

```bash
 ./wsolver.py -ivw dict/wordlewords
first known letter: !l
second known letter: !u
third known letter:
fourth known letter: !c
fifth known letter:
Known duds: nh
Suggestions: cruel, ulcer, clued, caulk, clout, cloud, could, clump

$ ./wsolver.py -i
first known letter:
second known letter: !c
third known letter: u
fourth known letter: l
fifth known letter:
Known duds: oi
Suggestions: caulk
```

Multiple round of hints can be provided in one go. For example, the above hints
are combined below. Note that known letters (green) override yellow or unknown
position letters.

```bash
$ ./wsolver.py -i -w dict/wordlewords
first known letter: !l
second known letter: !uc
third known letter: u
fourth known letter: l
fifth known letter:
Known duds: nhoi
Suggestions: caulk
```

The non-interactive command-line argument version:

```bash
$ ./wsolver.py -a '!l' -b '!uc' -c u -d l -z nhoi -w dict/wordlewords
Suggestions: caulk
```
