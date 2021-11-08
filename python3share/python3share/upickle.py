# fMBT, free Model Based Testing tool
# Copyright (c) 2021, Intel Corporation.
#
# Author: antti.kervinen@intel.com
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU Lesser General Public License,
# version 2.1, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St - Fifth Floor, Boston, MA 02110-1301 USA.

# This library provides size-optimized (de)serializer for Python built-in types.

import struct

def _size_val_data(i):
    if 0 <= len(i) <= 15:
        size_bit = 0 # length here, no data_bytes used
        val_bits = struct.pack('b', len(i))[0]
        data_bytes = b''
    else:
        size_bit = 1 # length is not here, it's in data_bytes
        if len(i) < 2**8:
            val_bits = 0b0000
            data_bytes = struct.pack('B', len(i))
        elif len(i) < 2**16:
            val_bits = 0b0001
            data_bytes = struct.pack('<H', len(i))
        elif len(i) < 2**24:
            val_bits = 0b0010
            data_bytes = struct.pack('<I', len(i) << 8)[1:]
        elif len(i) < 2**32:
            val_bits = 0b0011
            data_bytes = struct.pack('<I', len(i))
        elif len(i) < 2**64:
            val_bits = 0b0100
            data_bytes = struct.pack('<Q', len(i))
        else:
            raise ValueError('%s length out of range: %r' % (type(i), len(i)))
    return size_bit, val_bits, data_bytes

def _count(b, bs):
    """b is first byte, containing size_bit and val_bits,
    bs is following data bytes"""
    data_used = 0
    size_bit = (b >> 4) & 0b1
    val_bits = b & 0b1111
    if size_bit == 0:
        # count 0..15
        count = struct.unpack('b', struct.pack('b', b & 0x0f))[0]
    else:
        if val_bits == 0b0000:
            len_s = bs[:1]
            data_used = 1
            count = struct.unpack('B', len_s)[0]
        elif val_bits == 0b0001:
            len_s = bs[:2]
            data_used = 2
            count = struct.unpack('<H', len_s)[0]
        elif val_bits == 0b0010:
            len_s = bs[:3]
            data_used = 3
            count = struct.unpack('<I', b'\x00' + len_s)[0] >> 8
        elif val_bits == 0b0011:
            len_s = bs[:4]
            data_used = 4
            count = struct.unpack('<I', len_s)[0]
        elif val_bits == 0b0100:
            len_s = bs[:8]
            data_used = 8
            count = struct.unpack('<Q', len_s)[0]
    return count, data_used

def dumps(ds):
    # 0000 0000 reserved
    # -- NoneType
    # 0000 0001 None
    # -- bool
    # 0000 0010 False
    # 0000 0011 True
    #
    # first byte type/size/value bits:
    # type
    # |  size
    # |  | value
    # |  | |
    # ttts vvvv
    #
    # -- float, type bits 0000
    # 0001 0000 float, 4 data bytes will follow
    # 0001 xxxx reserved, room for double, complex, ...
    # 0000 1000 float,  0.0
    # 0000 1001 float,  1.0
    # 0000 1011 float, -1.0
    # -- int (size bit 0 => value bits are direct value)
    #        (size bit 1 => value bits are data bit count)
    # 0010 0000 int, 0
    # 0010 0001 int, 1
    # 0010 .... int, 2..14
    # 0010 1111 int, -1
    # 0011 0000 int, -127..128, 1 data byte follows
    # 0011 0001 int, -32786..32767, 2 data bytes follow
    # 0011 0010 int, ..., 3 data bytes follow
    # 0011 0011 int, ..., 4 data bytes follow
    # -- bytes
    # 010s ....
    # 0100 xxxx bytes next max 15 following data bytes
    # 0101 0000 bytes length (max 255) in the first data byte that follows
    # 0101 0001 list length (max 65535) in two data bytes follows
    # 0101 0010 list length (max 2**24-1) in 3 data bytes follows
    # 0101 0011 list length (max 2**32-1) in 4 data bytes follows
    # 0101 0100 list length (max 2**64-1) in 8 data bytes follows
    # -- str
    # 011s ....
    # -- set
    # 100s ....
    # -- tuple
    # 101s ....
    # -- list
    # 1100 xxxx list of 0-15 elements in stack
    # 1101 0000 list length (max 255) in data byte follows
    # 1101 0001 list length (max 65535) in two data bytes follows
    # 1101 0010 list length (max 2**24-1) in 3 data bytes follows
    # 1101 0011 list length (max 2**32-1) in 4 data bytes follows
    # 1101 0100 list length (max 2**64-1) in 8 data bytes follows
    # 1101 xxxx reserved
    # -- dict
    # 111s ....
    bs = []
    if isinstance(ds, type(None)):
        bs.append(0b00000001)
    elif isinstance(ds, bool):
        if not ds:
            bs.append(0b00000010)
        else:
            bs.append(0b00000011)
    elif isinstance(ds, float):
        type_bits = 0b000
        if ds == 0.0:
            size_bit = 0b0
            val_bits = 0b1000
            data_bytes = b''
        elif ds == 1.0:
            size_bit = 0b0
            val_bits = 0b1001
            data_bytes = b''
        elif ds == -1.0:
            size_bit = 0b0
            val_bits = 0b1011
            data_bytes = b''
        else:
            size_bit = 0b1
            val_bits = 0b0000
            data_bytes = struct.pack('<f', ds)
        bs.append((type_bits << 5) | (size_bit << 4) | val_bits)
        bs.extend(data_bytes)
    elif isinstance(ds, int):
        type_bits = 0b001
        if -1 <= ds <= 14:
            size_bit = 0 # value here, no size
            val_bits = struct.pack('b', ds+1)[0]
            data_bytes = b''
        else:
            # pack int value to necessary number of bytes
            size_bit = 1
            if -128 <= ds <= 127:
                data_bytes = struct.pack('b', ds)
                val_bits = 0b0000
            elif -32768 <= ds <= 32767:
                data_bytes = struct.pack('<h', ds)
                val_bits = 0b0001
            elif -2**23 <= ds <= 2**24-1:
                data_bytes = struct.pack('<i', ds << 8)[1:]
                val_bits = 0b0010
            elif -2**31 <= ds <= 2**31-1:
                data_bytes = struct.pack('<i', ds)
                val_bits = 0b0011
            elif -2**63 <= ds <= 2**63-1:
                data_bytes = struct.pack('<q', ds)
                val_bits = 0b0100
            else:
                # there is room in val_bits to handle even larger ints,
                # not implemented yet.
                raise ValueError('int out of range: %r' % (ds,))
        bs.append((type_bits << 5) | (size_bit << 4) | val_bits)
        bs.extend(data_bytes)
    elif isinstance(ds, bytes):
        type_bits = 0b010
        size_bit, val_bits, data_bytes = _size_val_data(ds)
        bs.append((type_bits << 5) | (size_bit << 4) | val_bits)
        bs.extend(data_bytes)
        bs.extend(ds)
    elif isinstance(ds, str):
        type_bits = 0b011
        dsb = ds.encode('utf-8')
        size_bit, val_bits, data_bytes = _size_val_data(dsb)
        bs.append((type_bits << 5) | (size_bit << 4) | val_bits)
        bs.extend(data_bytes)
        bs.extend(dsb)
    elif isinstance(ds, set) or isinstance(ds, tuple) or isinstance(ds, list):
        if isinstance(ds, set):
            type_bits = 0b100
        elif isinstance(ds, tuple):
            type_bits = 0b101
        elif isinstance(ds, list):
            type_bits = 0b110
        for ds_elt in ds:
            bs.extend(dumps(ds_elt))
        size_bit, val_bits, data_bytes = _size_val_data(ds)
        bs.append((type_bits << 5) | (size_bit << 4) | val_bits)
        bs.extend(data_bytes)
    elif isinstance(ds, dict):
        type_bits = 0b111
        for ds_key, ds_value in ds.items():
            bs.extend(dumps(ds_key))
            bs.extend(dumps(ds_value))
        size_bit, val_bits, data_bytes = _size_val_data(ds)
        bs.append((type_bits << 5) | (size_bit << 4) | val_bits)
        bs.extend(data_bytes)
    return b''.join(bytes((b,)) for b in bs)

