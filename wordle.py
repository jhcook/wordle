#!/usr/bin/env python3
"""
An implementation of Wordle.
Copyright (C) 2022-2024 Justin Cook

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
from multiprocessing import cpu_count, Pool, Manager

WORD_LENGTH = 5
THE_WORDS = []
ARGUMENTS = None

class Wordle():
    """A command-line Worlde® implementation"""
    guess_lst = ['1st', '2nd', '3rd', '4th', '5th', '6th']

    def __init__(self, assistance=False, simulate=False, verbose=False,
                 first=None, word=None, **kwargs):
        self.game_word = word if word else choice(THE_WORDS)
        self.srch_str = ["[a-z]"] * WORD_LENGTH
        self.potential_words = [first] if first else []
        self.wrdl = [None] * WORD_LENGTH
        self.num_guess = 0
        self.blacked_out = set()
        self.unknown_chars = {i: set() for i in range(WORD_LENGTH)}
        self.assistance = assistance
        self.simulate = simulate
        self.verbose = print if verbose else lambda *a, **k: None
        self.suggestion = lambda x: print(f"Suggestions: {x}") if assistance and not verbose else lambda x: None
        self.quiet = False
        self.printer = lambda x: print(f"{x}") if not self.quiet else lambda x: None
        self.user_word = None
        self.frequency = None

    def __user_guess(self):
        """Prompt the user for input and increment num_guess"""
        while True:
            if self.simulate and len(self.potential_words) > 0:
                self.user_word = self.potential_words[0]
            else:
                self.user_word = input(f"Enter {self.guess_lst[self.num_guess]} word: ")
            if self.user_word == "?":
                if not self.potential_words:
                    self.__search_dictionary()
                if len(self.potential_words) < 5:
                    suggestions = self.potential_words
                else:
                    suggestions = sample(self.potential_words, 5)
                print(f'Suggestions: {", ".join(suggestions)}')
                continue
            elif len(self.user_word) != WORD_LENGTH:
                self.printer(f"Word must be {WORD_LENGTH} characters.")
                continue
            elif self.user_word not in THE_WORDS:
                self.printer("That's not a word!")
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
        _ = [self.potential_words.append(w) for w in THE_WORDS if regex.search(w)]

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
        """Enumerate through `self.user_word` and compare each character with
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
        """A single play of Wordle®"""
        while self.num_guess < len(self.guess_lst):
            # Prompt for user try
            self.__user_guess()
            # Check user's input
            self.__check_guess()
            # Print Wordle
            self.printer("".join(self.wrdl))
            if self.user_word == self.game_word.lower():
                self.printer("Good job!")
                break
            # Print suggested words
            self.__gen_frequency()
            self.__letter_frequency()
            self.verbose(f"Suggestions: {', '.join([w for w in self.potential_words])}")
            self.suggestion(", ".join([w for w in self.potential_words][:5]))
        else:
            self.printer(f"Sorry, the answer is: {self.game_word}")
            return False
        return True

def read_words():
    """Read the dictionary and set THE_WORDS."""
    global THE_WORDS
    wrds = ARGUMENTS.words if ARGUMENTS.words else "/usr/share/dict/words"
    searcher = compile(f"^[a-z]{{{WORD_LENGTH}}}$")
    try:
        with open(wrds, 'r') as f:
            _ = [THE_WORDS.append(line.strip()) for line in f.readlines()
                 if searcher.search(line)]
    except (OSError, IndexError) as err:
        print(f"Error: {err}")
        exit(1)

def worker(task):
    """Use word as first guess and simulate a playing all Wordle® words.
    Count the number of successful and unsuccessful games.
    Print the results.
    """
    firstword, words = task
    global THE_WORDS
    THE_WORDS = words
    good, bad = 0, 0
    for word in words:
        try:
            wrdl = Wordle(simulate=True, first=firstword, word=word)
            wrdl.quiet = True
            if wrdl.play():
                good += 1
            else:
                bad += 1
        except KeyboardInterrupt:
            return
    print(f"{firstword},{good},{bad}", flush=True)

def simulator():
    """Play Wordle® as a simulator.
    Iterate through the entire dictionary and play the game with each word as
    the first guess. Print out the number of success and failures for each word.
    """
    found = False
    words = []
    for word in THE_WORDS:
        if ARGUMENTS.first and not found:
            if word != ARGUMENTS.first:
                continue
            found = True
        words.append(word)

    print("word,good,bad", flush=True)

    tasks = [(firstword, words) for firstword in words]
    with Pool(processes=cpu_count()) as pool:
        pool.map(worker, tasks)

if __name__ == "__main__":
    # Get command-line arguments
    parser = ArgumentParser(prog='wordle.py', usage='%(prog)s [options]',
                            description="The game of Wordle.",
                            epilog='Use "?" in guess for suggestions')
    parser.add_argument('-a', '--assistance', action='store_true',
                        help='give word hints')
    parser.add_argument('-s', '--simulate', action='store_true',
                        help='simulate a play that needs the first guess') 
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='increase verbosity')
    parser.add_argument('-w', '--words', type=str,
                        help='path to dictionary')
    parser.add_argument('--first', type=str, default=None,
                        help='use as first guess')
    parser.add_argument('--simulator', action='store_true',
                        help='simulate playing the entire dictionary (hours/days runtime)')
    parser.add_argument('--word', type=str,
                        help='use as Wordle® word')
    ARGUMENTS = parser.parse_args()

    # Read the dictionary
    read_words()

    if ARGUMENTS.simulator:
        try:
            simulator()
        except KeyboardInterrupt:
            print("Exiting...", flush=True)
    else:
        # Create game
        wrdl = Wordle(**vars(ARGUMENTS))
        if issubclass(type(wrdl.game_word), BaseException):
            print(wrdl.game_word)
            exit(2)

        # Play game
        try:
            wrdl.play()
        except KeyboardInterrupt:
            print()
