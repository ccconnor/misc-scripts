#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import x13bcd_hash
import hashlib

from binascii import unhexlify, hexlify


def reverse(source):
    return (hexlify((unhexlify(source))[::-1])).decode('utf-8')


# block header
version = reverse('60000000')
previous_hash = reverse('7ed99d046238670a28fbf836abf2b4d40d7ec91b1e96ddfa08de2e5e564b95d7')
merkle_root = reverse('a7359c55b0a72fa0c92baffea0c332532b9b0a198d5b7b5cc693f41f08e4aa42')
time = reverse((hex(1558408497))[2:])
bits = reverse('1a437a60')
nonce = reverse((hex(339840005))[2:])
block_header_hex = version + previous_hash + merkle_root + time + bits + nonce
print('block header:', block_header_hex)

# x13hash
block_header_bin = unhexlify(block_header_hex)
block_hash_bin = x13bcd_hash.getPoWHash(block_header_bin)
block_hash_hex = hexlify(block_hash_bin).decode("utf-8")
print('x13hash:', block_hash_hex)

# double sha256
hash256 = hashlib.sha256(hashlib.sha256(block_header_bin).digest()).digest()
print('double sha256:', hexlify(hash256).decode('utf-8'))

