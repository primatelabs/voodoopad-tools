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


class VPItem:
  def __init__(self, path, page_names):
    self.path = path
    self.tokens = []
    self.page_names = page_names

    text = self.read_plaintext(self.path)

    words = re.split(r"[\s\r\n;,.()-]+", text)

    # Find wikiwords
    for word in words:
      if is_wikiword(word):
        self.tokens.append(word)

    # Search for page names in this page. We are dong a 
    # case-insensitive search so convert both page
    # and names to lower-case
    text_lower = text.lower()
    names_lower = [x.lower() for x in page_names]

    # Find page names
    for i in range(len(page_names)):
      if text_lower.find(names_lower[i]) != -1:
        self.tokens.append(page_names[i])

    # Remove duplicates
    self.tokens = list(set(self.tokens))

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
