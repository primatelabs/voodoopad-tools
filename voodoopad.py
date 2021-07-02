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
import sqlite3
import os

class VPCache:
  def __init__(self):
    self.db_path = 'cache.db'
    self.init_cache()

  def init_cache(self):

    if os.path.isfile(self.db_path):
      return

    con = sqlite3.connect(self.db_path)

    cur = con.cursor()

    # create table
    cur.execute('''create table items(uuid text, key text, displayname text)''')
    cur.execute('''create table refs(wikiword text, uuid text)''')

    con.commit()
    con.close()


  def build_cache(self, ds):

    con = sqlite3.connect(self.db_path)

    cur = con.cursor()

    uuids = ds.item_uuids()

    # Get UUID, key and display name
    # TODO: This will fail if the UUID is an alias
    for uuid in uuids:
      plist = ds.item_plist(uuid)
      key = plist['key']
      displayname = plist['displayName']

      cur.execute('insert into items values (?, ?, ?)', (uuid, key, displayname))

    # Get wikiwords and uuids
    keywords = get_wikiword_map(ds)

    for k in keywords:
      for uuid in keywords[k]:
        cur.execute('insert into refs values(?, ?)', (k, uuid))

    con.commit()


  def get_backlinks(self, uuid):

    con = sqlite3.connect(self.db_path)

    cur = con.cursor()

    # Get 
    cur.execute('select key from items where uuid = ?', (uuid,))

    row = cur.fetchone()

    if row == None:
      return None

    key = row[0]

    rows = cur.execute("select uuid from refs where wikiword = '{0}'".format(key))

    links = []
    for r in rows:
      links.append(r[0])

    return links

  def get_forwardlinks(self, uuid):
    con = sqlite3.connect(self.db_path)

    cur = con.cursor()

    # Get keywords inside this document
    cur.execute('select wikiword from refs where uuid = ?', (uuid,))

    rows = cur.fetchall()

    # TODO: Can this be replaced by an IN clause?
    links = []

    for r in rows:
      word = r[0]
      cur.execute('select uuid from items where key = ? and uuid != ?', (word, uuid))
      tmp = cur.fetchone()
      if tmp == None:
        continue
      links.append(tmp[0])
 
    return links


  def dump_tables(self):
    con = sqlite3.connect(self.db_path)

    cur = con.cursor()

    rows = cur.execute('select * from items')

    for r in rows:
      print(r)

    rows = cur.execute('select * from refs')

    for r in rows:
      print(r)


def get_wikiword_map(ds):
  keywords = {}
  for uuid in ds.item_uuids():
    p = ds.item_path(uuid)
    item = tokenizer.VPItem(uuid, p)
 
    # TODO: Is this the correct place to convert the wikiword to
    # lowercase?
    for word in item.item_keywords():
      w = word.lower()
      if w not in keywords:
        keywords[w] = []
        keywords[w].append(uuid)
      else:
        if uuid not in keywords[w]:
          keywords[w].append(uuid)

  return keywords

# Map wiki words to page UUIDs and print the result
def show_wikiwords(ds):
  keywords = get_wikiword_map(ds)

  for w in keywords:
    print(w)
    print(keywords[w])

def main():
  ds = datastore.DataStore(sys.argv[1])
  print(ds.path)
  print(ds.storeinfo)
  print(ds.properties)

  print(ds.validate())

  #show_wikiwords(ds)
  print()
  print()
  print()
  cache = VPCache()
  cache.build_cache(ds)

  uuids = ds.item_uuids()

  for uuid in uuids:
    print(uuid, 'links to:')
    print(cache.get_forwardlinks(uuid))

  for uuid in uuids:
    print(uuid, 'backlinks to:')
    print(cache.get_backlinks(uuid))

if __name__ == '__main__':
  main()

