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

class WordTrieBranch:
    def __init__(self):
        self.words = 0
        self.prefixes = 0
        self.branches = {}

    def query(self, words):
        branch = self
        for word in words:
            if word not in branch.branches:
                return None
            else:
                branch = branch.branches[word]
        return branch

    def query_word(self, word):
        if word not in self.branches:
            return None
        else:
            return self.branches[word]


class WordTrie:
    def __init__(self):
        self.root = WordTrieBranch()

    def __add(self, words, branch):
        if words:
            branch.prefixes += 1
            word = words[0]
            if word not in branch.branches:
                branch.branches[word] = WordTrieBranch()
            self.__add(words[1:], branch.branches[word])
        else:
            branch.words += 1

    def add(self, words):
        self.__add(words, self.root)

    def query(self, words):
        return self.root.query(words)

    def query_word(self, word):
        return self.root.query_word(word)
