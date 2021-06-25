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

import sys

import datastore
import tokenizer

# Map wiki words to page UUIDs and print the result
def show_wikiwords(ds):
  keywords = {}
  for uuid in ds.item_uuids():
    p = ds.item_path(uuid)
    item = tokenizer.VPItem(uuid, p)
 
    for word in item.item_keywords():
      if word not in keywords:
        keywords[word] = []
        keywords[word].append(uuid)
      else:
        if uuid not in keywords[word]:
          keywords[word].append(uuid)

  for w in keywords:
    print(w)
    print(keywords[w])

def main():
  ds = datastore.DataStore(sys.argv[1])
  print(ds.path)
  print(ds.storeinfo)
  print(ds.properties)

  print(ds.validate())

  show_wikiwords(ds)

if __name__ == '__main__':
  main()

