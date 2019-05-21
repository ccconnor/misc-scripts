#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from bitcoin.core import serialize as ser

powLimit = 0x00000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffff
bits = ser.compact_from_uint256(powLimit)
print(hex(bits))
