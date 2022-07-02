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

import json
import argparse
import glob
import os
import subprocess
import sys

parent = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent)

import datastore
import voodoopad

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('document', help='document')
    parser.add_argument('directory', help='directory')

    args = parser.parse_args()
    print(args)

    if not os.path.exists(args.document):
        datastore.DataStore.create(args.document)

    vp = voodoopad.VoodooPad(args.document)

    for file in glob.glob(f'{args.directory}/*.json'):
        with open(file, 'r') as f:
            article = json.loads(f.read())
            vp.add(article['markdown'], article['title'], 'markdown')

    vp.cache_.update_cache(vp.ds_)


if __name__ == '__main__':
    main()
