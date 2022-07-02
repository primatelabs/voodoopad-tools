#!/usr/bin/env python3

# Copyright (c) 2004-2022 Primate Labs Inc.
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

import unittest

from wordtrie import WordTrie
from tokenizer import tokenize_text, VPItem


class TokenizerTest(unittest.TestCase):
    def links(self, trie, text, expected):
        item = VPItem(text, trie)

        keywords = set(item.item_keywords())
        expected = set(expected)

        self.assertTrue(keywords == expected)

    def test_smoke(self):
        names = [
            'atari',
            'atari st',
            'atari falcon',
            'apple',
            'video game',
            'video game crash of 1983',
        ]

        trie = WordTrie()
        for name in names:
            trie.add(tokenize_text(name.lower()))

        text = 'the atari falcon was not as popular as the atari st'
        expected = ['atari falcon', 'atari st']
        self.links(trie, text, expected)

        text = 'atari made the atari falcon and the atari st'
        expected = ['atari', 'atari falcon', 'atari st']
        self.links(trie, text, expected)

        text = 'atari made the atari falcon and the atari st computers'
        expected = ['atari', 'atari falcon', 'atari st']
        self.links(trie, text, expected)
