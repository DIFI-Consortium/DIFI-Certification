"""
# Copyright (c) ___________________.
# Licensed under the MIT License.
# SPDX-License-Identifier: MIT

"""

class InvalidArgs(Exception):
    pass


def bitstring_to_bytes(s, handle_empty=False):
    v = int(s, 2)
    b = bytearray()
    if handle_empty is True and v == 0:
        if len(s) >= 8:
            return (0).to_bytes(int(len(s)/8), byteorder='big')
    else:
        while v:
            b.append(v & 0xff)
            v >>= 8
    return bytes(b[::-1])
