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


class WordTrieTest(unittest.TestCase):
    def test_smoke(self):
        trie = WordTrie()

        trie.add(['hello', 'there'])
        branch = trie.query(['hello'])
        self.assertIsNotNone(branch)
        self.assertEqual(branch.words, 0)
        self.assertEqual(branch.prefixes, 1)

        trie.add(['hello', 'world'])
        branch = trie.query(['hello'])
        self.assertIsNotNone(branch)
        self.assertEqual(branch.words, 0)
        self.assertEqual(branch.prefixes, 2)

        trie.add(['hello'])
        branch = trie.query(['hello'])
        self.assertIsNotNone(branch)
        self.assertEqual(branch.words, 1)
        self.assertEqual(branch.prefixes, 2)

        trie.add(['wombat', 'hello'])
        branch = trie.query(['hello'])
        self.assertIsNotNone(branch)
        self.assertEqual(branch.words, 1)
        self.assertEqual(branch.prefixes, 2)

        branch = trie.query(['hello', 'world'])
        self.assertIsNotNone(branch)
        self.assertEqual(branch.words, 1)
        self.assertEqual(branch.prefixes, 0)

        branch = trie.query(['koala'])
        self.assertIsNone(branch)