def loads(bs):
    stack = []
    i = 0
    while i < len(bs):
        b = bs[i]
        i += 1
        if b == 0b00000001:
            stack.append(None)
            continue
        elif b == 0b00000010:
            stack.append(False)
            continue
        elif b == 0b00000011:
            stack.append(True)
            continue
        type_bits = (b >> 5) & 0b111
        size_bit = (b >> 4) & 0b1
        val_bits = b & 0b1111
        if type_bits == 0: # float
            if size_bit == 0: # float
                if val_bits == 0b1000:
                    stack.append(0.0)
                elif val_bits == 0b1001:
                    stack.append(1.0)
                elif val_bits == 0b1011:
                    stack.append(-1.0)
            else:
                float_s = bs[i:i+4]
                i += 4
                stack.append(struct.unpack('<f', float_s)[0])
        elif type_bits == 1: # int
            if size_bit == 0: # value here, no size
                stack.append(struct.unpack('b', struct.pack('b', b & 0x0f))[0]-1)
            elif size_bit == 1:
                if val_bits == 0: # value in single byte
                    int_s = bs[i:i+1]
                    i += 1
                    stack.append(struct.unpack('b', int_s)[0])
                elif val_bits == 1: # value in next two bytes
                    int_s = bs[i:i+2]
                    i += 2
                    stack.append(struct.unpack('<h', int_s)[0])
                elif val_bits == 2: # value in next three bytes
                    int_s = bs[i:i+3]
                    i += 3
                    stack.append(struct.unpack('<i', b'\x00' + int_s)[0] >> 8)
                elif val_bits == 3: # value in next four bytes
                    int_s = bs[i:i+4]
                    i += 4
                    stack.append(struct.unpack('<i', int_s)[0])
                elif val_bits == 4: # value in next 8 bytes
                    int_s = bs[i:i+8]
                    i += 8
                    stack.append(struct.unpack('<q', int_s)[0])
        elif type_bits == 0b010: # bytes
            count, data_used = _count(b, bs[i:i+8])
            i += data_used
            stack.append(bs[i:i+count])
            i += count
        elif type_bits == 0b011: # str
            count, data_used = _count(b, bs[i:i+8])
            i += data_used
            stack.append(bs[i:i+count].decode('utf-8'))
            i += count
        elif type_bits == 0b100 or type_bits == 0b101 or type_bits == 0b110: # set, tuple, list
            if type_bits == 0b100:
                constructor = set
            elif type_bits == 0b101:
                constructor = tuple
            elif type_bits == 0b110:
                constructor = list
            count, data_used = _count(b, bs[i:i+8])
            i += data_used
            if count > 0:
                t = constructor(stack[-count:])
                stack = stack[:-count]
                stack.append(t)
            else:
                stack.append(constructor())
        elif type_bits == 0b111: # dict
            count, data_used = _count(b, bs[i:i+8])
            i += data_used
            if count > 0:
                d_items = stack[-count*2:]
                stack = stack[:-count*2]
                keys = d_items[::2]
                values = d_items[1::2]
                stack.append(dict(zip(keys, values)))
            else:
                stack.append({})
    return stack.pop()
