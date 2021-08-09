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

import errno
import glob
import hashlib
import os
from pathlib import Path
import plistlib
import uuid as UUID
import vpenc

def sha1_hash(s):
  sha1 = hashlib.sha1()
  sha1.update(s.encode('utf-8'))
  return sha1.hexdigest()

class DataStore:
  def __init__(self, path, password=None):
    self.path = Path(path)
    self.encrypted = False
    self.enc_ctx = None
    self.password = password

    storeinfo_path = Path(self.path, 'storeinfo.plist')
    if not storeinfo_path.exists():
      # FIXME: Raise an error that indicates the vpdoc is invalid or corrupt.
      raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), storeinfo_path)

    properties_path = Path(self.path, 'properties.plist')
    if not properties_path.exists():
      # FIXME: Raise an error that indicates the vpdoc is invalid or corrupt.
      raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), properties_path)

    self.storeinfo = plistlib.load(open(storeinfo_path, 'rb'), fmt=plistlib.FMT_XML)

    if self.storeinfo['isEncrypted']:
      if self.password == None:
        raise Exception('Password is required for encrypted document')
      self.encrypted = True
      self.enc_ctx = vpenc.VPEncryptionContext()
      self.enc_ctx.load(self.path, self.password)
 
    if self.storeinfo['VoodooPadBundleVersion'] != 6:
      raise Exception('Unsupported')

    self.properties = self.load_plist(properties_path)

    items_path = Path(self.path, 'pages')
    if not items_path.is_dir():
      # FIXME: Raise an error that indicates the vpdoc is invalid or corrupt.
      raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), properties_path)

    self.item_plists = {}
    item_plist_paths  = items_path.rglob('*.plist')
    for item_plist_path in item_plist_paths:
      item_uuid = item_plist_path.stem
      item_plist = self.load_plist(item_plist_path)
      self.item_plists[item_uuid] = item_plist

    self.items = {}
    for item_uuid in self.item_plists.keys():
      item_plist = self.item_plist(item_uuid)

      # If the current item is an alias, then there is no file associated with
      # it.  Skip it and move on to the next item.
      if item_plist['uti'] in ['com.fm.page-alias']:
        continue

      item_path = self.item_path(item_uuid)

      if not item_path.exists():
        # FIXME: Raise an error that indicates the vpdoc is invalid or corrupt.
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), item_path)
      self.items[item_uuid] = self.load_file(item_path).decode('utf-8')

  def item_uuids(self):
    return self.item_plists.keys()

  def item(self, uuid):
    # TODO: Should item() return the underlying item (e.g., if the uuid is an
    # alias) or should it return something else?
    return self.items[uuid]

  def item_plist(self, uuid):
    return self.item_plists[uuid]

  def item_path(self, uuid):
    return Path(self.path, 'pages', uuid[0], uuid)

  def item_plist_path(self, uuid):
    return Path(self.path, 'pages', uuid[0], '{}.plist'.format(uuid))

  def validate(self):
    valid = True

    # Validate that the UUIDs match the UUIDs stored in the property lists.
    for item_uuid in self.item_uuids():
      item_plist = self.item_plist(item_uuid)
      if item_uuid != item_plist['uuid']:
        valid = False
        print('[WARN] UUID mismatch for {}'.format(item_uuid))

    # TODO: Check the default item exists.

    # TODO: Check the expected item count matches the actual item count.

    # TODO: Check that alias targets exist.

    return valid
  
  def add_item(self, name, text, format):
    item_uuid = str(UUID.uuid4())
    item_key = name.lower()

    data_hash = sha1_hash(text)

    # TODO: Add all fields.
    pl = dict(
      uuid = item_uuid,
      key = item_key,
      displayName = name,
      uti = format,
      dataHash = data_hash
    )

    item_path = Path(self.path, 'pages', item_uuid[0], item_uuid)
    plist_path = Path(self.path, 'pages', item_uuid[0], item_uuid + '.plist')

    # Save to disk
    self.save_plist(pl, plist_path)
    self.save_file(text.encode('utf-8'), item_path)

    # Keep in memory
    self.items[item_uuid] = text
    self.item_plists[item_uuid] = pl


  def load_plist(self, path):
    if self.encrypted:
      return self.enc_ctx.load_plist(path)
    else:
      return plistlib.load(open(path, 'rb'), fmt=plistlib.FMT_XML)

  def save_plist(self, plist, path):
    if self.encrypted:
      return self.enc_ctx.save_plist(plist, path)
    else:
      with open(path, 'wb') as fp:
        plistlib.dump(plist, fp)

  def load_file(self, path):
    if self.encrypted:
      return self.enc_ctx.load_file(path)
    else:
      return open(path, 'rb').read()
  
  def save_file(self, data, path):
    if self.encrypted:
      self.enc_ctx.save_file(path, data)
    else:
      with open(path, 'wb') as fp:
        fp.write(data.encode('utf-8'))
