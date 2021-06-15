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
import sys

import hkdf
import hashlib
import hmac
from math import ceil

from Crypto.Cipher import AES

# Decryption functions
def hmac_sha256(key, data):
  return hmac.new(key, data, hashlib.sha256).digest()

def hkdf_sha256(key, salt, info, length):
  kdf = hkdf.Hkdf(salt, key, hash=hashlib.sha256)
  return kdf.expand(info, length)

def pbkdf_sha512(password, salt, iterations):
  return hashlib.pbkdf2_hmac('sha512', bytes(password, 'utf-8'), salt, iterations)

def unpad_pkcs7(data):
  padding_byte = data[-1]
  count = int(padding_byte)
  return data[:-count]

def aes_cbc_decrypt(iv, key, ciphertext):
  cipher = AES.new(key, AES.MODE_CBC, iv)
  return cipher.decrypt(ciphertext)

def aead_decrypt(enc_key, hmac_key, payload):
  iv = payload[0:16]
  auth_token = payload[-32:]

  # Skip the associated_data size
  assoc_data_len = int.from_bytes(payload[16:18], 'little')

  if (assoc_data_len != 0):
    raise Exception('Associated data is not supported')

  encrypted_data = payload[18:][:-32]

  hmac_input = iv + encrypted_data
  h = hmac_sha256(hmac_key, hmac_input)

  if (h != auth_token):
    raise Exception('Invalid hmac')

  decrypted_data = aes_cbc_decrypt(iv, enc_key, encrypted_data)

  return unpad_pkcs7(decrypted_data)

def derive_keys(password, pbkdf_salt, hkdf_salt, iterations):
  dmk = pbkdf_sha512(password, pbkdf_salt, iterations)
  k = hkdf_sha256(dmk, hkdf_salt, b'MK-SUBKEY', 64)
  aes_key = k[0:32]
  hmac_key = k[32:]

  return aes_key, hmac_key

def unwrap_keys(aes_key, hmac_key, dpk):
  decrypted_dmk = aead_decrypt(aes_key, hmac_key, dpk)

  payload_enc_key = decrypted_dmk[0:32]
  payload_hmac_key = decrypted_dmk[32:]

  return payload_enc_key, payload_hmac_key

class VDEHeader:
  def __init__(self, data):
    self.compat_version = int.from_bytes(data[5:6], 'little')
    self.feature_version = int.from_bytes(data[6:7], 'little')
    self.payload_offset = int.from_bytes(data[7:15], 'little')
    self.payload_length = int.from_bytes(data[15:23], 'little')
    self.vde_offset = int.from_bytes(data[23:31], 'little')
    self.vde_length = int.from_bytes(data[31:39], 'little')

class VDESession:
  def __init__(self, data):
    self.compat_version = int.from_bytes(data[0:1], 'little')
    self.feature_version = int.from_bytes(data[1:2], 'little')
    self.pbkdf_iterations = int.from_bytes(data[2:6], "little")
    self.pbkdf_salt_len = int.from_bytes(data[6:10], 'little')
    self.pbkdf_salt = data[10:42]
    self.hkdf_salt_len = int.from_bytes(data[42:46], 'little')
    self.hkdf_salt = data[46:78]
    self.dpk_len = int.from_bytes(data[78:82], 'little')
    self.dpk = data[82:82 + self.dpk_len]

def read_header(f):
  f.seek(0)

  header_bytes = f.read(39)

  return VDEHeader(header_bytes)



# Loads an encrypted file from the filesystem, decrypts it using the
# supplied password and returns a byte array of the unencrypted
# contents
def load_encrypted_file(password, file_path):

  f = open(file_path, 'rb')

  # Check for magic number 'vpvde'
  magic_number = f.read(5)
  if (magic_number != b'vpvde'):
    raise Exception('Not an encrypted file')

  header = read_header(f)

  # Load encrypted payload
  f.seek(header.payload_offset)
  encrypted_payload = f.read(header.payload_length)

  # Load encrypted key data
  f.seek(header.vde_offset)
  vde_bytes = f.read(header.vde_length)
  vde = VDESession(vde_bytes)

  #Derive keys from password
  aes_key, hmac_key = derive_keys(password, vde.pbkdf_salt, vde.hkdf_salt, vde.pbkdf_iterations)

  payload_enc_key, payload_hmac_key = unwrap_keys(aes_key, hmac_key, vde.dpk)

  decrypted_payload = aead_decrypt(payload_enc_key, payload_hmac_key, encrypted_payload)

  return decrypted_payload

# Same a load_encrypted_file except the file contents are passed as a byte
# array
def decrypt_data(password, data):

  # Check for magic number 'vpvde'
  magic_number = data[0:5]
  if (magic_number != b'vpvde'):
    raise Exception('Not an encrypted file')

  header = VDEHeader(data)

  # Load encrypted payload
  encrypted_payload = data[header.payload_offset:header.payload_offset + header.payload_length]

  # Load encrypted key data
  vde_bytes = data[header.vde_offset:header.vde_offset + header.vde_length]
  vde = VDESession(vde_bytes)

  #Derive keys from password
  aes_key, hmac_key = derive_keys(password, vde.pbkdf_salt, vde.hkdf_salt, vde.pbkdf_iterations)

  payload_enc_key, payload_hmac_key = unwrap_keys(aes_key, hmac_key, vde.dpk)

  decrypted_payload = aead_decrypt(payload_enc_key, payload_hmac_key, encrypted_payload)

  return decrypted_payload

# Loads an encrypted plist document. Returns the plist object.
def load_encrypted_plist(password, file_path):
  data = load_encrypted_file(password, file_path)

  return plistlib.loads(data, fmt=plistlib.FMT_XML)

def main():

 
  password = sys.argv[1]
  vp_path = sys.argv[2]
  
  # Decrypt and display storeinfo.plist
  path = Path(Path(), vp_path, 'storeinfo.plist')

  storeinfo = plistlib.load(open(path, 'rb'), fmt=plistlib.FMT_XML)

  encrypted = storeinfo['VoodooPadEncryptedStoreInfo']
  decrypted = decrypt_data(password, encrypted)

  # Decrypt and display tags.plist
  path = Path(Path(), vp_path, 'tags.plist')
  tags = load_encrypted_plist(password, path)

if __name__ == '__main__':
  main()