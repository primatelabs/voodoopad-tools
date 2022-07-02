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


from pathlib import Path
import os
import sys

import vpenc


def main():

    if len(sys.argv) != 3:
        print('Usage: <password> <encrypted VP document>')
        return

    password = sys.argv[1]
    vp_path = sys.argv[2]

    ctx = vpenc.VPEncryptionContext()
    ctx.load(vp_path, password)

    items_path = Path(vp_path, 'pages')
    items_plist_paths = items_path.rglob('*.plist')
    for items_plist_path in items_plist_paths:
        print(items_plist_path)
        item_path = os.path.relpath(items_plist_path, vp_path)
        data_path = os.path.splitext(item_path)[0]

        info = ctx.load_plist(item_path)
        print(info)
        data = ctx.load_file(data_path)
        print(data)


if __name__ == '__main__':
    main()
