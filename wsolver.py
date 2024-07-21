#!/usr/bin/env python3
"""A solver tool for Wordle.
Copyright (C) 2022 Justin Cook

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from argparse import ArgumentParser
from re import compile
from collections import Counter

WORD_LENGTH = 5

class WordleSolver():
    """A pretty good solver for beating Wordle"""

    letters = ['first', 'second', 'third', 'fourth', 'fifth']

    def __init__(self, cargs):
        self.potential_words = []
        self.frequency = None
        self.blacked_out = set()
        self.unknown_chars = {i: set() for i in range(WORD_LENGTH)}
        self.srch_str = ['[a-z]{1}'] * WORD_LENGTH
        self.dictionary = cargs.words if cargs.words else "/usr/share/dict/words"
        try:
            with open(self.dictionary, 'r', encoding='utf-8') as d:
                searcher = compile(f"^[a-z]{{{WORD_LENGTH}}}$")
                self.the_words = [line.strip() for line in d.readlines()
                                  if searcher.search(line)]
        except OSError as err:
            self.dictionary = err
        self.interactive = cargs.interactive
        self.verbose = print if cargs.verbose else lambda a, **v: None

    def __user_prompt(self, cargs):
        """Prompt the user for known letters and duds."""
        for i, l in enumerate(self.letters):
            if self.interactive:
                known = input(f"{l} known letter: ")
            else:
                known = eval(f"cargs.{l}")
            if known.startswith('!'):
                _ = [self.unknown_chars[i].add(c) for c in known[1:]]
            elif known:
                self.srch_str[i] = known
        if self.interactive:
            _ = [self.blacked_out.add(c) for c in input("Known duds: ")]
        else:
            _ = [self.blacked_out.add(c) for c in cargs.dud]

    def __letter_frequency(self):
        """Count the letters in potential words and sort by frequency."""
        potential_words = {w: Counter(w) for w in self.potential_words}
        potential_words = {k: v for k, v in sorted(potential_words.items(),
                           key=self.frequency, reverse=True)}
        self.potential_words = [k for k in potential_words]

    def __gen_frequency(self):
        """Calculate letter frequency amongst all five-letter potential
        words and create an algorithm weighing groups of letters and
        distribution.
        """

        # Count all letters across all potential words.
        letter_count = Counter()
        _ = [letter_count.update(w) for w in self.potential_words]
        self.verbose(f"letter_count: {letter_count}")

        # Group the letters by 10%. Counters are ordered by value.
        letter_groups = {i:[] for i in range(7)}
        i, rank = (0, 0)
        for letter, count in letter_count.most_common():
            if rank == 0:
                rank = count
            letter_groups.setdefault(i, [])
            if count <= int(.9*rank):
                i += 1
                rank = count
                letter_groups.setdefault(i, [])
            letter_groups[i].extend(letter)
        self.verbose(f"letter_groups: {letter_groups}")
        self.frequency = lambda c: [len(set(c[1].keys()))*8] + \
                                   [c[1][l]*7 for l in letter_groups[0]] + \
                                   [c[1][l]*6 for l in letter_groups[1]] + \
                                   [c[1][l]*5 for l in letter_groups[2]] + \
                                   [c[1][l]*4 for l in letter_groups[3]] + \
                                   [c[1][l]*3 for l in letter_groups[4]] + \
                                   [c[1][l]*2 for l in letter_groups[5]] + \
                                   [c[1][l] for l in letter_groups[6]]

    def __gen_search(self):
        for i, v in enumerate(self.srch_str):
            if not self.unknown_chars[i] and not self.blacked_out:
                continue
            if len(v) > 1:
                schars = ''.join(set.union(self.unknown_chars[i], self.blacked_out))
                self.srch_str[i] = f"(?:(?![{schars}])[a-z]){{1}}"

    def __search_dictionary(self):
        """Consult known matched characters `self.srch_str` to narrow down
        word candidates.
        """
        self.potential_words = []
        temp_str = ''.join(self.srch_str)
        tl = self.unknown_chars.values()
        rl = set([item for tl in tl for item in tl])
        required_letters = [f"(?=.*{c})" for c in rl]
        ss = f"(?:{''.join(required_letters)})^{temp_str}$" if \
                          required_letters else rf"^{temp_str}$"
        self.verbose(f"search: {ss}")
        regex = compile(ss)
        with open(self.dictionary, 'r', encoding='utf-8') as d:
            for line in d.readlines():
                word = regex.search(line)
                if word:
                    self.potential_words.append(word.group())

    def play(self, cargs=None):
        """Play the game"""
        self.__user_prompt(cargs)
        self.__gen_search()
        self.__search_dictionary()
        self.__gen_frequency()
        self.__letter_frequency()

if __name__ == "__main__":
    # Get command-line arguments
    parser = ArgumentParser(prog='wsolver.py', usage='%(prog)s [options]',
                            description="A tool to help solve Wordle.",
                            epilog="...just like that!")
    parser.add_argument('-a', '--first', type=str, default='',
                        help='1st character hint')
    parser.add_argument('-b', '--second', type=str, default='',
                        help='2nd character hint')
    parser.add_argument('-c', '--third', type=str, default='',
                        help='3rd character hint')
    parser.add_argument('-d', '--fourth', type=str, default='',
                        help='4th character hint')
    parser.add_argument('-e', '--fifth', type=str, default='',
                        help='5th character hint')
    parser.add_argument('-i', '--interactive', action='store_true',
                        help='interactive session')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='increase verbosity')
    parser.add_argument('-w', '--words', type=str, default='',
                        help='path to dictionary')
    parser.add_argument('-z', '--dud', type=str, default='',
                        help='characters not in word')
    args = parser.parse_args()

    # Create solver
    wrdl = WordleSolver(args)
    if issubclass(type(wrdl.dictionary), BaseException):
        print(wrdl.dictionary)
        exit(2)

    # Generate and display words
    wrdl.play(args)
    if not args.verbose:
        print(f"Suggestions: {", ".join([w for i, w in enumerate(wrdl.potential_words) if i < 5])}")
    else:
        print(f"Suggestions: {", ".join([w for w in wrdl.potential_words])}")
