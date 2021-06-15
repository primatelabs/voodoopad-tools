## VoodooPad Document Encryption (VDE)

### VDE Item

| Structure name  | Size  |
| ------------ | ------------ |
|  VDE Header |  variable |
|  Encrypted Data |  variable |
|   VDE Session| Variable




##### VDE Header

| Structure name  | Size  |
| ------------ | ------------ |
|  Magic number |  5 bytes |
|  Compat version |  1 byte |
|   Feature version| 1 byte
| Encrypted data offset | 8 bytes |
| Encrypted data size| 8 bytes |
| VDE Session offset| 8 bytes|
| VDE Session size|8 bytes|

- The magic number is 5 bytes representing the string `vpvde`

##### Encrypted Data

- The encrypted data is in ETM-AEAD-v1 format (see below)

##### VDE Session

| Structure name  | Size  |
| ------------ | ------------ |
|  Compat version |  1 byte |
|  Feature version |  1 byte |
|   PBKDF Iterations | 4 bytes
| PBKDF salt size | 4 bytes |
| PBKDF salt| variable size|
|HKDF salt size| 4 bytes|
|HKDF salt|variable size|
|DPK size| 4 bytes|
|DPK| variable size|

##### Data Protection Key (DPK)

The Data Protection Key (DPK) is used to encrypt and authenticate the Encrypted Data portion of the VDE Item. It is a 512-bit key: 256 bits for encryption, 256 bits for authentication.

The DPK is encrypted using DMK-SUBKEY. The DPK is stored in the ETM-AEAD-v1 format.


##### ETM-AEAD-v1 format


| Structure name  | Size  |
| ------------ | ------------ |
|  IV |  16 byte |
|  Associated data size |  2 bytes |
|  Associated data | variable size|
| Encrypted data | variable size|
| HMAC tag| 32 bytes|

The size of the encrypted data is inferred by subtracting the size of the other data elements from the size of the structure.

The HMAC tag is calculated as

`HMAC(IV || encrypted data)`

Where `||` is concatenation.

When the key is correct, the calculated HMAC will match the HMAC tag in the data structure.

Note: The Associated data field doesn't appear to be used anywhere, and the length is always 0, and does not get included in the HMAC calculation.

Encrypted Data is encrypted using `AES-256-CBC` with `PKCS7` padding.


#### Document encryption using password

VoodooPad protects its documents using a password.

The Document Master Key (DMK) is a 512-bit key derived from the password using PBKDF2-SHA512.

The DMK is fed through the HKDF-SHA-256 function to get a 512-bit DMK-SUBKEY.

`DMK = PBKDF2-HMAC-SHA512(password, pbkdf_salt, 64)`

`DMK-SUBKEY = HKDF(MK, hkdf_salt, 'MK-SUBKEY', 64)`

DMK-SUBKEY encrypts the Document Master Key (DMK).


### VoodooPad document files

When a document is encrypted, all the files are encrypted using the VPE Item format.

Exceptions are:

##### storeinfo.plist

A plist file containing a `VoodooPadEncryptedStoreInfo` field. This field contains a VPE encrypted storeinfo.plist file.

##### vde.plist

A plist file containing the PBKDF salt and HKDF salt. These seem to match the salts encoded in the encrypted files in the document, which means we can probably derive the DMK and DMK-SUBKEY once and use it to decrypt all files in the document instead of deriving them from the password every time.

