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
import uuid as UUID
import plistlib
from pathlib import Path
import hashlib

class VPCache:
  def __init__(self, ds_path):
    self.db_path = str(Path(ds_path, 'cache.db'))
    self.init_cache()

  def init_cache(self):

    # If the file exists, assume the tables already exist
    if os.path.isfile(self.db_path):
      return

    con = sqlite3.connect(self.db_path)

    cur = con.cursor()

    # create table
    cur.execute('''create table items(uuid text, key text, displayname text, dataHash text)''')
    cur.execute('''create table refs(wikiword text, uuid text)''')

    con.commit()
    con.close()

  '''
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
      data_hash = plist['dataHash']
      cur.execute('insert into items values (?, ?, ?, ?)', (uuid, key, displayname, data_hash))

    # Get wikiwords and uuids
    keywords = get_wikiword_map(ds)

    for k in keywords:
      for uuid in keywords[k]:
        cur.execute('insert into refs values(?, ?)', (k, uuid))

    con.commit()
  '''

  def update_cache(self, ds):
    con = sqlite3.connect(self.db_path)

    cur = con.cursor()

    uuids = ds.item_uuids()

    updated_items = []
    new_items = []

    # Go through the UUIDs and check if any are new or updated
    for uuid in uuids:
      item = ds.item_plist(uuid)
      data_hash = item['dataHash']

      cur.execute('select uuid, dataHash from items where uuid = ?', (uuid,))
      row = cur.fetchone()

      # This item does not exist. It is a new item.
      if row == None:
        new_items.append(uuid)
        continue

      # This item was updated
      if row[1] != data_hash:
        updated_items.append(uuid)

    if len(updated_items) == 0 and len(new_items) == 0:
      return

    # Delete keywords for updated items.
    for uuid in updated_items:
      cur.execute('delete from refs where uuid = ?', (uuid,))

    for uuid in updated_items:
      keywords = get_wikiwords(ds, uuid)
      for k in keywords:
        cur.execute('insert into refs values(?, ?)', (k, uuid))

    for uuid in new_items:
      plist = ds.item_plist(uuid)
      key = plist['key']
      displayname = plist['displayName']
      data_hash = plist['dataHash']
      cur.execute('insert into items values (?, ?, ?, ?)', (uuid, key, displayname, data_hash))

      keywords = get_wikiwords(ds, uuid)
      for k in keywords:
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
    #p = ds.item_path(uuid)
 
    words = get_wikiwords(ds, uuid)

    for w in words:
      if w not in keywords:
        keywords[w] = []
        keywords[w].append(uuid)
      else:
        keywords[w].append(uuid)

  return keywords

def get_page_names(ds):
  names = []
  for uuid in ds.item_uuids():
    item = ds.item_plist(uuid)
    names.append(item['displayName'])
  
  return names

# Returns an array of wikiwords in the document
def get_wikiwords(ds, uuid):
  keywords = []

  page_names = get_page_names(ds)

  p = ds.item_path(uuid)
  item = tokenizer.VPItem(p, page_names)

  # TODO: Is this the correct place to convert the wikiword to
  # lowercase?
  for word in item.item_keywords():
    w = word.lower()
    if w not in keywords:
      keywords.append(w)

  return keywords

# Map wiki words to page UUIDs and print the result
def show_wikiwords(ds):
  keywords = get_wikiword_map(ds)

  for w in keywords:
    print(w)
    print(keywords[w])

def sha1_hash(s):
  sha1 = hashlib.sha1()
  sha1.update(s.encode('utf-8'))
  return sha1.hexdigest()


def add_item(store_path, name, text):

  item_uuid = str(UUID.uuid4())

  item_path = Path(store_path, 'pages', item_uuid[0], item_uuid)
  plist_path = Path(store_path, 'pages', item_uuid[0], item_uuid + '.plist')

  item_key = name.lower()

  data_hash = sha1_hash(text)

  pl = dict(
    uuid = item_uuid,
    key = item_key,
    displayName = name,
    uti = 'public.utf8-plain-text',
    dataHash = data_hash
  )

  with open(plist_path, 'wb') as fp:
    plistlib.dump(pl, fp)

  with open(item_path, 'wb') as fp:
    fp.write(text.encode('utf-8'))


def main():
  cmd = ''

  if len(sys.argv) < 1:
    print('usage: voodoopad.py document [command]')
    exit(1)
  
  if len(sys.argv) >= 3:
    cmd = sys.argv[2]

  ds = datastore.DataStore(sys.argv[1])

  # Update the cache and dump information about the document
  if cmd == '':

    print(ds.path)
    print(ds.storeinfo)
    print(ds.properties)

    print(ds.validate())

    cache = VPCache(sys.argv[1])
    cache.update_cache(ds)

    #cache.dump_tables()

    uuids = ds.item_uuids()

    for uuid in uuids:
      print(ds.item_plist(uuid)['displayName'], 'links to:')
      for id in cache.get_forwardlinks(uuid):
        print(id, ds.item_plist(id)['displayName'])

    for uuid in uuids:
      print(ds.item_plist(uuid)['displayName'], ' backlinks to:')
      for id in cache.get_backlinks(uuid):
        print(id, ds.item_plist(id)['displayName'])

  # Add a page to the document
  elif cmd == 'add':

    text_file = sys.argv[3]
    name = sys.argv[4]
    with open(sys.argv[3], 'rb') as f:
      text = f.read().decode('utf-8')
      add_item(sys.argv[1], name, text)

  else:

    print('Unknown command')

if __name__ == '__main__':
  main()

