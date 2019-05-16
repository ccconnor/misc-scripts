#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from mnemonic import Mnemonic
from binascii import hexlify, unhexlify
from bip32utils import BIP32Key, BIP32_HARDEN

m = Mnemonic('english')
words = 'xxx'
seed = hexlify(m.to_seed(words)).decode('utf-8')

bip32Key = BIP32Key.fromEntropy(unhexlify(seed))
bip32RootKey = bip32Key.ExtendedKey()
print(bip32RootKey)

bip32Key = bip32Key.ChildKey(44+BIP32_HARDEN).ChildKey(0+BIP32_HARDEN).ChildKey(0+BIP32_HARDEN).ChildKey(0)
bip32MasterKey = bip32Key.ExtendedKey()
print(bip32MasterKey)
