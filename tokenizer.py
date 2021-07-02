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

class Tokenizer:
  def __init__(self, s):
    self.source = s
    self.idx = 0

  def is_break(self, c):
    b = [' ', '\r', '\n', ';', ',', '.']

    return c in b
 
  # Returns the next token, or the empty string if there are no tokens
  # remaining
  def next_token(self):
    in_word = False
    word_start = 0
    word_len = 0

    while True:

      # At the end of the string?
      if self.idx == len(self.source):
        if in_word:
          return self.source[word_start:word_start + word_len]
        else:
          return ''

      # Encountered a separator?
      if self.is_break(self.source[self.idx]):
        if in_word:
          return self.source[word_start:word_start + word_len]
        else:
          self.idx = self.idx + 1
          continue

      # Start of a word? 
      if not in_word:
        in_word = True
        word_start = self.idx
        word_len = 1
      else:
        word_len = word_len + 1
      
      self.idx = self.idx + 1

def is_wikiword(word):

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


class VPItem:
  def __init__(self, uuid, path):
    self.uuid = uuid
    self.path = path
    self.wikiwords = []

    text = self.read_plaintext(self.path)

    t = Tokenizer(text)
    
    while True:
      word = t.next_token()
      if word == '':
        break

      if is_wikiword(word):
        self.wikiwords.append(word)
  
  def item_uuid(self):
    return self.uuid
  
  def item_keywords(self):
    return self.wikiwords
  
  def read_plaintext(self, path):

    try:
      f = open(path, 'r')
      s = f.read()
    except UnicodeDecodeError as e:
      print('Warning: ', self.uuid, 'is not UTF-8')
      s = ''

    return s
