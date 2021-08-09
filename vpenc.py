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

import hashlib
import os
from pathlib import Path
import plistlib
import sys

import hkdf
import hashlib
import hmac
from math import ceil
import secrets
import uuid

from Crypto.Cipher import AES

# Decryption functions
def hmac_sha256(key, data):
  return hmac.new(key, data, hashlib.sha256).digest()

def hkdf_sha256(key, salt, info, length):
  kdf = hkdf.Hkdf(salt, key, hash=hashlib.sha256)
  return kdf.expand(info, length)

def pbkdf_sha512(password, salt, iterations):
  return hashlib.pbkdf2_hmac('sha512', bytes(password, 'utf-8'), salt, iterations)

# Removes PKCS7 padding
def unpad_pkcs7(data):
  padding_byte = data[-1]
  count = int(padding_byte)
  return data[:-count]

# Applies PKCS7 padding
def pad_pkcs7(data):
  data_len = len(data)
  count = 16 - (data_len % 16)
  padding_byte = count.to_bytes(1, 'little')

  padded = data
  for i in range(0, count):
    padded = padded + padding_byte

  return padded

# Decrypt data. Length must be a multiple of 16 bytes.
def aes_cbc_decrypt(iv, key, ciphertext):
  cipher = AES.new(key, AES.MODE_CBC, iv)
  return cipher.decrypt(ciphertext)

# Encrypt data. Length must be a multiple of 16 bytes.
def aes_cbc_encrypt(iv, key, plaintext):
  cipher = AES.new(key, AES.MODE_CBC, iv)

  return cipher.encrypt(plaintext)


# Decrypt authenticated data
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


# Encrypt and authenticate data
def aead_encrypt(enc_key, hmac_key, payload):
  # Random IV
  iv = secrets.token_bytes(16)

  padded_payload = pad_pkcs7(payload)

  # Encrypt the data
  encrypted_data = aes_cbc_encrypt(iv, enc_key, padded_payload)

  # Compute HMAC
  hmac_input = iv + encrypted_data
  
  h = hmac_sha256(hmac_key, hmac_input)

  # We have no associated data
  assoc_data_len = 0

  return iv + assoc_data_len.to_bytes(2, 'little') + encrypted_data + h



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

# Wraps payload_aes_key and payload_hmac_key
def wrap_keys(aes_key, hmac_key, payload_aes_key, payload_hmac_key):

  keys = payload_aes_key + payload_hmac_key

  return aead_encrypt(aes_key, hmac_key, keys)

class VDEHeader:
  def parse(self, data):
    self.compat_version = int.from_bytes(data[5:6], 'little')
    self.feature_version = int.from_bytes(data[6:7], 'little')
    self.payload_offset = int.from_bytes(data[7:15], 'little')
    self.payload_length = int.from_bytes(data[15:23], 'little')
    self.vde_offset = int.from_bytes(data[23:31], 'little')
    self.vde_length = int.from_bytes(data[31:39], 'little')

  def create(self, payload_length, vde_length):
    self.compat_version = 1
    self.feature_version = 1
    self.payload_offset = 39
    self.payload_length = payload_length
    self.vde_offset = self.payload_offset + self.payload_length
    self.vde_length = vde_length

  def serialize(self):
    vde_bytes = b'vpvde'
    vde_bytes = vde_bytes + self.compat_version.to_bytes(1, 'little')
    vde_bytes = vde_bytes + self.feature_version.to_bytes(1, 'little')
    vde_bytes = vde_bytes + self.payload_offset.to_bytes(8, 'little')
    vde_bytes = vde_bytes + self.payload_length.to_bytes(8, 'little')
    vde_bytes = vde_bytes + self.vde_offset.to_bytes(8, 'little')
    vde_bytes = vde_bytes + self.vde_length.to_bytes(8, 'little')

    return vde_bytes

class VDESession:
  def parse(self, data):
    self.compat_version = int.from_bytes(data[0:1], 'little')
    self.feature_version = int.from_bytes(data[1:2], 'little')
    self.pbkdf_iterations = int.from_bytes(data[2:6], "little")
    self.pbkdf_salt_len = int.from_bytes(data[6:10], 'little')
    self.pbkdf_salt = data[10:42]
    self.hkdf_salt_len = int.from_bytes(data[42:46], 'little')
    self.hkdf_salt = data[46:78]
    self.dpk_len = int.from_bytes(data[78:82], 'little')
    self.dpk = data[82:82 + self.dpk_len]

  def create(self, pbkdf_iterations, pbkdf_salt, hkdf_salt, dpk):
    self.compat_version = 1
    self.feature_version = 1
    self.pbkdf_iterations = pbkdf_iterations
    self.pbkdf_salt_len = len(pbkdf_salt)
    self.pbkdf_salt = pbkdf_salt
    self.hkdf_salt_len = len(hkdf_salt)
    self.hkdf_salt = hkdf_salt
    self.dpk_len = len(dpk)
    self.dpk = dpk

  def serialize(self):
    vde_bytes = self.compat_version.to_bytes(1, 'little')
    vde_bytes = vde_bytes + self.feature_version.to_bytes(1, 'little')
    vde_bytes = vde_bytes + self.pbkdf_iterations.to_bytes(4, 'little')
    vde_bytes = vde_bytes + self.pbkdf_salt_len.to_bytes(4, 'little')
    vde_bytes = vde_bytes + self.pbkdf_salt
    vde_bytes = vde_bytes + self.hkdf_salt_len.to_bytes(4, 'little')
    vde_bytes = vde_bytes + self.hkdf_salt
    vde_bytes = vde_bytes + self.dpk_len.to_bytes(4, 'little')
    vde_bytes = vde_bytes + self.dpk

    return vde_bytes

