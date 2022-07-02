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

import re
import sys


# Parses a link and moves the index forward
# Returns link_text, link_target
def parse_link(markdown_link, start=0):

    if start == -1:
        start = 0

    if start >= len(markdown_link):
        return None

    if markdown_link[start] != '[':
        return None

    if markdown_link[start + 1] == '[':
        return None

    # Find the ending bracket
    count = 0
    while True:
        if start + count >= len(markdown_link):
            return None

        count = count + 1
        if markdown_link[start + count] == ']':
            break
        elif count == len(markdown_link):
            return None

    link_text = markdown_link[start + 1:start + count]

    if start + count + 1 >= len(markdown_link):
        return None

    # Assume no space between bracket and parenthesis
    if markdown_link[start + count + 1] != '(':
        return None

    # Assume link cannot be empty
    if markdown_link[start + count + 2] == ')':
        return None

    # Ignore Wikipedia category links
    # TODO: Should these be somewhere else?
    category = '/Category:'
    if markdown_link.find(category, start + count + 1, start + count + 1 + len(category) + 1) != -1:
        return None

    file = '/File:'
    if markdown_link.find(file, start + count + 1, start + count + 1 + len(file) + 1) != -1:
        return None

    commons = '/commons:'
    if markdown_link.find(commons, start + count + 1, start + count + 1 + len(commons) + 1) != -1:
        return None

    fragment = '/#'
    if markdown_link.find(fragment, start + count + 1, start + count + 1 + len(fragment) + 1) != -1:
        return None

    # Find ending parenthesis
    open_count = 0
    end_idx = start + count + 1
    while True:
        if end_idx >= len(markdown_link):
            return None

        end_idx = end_idx + 1

        # Can have parenthesis inside parenthesis e.g. wikipedia links
        c = markdown_link[end_idx]

        if c == '(':
            open_count = open_count + 1
        elif c == ')':
            if open_count == 0:
                break
            open_count = open_count - 1
        elif c == '|' or c == '?' or c == '[' or c == ']':
            return None

    link_target = markdown_link[(start + count + 2):end_idx]

    link_size = end_idx + 1 - start

    return link_text, link_target, link_size


def is_wikilink(text):
    return text.find('"wikilink"') != -1


# Convert a WikiLink to a markdown link
def convert_link(text):

    # Remove "wikilink"
    text = text.replace('"wikilink"', '')

    # Strip spaces
    text = text.strip(' ')

    # Remove forward slash

    if text[0] == '/':
        text = text[1:]

    # Replace brackets with underscores
    text = text.replace('(', '_')
    text = text.replace(')', '_')

    # Replace spaces with underscores
    text = text.replace(' ', '_')
    text = text.strip('_')

    # Remove any double underscores
    text = text.replace('__', '_')

    # Remove commas
    text = text.replace(',', '')

    # Remove non-alphanumeric characters
    text = re.sub(r'\W+', '', text)

    return text


def parse_wikilink(text):
    text = text.replace('"wikilink"', '')
    text = text.rstrip(' ')

    if text[0] == '/':
        text = text[1:]

    return text


def make_link(text, url):
    return '[{0}]({1})'.format(text, url)


def convert_article(text):
    new_text = ''
    idx = 0
    old_idx = 0

    while True:
        if idx >= len(text):
            break

        if text[idx] == '[':

            # Possible link
            link = parse_link(text, idx)

            if link is None:
                idx = idx + 1
                continue

            link_text = link[0]
            url = link[1]
            size = link[2]

            url = convert_link(url)

            new_text = new_text + text[old_idx:idx] + make_link(link_text, url)
            old_idx = idx + size
            idx = idx + size
        else:
            idx = idx + 1

    return new_text


def get_links(text):
    new_text = ''
    idx = 0
    old_idx = 0
    urls = []

    while True:
        if idx >= len(text):
            break

        if text[idx] == '[':
            count = 1
            while True:
                if text[idx + count] == '[':
                    count = count + 1
                else:
                    break

            if count > 1:
                idx = idx + count
                continue

            # Possible link
            link = parse_link(text, idx)

            if link is None:
                idx = idx + 1
                continue

            link_text = link[0]
            url = link[1]
            size = link[2]

            # print if its a wikilink
            if is_wikilink(url):
                url = parse_wikilink(url)
                urls.append(url)

            idx = idx + size
        else:
            idx = idx + 1

    return urls


def main():
    cmd = sys.argv[1]

    if cmd == 'convert':

        filename = sys.argv[2]
        lines = []
        with open(filename, 'rb') as f:
            text = f.read().decode('utf-8')

        new_text = convert_article(text)
        print(new_text)
    elif cmd == 'get-links':

        filename = sys.argv[2]
        lines = []
        with open(filename, 'rb') as f:
            text = f.read().decode('utf-8')

        links = get_links(text)
        for l in links:
            print(l)

    elif cmd == 'sanitize-link':
        link = sys.argv[2]

        print(convert_link(link))

    else:
        print('Invalid command')

if __name__ == '__main__':
    main()
