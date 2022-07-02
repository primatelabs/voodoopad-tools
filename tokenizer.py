#!/usr/bin/env python3

# Copyright (c) 2004-2021 Primate Labs Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import re

from wordtrie import WordTrie

def is_wikiword(word):

    # Must be alphanumeric
    if not word.isalnum():
        return False

    # Must start with upper-case character
    if not word[0].isupper():
        return False

    # Must contain at least 1 lower-case chacter followed
    # by at least 1 upper-case character
    has_lower = False
    for i in range(1, len(word)):

        if word[i].islower():
            has_lower = True

        if word[i].isupper() and has_lower:
            return True

    return False


def tokenize_text(text):
    return re.split(r"[\s\r\n;,.()-]+", text)


def lookup_name(words, start, trie):
    best = None

    current_branch = trie
    next_branch = None

    for i in range(start, len(words)):
        next_branch = current_branch.query_word(words[i])
        if next_branch is None:
            break
        if next_branch.words > 0:
            best = i
        current_branch = next_branch

    if best is None:
        return None

    return words[start:(best + 1)]


class VPItem:
    def __init__(self, text, trie):
        self.tokens = []

        words = tokenize_text(text)

        self.find_wikiwords(words)

        words = tokenize_text(text.lower())

        for i in range(len(words)):
            # Check to see if the current word is at the root of the trie.
            branch = trie.query_word(words[i])
            if branch is None:
                continue
            else:
                match = lookup_name(words, i, trie)
                if match:
                    self.tokens.append(' '.join(match))

        # Remove duplicates
        self.tokens = list(set(self.tokens))


    def find_wikiwords(self, words):
        for word in words:
            if is_wikiword(word):
                self.tokens.append(word)


    def item_keywords(self):
        return self.tokens


    def read_plaintext(self, path):
        try:
            f = open(path, 'r')
            s = f.read()
        except UnicodeDecodeError as e:
            print('Warning: ', self.uuid, 'is not UTF-8')
            s = ''

        return s
