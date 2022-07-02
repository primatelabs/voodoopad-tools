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

# flake8: noqa

import argparse
import hashlib
import os
from pathlib import Path
import sqlite3
import tokenizer

import datastore


class PageFormat:
    Plaintext = 'public.utf8-plain-text'
    MarkDown = 'net.daringfireball.markdown'


class VPCache:
    def __init__(self, ds_path, in_memory=False):
        self.conn_ = None
        self.in_memory_ = in_memory
        if in_memory:
            self.db_path = ':memory:'
        else:
            self.db_path = str(Path(ds_path, 'cache.db'))

        self.init_cache()

    def get_connection(self):
        if self.conn_ is None:
            self.conn_ = sqlite3.connect(self.db_path)

        return self.conn_

    def init_cache(self):

        # If the file exists, assume the tables already exist
        if not self.in_memory_ and os.path.isfile(self.db_path):
            return

        con = self.get_connection()

        cur = con.cursor()

        # create table
        cur.execute('''create table items(uuid text, key text, displayname text, dataHash text)''')
        cur.execute('''create table refs(wikiword text, uuid text, key text)''')

        con.commit()

    def update_cache(self, ds):

        con = self.get_connection()

        cur = con.cursor()

        ds.regenerate_trie()
        uuids = ds.item_uuids()

        updated_items = []
        new_items = []

        # Go through the UUIDs and check if any are new or updated
        for uuid in uuids:
            print(uuid)
            item = ds.item_plist(uuid)
            data_hash = item['dataHash']

            cur.execute('select uuid, dataHash from items where uuid = ?', (uuid,))
            row = cur.fetchone()

            # This item does not exist. It is a new item.
            if row is None:
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
                cur.execute('insert into refs values(?, ?, ?)', (k, uuid, k.lower()))

        for uuid in new_items:
            plist = ds.item_plist(uuid)
            key = plist['key']
            displayname = plist['displayName']
            data_hash = plist['dataHash']
            cur.execute('insert into items values (?, ?, ?, ?)', (uuid, key, displayname, data_hash))

            keywords = get_wikiwords(ds, uuid)
            for k in keywords:
                cur.execute('insert into refs values(?, ?, ?)', (k, uuid, k.lower()))

        con.commit()

    def get_backlinks(self, uuid):

        con = self.get_connection()

        cur = con.cursor()

        cur.execute('select key from items where uuid = ?', (uuid,))

        row = cur.fetchone()

        if row is None:
            return None

        key = row[0]

        rows = cur.execute("select uuid from refs where key = '{0}'".format(key))

        links = []
        for r in rows:
            links.append(r[0])

        return links

    def get_forwardlinks(self, uuid):
        con = self.get_connection()

        cur = con.cursor()

        # Get keywords inside this document
        cur.execute('select key from refs where uuid = ?', (uuid,))

        rows = cur.fetchall()

        # TODO: Can this be replaced by an IN clause?
        links = []

        for r in rows:
            key = r[0]
            cur.execute('select uuid from items where key = ? and uuid != ?', (key, uuid))
            tmp = cur.fetchone()
            if tmp is None:
                continue
            links.append(tmp[0])

        return links

    # Get the keywords that appear in the document with the given UUID
    def get_links(self, uuid):

        con = self.get_connection()

        cur = con.cursor()

        cur.execute('select key, wikiword from refs where uuid = ?', (uuid,))
        rows = cur.fetchall()

        links = {}
        for r in rows:
            key = r[0]
            word = r[1]
            links[key] = word

        return links

    # Dump tables contents to stdout
    def dump_tables(self):
        con = self.get_connection()

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
    text = ds.item(uuid)
    item = tokenizer.VPItem(text, ds.trie)

    return item.item_keywords()


# Map wiki words to page UUIDs and print the result
def show_wikiwords(ds):
    keywords = get_wikiword_map(ds)

    for w in keywords:
        print(w)
        print(keywords[w])