def read_header(f):
  f.seek(0)

  header_bytes = f.read(39)

  header = VDEHeader()
  header.parse(header_bytes)

  return header

class VPEncryptionContext:

  def load(self, doc_path, password):
    self.doc_path = doc_path

    vde = plistlib.load(open(Path(doc_path, 'vde.plist'), 'rb'), fmt=plistlib.FMT_XML)
    hkdf_salt = vde['kdf']['hkdf_salt']
    pbkdf_salt = vde['kdf']['pbkdf2_salt']
    pbkdf_iterations = vde['kdf']['pbkdf2_iterations']

    aes_key, hmac_key = derive_keys(password, pbkdf_salt, hkdf_salt, pbkdf_iterations)

    self.hkdf_salt = hkdf_salt
    self.pbkdf_salt = pbkdf_salt
    self.pbkdf_iterations = pbkdf_iterations
    self.aes_key = aes_key
    self.hmac_key = hmac_key


  def create(self, doc_path, password):
    self.doc_path = doc_path

    pbkdf_salt = secrets.token_bytes(32)
    hkdf_salt = secrets.token_bytes(32)
    pbkdf_iterations = 40000

    aes_key, hmac_key = derive_keys(password, pbkdf_salt, hkdf_salt, pbkdf_iterations)

    self.hkdf_salt = hkdf_salt
    self.pbkdf_salt = pbkdf_salt
    self.pbkdf_iterations = pbkdf_iterations
    self.aes_key = aes_key
    self.hmac_key = hmac_key

    # Create vde.plist
    vde = {}
    vde['kdf'] = {}
    vde['compat_version'] = 1
    vde['feature_version'] = 1
    vde['kdf']['hkdf_salt'] = hkdf_salt
    vde['kdf']['pbkdf2_salt'] = pbkdf_salt
    vde['kdf']['pbkdf2_iterations'] = pbkdf_iterations

    f = open(Path(doc_path, 'vde.plist'), 'wb')
    plistlib.dump(vde, f)

    # Create storeinfo.plist
    encrypted_store_info = {}
    encrypted_store_info['uuid'] = str(uuid.uuid4)

    data = self.encrypt_data(plistlib.dumps(encrypted_store_info))

    store_info = {}
    store_info['VoodooPadBundleVersion'] = 6
    store_info['VoodooPadEncryptedStoreInfo'] = data
    store_info['isEncrypted'] = True

    plistlib.dump(store_info, open(Path(doc_path, 'storeinfo.plist'), 'wb'))


  def load_file(self, file_path):
    
    f = open(Path(file_path), 'rb')

    data = f.read()
    f.close()

    return self.decrypt_data(data)


  def load_plist(self, file_path):
    data = self.load_file(file_path)

    return plistlib.loads(data, fmt=plistlib.FMT_XML)

  def save_plist(self, plist, plist_path):
    serial = plistlib.dumps(plist, fmt=plistlib.FMT_XML)
    self.save_file(plist_path, serial)

  def save_file(self, file_path, payload):
    
    encrypted_data = self.encrypt_data(payload)
    f = open(file_path, 'wb')
    f.write(encrypted_data)
    f.close()


  def decrypt_data(self, data):

    # Check for magic number 'vpvde'
    magic_number = data[0:5]
    if (magic_number != b'vpvde'):
      raise Exception('Not an encrypted file')

    header = VDEHeader()
    header.parse(data)

    # Load encrypted payload
    encrypted_payload = data[header.payload_offset:header.payload_offset + header.payload_length]

    # Load encrypted key data
    vde_bytes = data[header.vde_offset:header.vde_offset + header.vde_length]
    vde = VDESession()
    vde.parse(vde_bytes)

    payload_enc_key, payload_hmac_key = unwrap_keys(self.aes_key, self.hmac_key, vde.dpk)

    return aead_decrypt(payload_enc_key, payload_hmac_key, encrypted_payload)


  def encrypt_data(self, payload):

    # Generate random keys to encrypt the file
    payload_enc_key = secrets.token_bytes(32)
    payload_hmac_key = secrets.token_bytes(32)

    # Encrypt the data
    encrypted_payload = aead_encrypt(payload_enc_key, payload_hmac_key, payload)

    # Wrap the keys we just used
    wrapped_keys = wrap_keys(self.aes_key, self.hmac_key, payload_enc_key, payload_hmac_key)

    # Create VDE session object
    vde_session = VDESession()
    vde_session.create(self.pbkdf_iterations, self.pbkdf_salt, self.hkdf_salt, wrapped_keys)
    vde_session_bytes = vde_session.serialize()

    # Create VDE header
    vde_header = VDEHeader()
    vde_header.create(len(encrypted_payload), len(vde_session_bytes))
    vde_header_bytes = vde_header.serialize()

    return vde_header_bytes + encrypted_payload + vde_session_bytes
