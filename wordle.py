#!/usr/bin/env python3
"""
An implementation of Wordle.
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
from random import choice, sample

WORD_LENGTH = 5

class Wordle():
    """A command-line Worlde® implementation"""
    guess_lst = ['1st', '2nd', '3rd', '4th', '5th', '6th']

    def __init__(self, words=None, assistance=False, verbose=False):
        # Get a word six characters in length
        self.dictionary = words if words else "/usr/share/dict/words"
        try:
            with open(self.dictionary, 'r', encoding='utf-8') as d:
                searcher = compile(f"^[a-z]{{{WORD_LENGTH}}}$")
                self.the_words = [line.strip() for line in d.readlines()
                                  if searcher.search(line)]
                self.game_word = choice(self.the_words)
        except (OSError, IndexError) as err:
            self.game_word = err
        self.srch_str = ["[a-z]"] * WORD_LENGTH
        self.potential_words = []
        self.wrdl = [None] * WORD_LENGTH
        self.num_guess = 0
        self.blacked_out = set()
        self.unknown_chars = {i: set() for i in range(WORD_LENGTH)}
        self.assistance = assistance
        self.verbose = print if verbose else lambda *a, **k: None
        self.suggestion = lambda x: print(f"Suggestions: {x}") if assistance and not verbose else lambda x: None
        self.user_word = None
        self.frequency = None

    def __user_guess(self):
        """Prompt the user for input and increment num_guess"""
        while True:
            self.user_word = input(f"Enter {self.guess_lst[self.num_guess]} word: ")
            if self.user_word == "?":
                if not self.potential_words:
                    self.__search_dictionary()
                if len(self.potential_words) < 5:
                    suggestions = self.potential_words
                else:
                    suggestions = sample(self.potential_words, 5)
                print(f"Suggestions: {", ".join(suggestions)}")
                continue
            elif len(self.user_word) != WORD_LENGTH:
                print(f"Word must be {WORD_LENGTH} characters.")
                continue
            elif self.user_word not in self.the_words:
                print("That's not a word!")
                continue
            self.num_guess += 1
            break

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
            self.verbose(f"known strays: {required_letters}")
            for line in d.readlines():
                word = regex.search(line)
                if word:
                    self.potential_words.append(word.group())

    def __gen_frequency(self):
        """Calculate letter frequency amost all five-letter words in the
        dictionary and create an algorithm weighing groups of letters and
        distribution.
        """
        # Count all letters across all words in the dictionary.
        letter_count = Counter()
        _ = [letter_count.update(w) for w in self.potential_words]
        self.verbose(f"letter count: {letter_count}")

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

    def __letter_frequency(self):
        """Create a dictionary of words with 'word': Counter('word') as k, v.
        Sort the dictionary weighing groups of letters by frequency of
        occurance in the group and distribution of letters in the word.
        Set `self.potential_words` as the sorted list.

        TODO: the algorithm should be calculated based on the dictionary used
        """
        potential_words = {w: Counter(w) for w in self.potential_words}
        potential_words = {k: v for k, v in sorted(potential_words.items(),
                           key=self.frequency, reverse=True)}
        self.potential_words = [k for k in potential_words]

    def __check_guess(self):
        self.__gen_wordle()
        self.__gen_search()
        self.__search_dictionary()

    def __gen_wordle(self):
        """Enumerate through `self.user_word` anc compare each character with
        `self.game_word`. Update `self.wrdl` with the appropriate character and
        recreate the search string based on the results."""
        for i, v in enumerate(self.user_word):
            if self.game_word[i].lower() == v:
                self.wrdl[i] = f"\033[1;42m {v.upper()} \033[m"
                self.srch_str[i] = v
            elif v in self.game_word:
                self.wrdl[i] = f"\033[1;43m {v.upper()} \033[m"
                self.unknown_chars[i].add(v)
            else:
                self.wrdl[i] = f"\033[1;30m {v.upper()} \033[m"
                self.blacked_out.add(v)

    def __gen_search(self):
        """Generate a list of search strings injecting the unknown characters
        and blacked out characters in the regex for each position.
        """
        for i, v in enumerate(self.srch_str):
            if not self.unknown_chars[i] and not self.blacked_out:
                continue
            if len(v) > 1:
                schars = ''.join(set.union(self.unknown_chars[i], self.blacked_out))
                self.srch_str[i] = f"(?:(?![{schars}])[a-z]){{1}}"

    def play(self):
        """Play Wordle"""
        while self.num_guess < len(self.guess_lst):
            # Prompt for user try
            self.__user_guess()
            # Check user's input
            self.__check_guess()
            # Print Wordle
            print("".join(self.wrdl))
            if self.user_word == self.game_word.lower():
                print("Good job!")
                break
            # Print suggested words
            self.__gen_frequency()
            self.__letter_frequency()
            self.verbose(f"Suggestions: {', '.join([w for w in self.potential_words])}")
            self.suggestion(", ".join([w for w in self.potential_words][:5]))
        else:
            print(f"Sorry, the answer is: {self.game_word}")

if __name__ == "__main__":
    # Get command-line arguments
    parser = ArgumentParser(prog='wordle.py', usage='%(prog)s [options]',
                            description="The game of Wordle.",
                            epilog='Use "?" in guess for suggestions')
    parser.add_argument('-a', '--assistance', action='store_true',
                        help='give word hints')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='increase verbosity')
    parser.add_argument('-w', '--words', type=str,
                        help='path to dictionary')
    args = parser.parse_args()

    # Create game
    wrdl = Wordle(**vars(args))
    if issubclass(type(wrdl.game_word), BaseException):
        print(wrdl.game_word)
        exit(2)

    # Play game
    try:
        wrdl.play()
    except KeyboardInterrupt:
        print()