class VoodooPad:
    ds_ = None
    cache_ = None
    path_ = None
    password_ = None

    def __init__(self, document_path=None, password=None, in_memory=False):
        self.path_ = document_path
        self.password_ = password
        self.in_memory_ = in_memory

        if self.path_ is not None:
            self.ds_ = datastore.DataStore.open(self.path_, password, in_memory)
            self.cache_ = VPCache(self.path_, self.in_memory_)
            self.cache_.update_cache(self.ds_)

    def sha1_hash(self, s):
        sha1 = hashlib.sha1()
        sha1.update(s.encode('utf-8'))
        return sha1.hexdigest()

    # Returns a markdown link with the given text and URL
    def markdown_link(self, text, url):
        return '[{0}]({1})'.format(text, url)

    # Determines if an index is inside a markdown link
    def in_markdown_link(self, text, idx):
        size = 64

        left_paren = text.find('(', max(idx - size, 0), idx)
        right_paren = text.find(')', idx, min(idx + size, len(text) - 1))

        left_bracket = text.find('[', max(idx - size, 0), idx)
        right_bracket = text.find(']', idx, min(idx + size, len(text) - 1))

        if left_bracket != -1 and right_bracket != -1:
            if text[right_bracket + 1] == '(':
                return True

        if left_paren != -1 and right_paren != -1:
            if text[left_paren - 1] == ']':
                return True

        return False

    # Convert the page to markdown
    def render_page(self, ds, cache, uuid):  # noqa: C901

        # p = ds.item_path(uuid)

        plist = ds.item_plist(uuid)

        page_key = plist['key']

        text = ds.item(uuid)

        links = cache.get_links(uuid)

        # We are doing a case-insensitive search. Convert the text to lower case.
        text_lower = text.lower()
        indexes = {}

        # Locate the keywords in the text and store the index
        for key in links:
            idx = 0

            # Do not link this document to itself
            if key == page_key:
                continue

            while True:
                idx = text_lower.find(key, idx)
                if idx == -1:
                    break

                # If the word is a markdown link target and it's the only thing in the link target, then we
                # want to replace the link target with the file name e.g. [Napoleon](Napoleon) becomes
                # [Napoleon](Napoleon.md)
                if idx >= 2 and idx + len(key) < len(text) and text[idx - 1] == '(' and text[idx + len(key)] == ')' and text[idx - 2] == ']':
                    indexes[idx] = key
                    idx = idx + len(key)
                    continue

                # Ignore if it's part of a bigger word but accept if its surrounded by punctuation.
                # TODO: Is there a better way to do this?
                if (idx != 0 and text[idx - 1] not in [' ','\n', '\r']) or (idx + len(key) < len(text) and text[idx + len(key)] not in [' ', '.', ',','\n', '\r']):
                    idx = idx + len(key)
                    continue

                # Ignore if already inside a markdown link
                if self.in_markdown_link(text, idx):
                    idx = idx + len(key)
                    continue

                indexes[idx] = key
                idx = idx + len(key)

        # Nothing to do if no keywords were found
        if len(indexes) == 0:
            return text

        # Replacing keywords will change the length of the text and change the positions of the
        # other keywords. Sort the indexes so that we can do a single scan over the text and
        # replace keywords as they appear, keeping track of the change in position.
        sorted_keys = list(indexes.keys())
        sorted_keys.sort()

        sorted_indexes = []

        for k in sorted_indexes:
            sorted_indexes.append({'index': k, 'key': indexes[k]})

        offset = 0
        for s in sorted_indexes:

            idx = s['index']
            key = s['key']

            if text[idx + offset - 1] == '(' and text[idx + offset + len(key)] == ')' and text[idx + offset - 2] == ']':
                # Replace link inside of a markdown link
                replacement = links[key] + '.md'
                text = text[:idx + offset] + links[key] + '.md' + text[idx + offset + len(key):]
                offset = offset + len(replacement) - len(key)
            else:
                # Add a markdown link
                word = text[idx + offset:idx + offset + len(key)]
                markdown = self.markdown_link(word, links[key] + '.md')
                text = text[:idx + offset] + markdown + text[idx + offset + len(key):]
                offset = offset + len(markdown) - len(key)

        return text

    def render_document(self, output_dir):

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        for uuid in self.ds_.item_uuids():
            plist = self.ds_.item_plist(uuid)
            display_name = plist['displayName']
            text = self.render_page(self.ds_, self.cache_, uuid)
            filename = output_dir + '/{0}.md'.format(display_name)
            with open(filename, 'w') as f:
                f.write(text)

    def render_doc(self):
        self.cache_.update_cache(self.ds_)

        pages = []
        for uuid in self.ds_.item_uuids():
            plist = self.ds_.item_plist(uuid)
            display_name = plist['displayName']
            text = self.render_page(self.ds_, self.cache_, uuid)

            pages.append({'display_name': display_name, 'text': text})

        return pages

    def add_item(self, ds, name, text, format=PageFormat.Plaintext):
        for item in self.ds_.item_plists.values():
            if item['displayName'].lower() == name.lower():
                print('A page with that name already exists')
                return

        self.ds_.add_item(name, text, format)

    def render(self, output_dir):
        self.cache_.update_cache(self.ds_)
        self.render_document(output_dir)

    def print_info(self):
        print('Path: {}'.format(self.ds_.path))
        print('Info: {}'.format(self.ds_.storeinfo))
        print('Properties: {}'.format(self.ds_.properties))

        print('Valid: {}'.format(self.ds_.validate()))
        uuids = self.ds_.item_uuids()

        for uuid in uuids:
            print(self.ds_.item_plist(uuid)['displayName'], 'links to:')
            for id in self.cache_.get_forwardlinks(uuid):
                print(id, self.ds_.item_plist(id)['displayName'])

        for uuid in uuids:
            print(self.ds_.item_plist(uuid)['displayName'], ' backlinks to:')
            for id in self.cache_.get_backlinks(uuid):
                print(id, self.ds_.item_plist(id)['displayName'])

    def add_file(self, path, name, format):
        with open(path, 'rb') as f:
            text = f.read().decode('utf-8')

        self.add(text, name, format)

    def add(self, text, name, format):
        if format == 'plaintext':
            format = PageFormat.Plaintext
        elif format == 'markdown':
            format = PageFormat.MarkDown
        else:
            print('Invalid format ', format)
            return

        self.add_item(self.ds_, name, text, format)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('document', help='document')
    parser.add_argument('command', nargs='?', default=None, help='command')
    parser.add_argument('--file', help='file')
    parser.add_argument('--format', default='plaintext', help='format')
    parser.add_argument('--output', default=None, help='output')
    parser.add_argument('--password', help='password')
    parser.add_argument('--title', help='title')

    args = parser.parse_args()
    print(args)

    if args.command == 'create':
        datastore.DataStore.create(args.document)
        return

    vp = VoodooPad(None, None)
    vp.ds_ = datastore.DataStore.open(args.document, args.password)
    vp.cache_ = VPCache(args.document, True)
    vp.cache_.update_cache(vp.ds_)

    if args.command is None:
        vp.print_info()
    elif args.command == 'add':
        vp.add_file(args.file, args.title, args.format)
    elif args.command == 'render':
        vp.render(args.output)
    else:
        print(f'Unknown command \'{args.command}\'')


if __name__ == '__main__':
    main()
