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

import argparse
import json
import os
import pprint
import re
import subprocess
import sys
import tempfile
import unicodedata
import urllib.parse
import xml.etree.ElementTree as ET

from markdown_it import MarkdownIt
from markdown_it.renderer import RendererProtocol
import pandoc
import requests


def slugify(value):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    value = unicodedata.normalize('NFKC', value)
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


class Article:
    def __init__(self, title, text):
        self.title = title
        self.text = text

    @classmethod
    def download(klass, name):
        r = requests.get(f'https://en.wikipedia.org/wiki/Special:Export/{name}')
        if r.status_code != 200:
            return None

        ns = {
            'export': 'http://www.mediawiki.org/xml/export-0.10/'
        }

        root = ET.fromstring(r.text)

        nodes = root.findall("export:page/export:title", ns)
        title = nodes[0].text

        nodes = root.findall("export:page/export:revision/export:text", ns)
        text = nodes[0].text

        return klass(title, text)

    def markdown(self):
        document = pandoc.read(self.text, format="mediawiki")
        return pandoc.write(document, format="gfm")

    def __links(self, tokens, links):
        for token in tokens:
            if token.type == 'link_open':
                links.append(token.attrs['href'])
            if token.children != None:
                links = self.__links(token.children, links)
        return links

    def links(self):
        md = MarkdownIt("commonmark")
        tokens = md.parse(self.markdown())
        return self.__links(tokens, [])

    def to_json(self):
        return json.dumps({
            'title': self.title,
            'text': self.text,
            'markdown': self.markdown()
        }, indent=4)


def download_article(article_name, output_dir, crawl_depth):
    print(f'download {article_name} {crawl_depth}')

    article = Article.download(article_name)

    article_filename = f'{slugify(article.title)}.json'
    article_path = os.path.join(output_dir, article_filename)

    if os.path.exists(article_path):
        return

    with open(article_path, 'w') as f:
        f.write(article.to_json())

    if crawl_depth > 0:
        links = article.links()
        for link in links:
            url = urllib.parse.urlparse(link)
            if not url.scheme and not url.netloc:
                print(url.path)
                try:
                    download_article(url.path, output_dir, crawl_depth - 1)
                except:
                    print(f'error {url.path}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('article', help='article')
    parser.add_argument('output', help='output')
    parser.add_argument('--crawl-depth', type=int, default=0, help='crawl depth')

    args = parser.parse_args()
    print(args)

    try:
        os.mkdir(args.output)
    except FileExistsError:
        pass

    download_article(args.article, args.output, args.crawl_depth)


if __name__ == '__main__':
    main()
