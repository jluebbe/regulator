import binascii
import signal

import attr
import bitstruct

from .location import Location


class MemorySlice:
    def _shift_slice(self, value, offset):
        if isinstance(value, slice):
            assert value.step is None
            return slice(value.start + offset, value.stop + offset)
        else:
            return value + offset

    def __init__(self, base, *, swapped=True, word_size=1):
        self.base = base
        self.data = bytearray()
        self.swapped = swapped # little endian
        self.word_size = word_size

    def __setitem__(self, index, value):
        index = self._shift_slice(index, -self.base)

        if isinstance(index, slice):
            assert 0 <= index.start < index.stop <= (1024*1024)
            value = binascii.unhexlify(value)
            assert len(value) == index.stop-index.start
            assert len(value) in [1, 2, 4, 8]
            if self.swapped:
                value = value[::-1]
            size = max(len(self.data), index.stop)
        else:
            assert 0 <= index < (1024*1024)
            assert 0 <= value <= 255
            size = max(len(self.data), index+1)

        if len(self.data) < size:
            self.data.extend(b'\00' * (size-len(self.data)))
        self.data[index] = value
    
    def __getitem__(self, index):
        index = self._shift_slice(index, -self.base)
        value = self.data[index]

        if isinstance(index, slice):
            assert len(value) in [1, 2, 4, 8]
            if self.swapped:
                value = value[::-1]
            return binascii.hexlify(value).decode('ASCII')
        else:
            return value

    def __str__(self):
        lines = []
        for line_offset in range(self.base, self.base+len(self.data), 16):
            line = ["{:08x}:".format(line_offset)]
            for byte_offset in range(line_offset, self.base+len(self.data), self.word_size):
                line.append(self[byte_offset:byte_offset+self.word_size])
            lines.append(' '.join(line))
        return '\n'.join(lines)

    def __len__(self):
        return len(self.data)

    @property
    def inner_loc(self):
        return Location(self.base, self.base+len(self.data))

    def map(self, addr):
        return addr

class MemoryView:
    """a relative view into a memory slice"""

    def __init__(self, parent, loc):
        self._parent = parent
        overlap = parent.inner_loc & loc
        if overlap is None:
            raise ValueError("{} and {} do not overlap".format(parent.inner_loc, loc))
        self._start = overlap.start
        self._stop = overlap.stop

    def __getitem__(self, index):
        if index < 0 or index >= self._stop:
            raise IndexError()

        return self._parent[self._start+index]

    def __repr__(self):
        return "{}/{}".format(repr(self._parent), self.outer_loc.hex())

    def __len__(self):
        return self._stop-self._start

    @property
    def outer_loc(self):
        return Location(self._start, self._stop)

    @property
    def inner_loc(self):
        return Location.from_size(self._stop-self._start)

    @property
    def word_size(self):
        return self._parent.word_size

    @property
    def swapped(self):
        return self._parent.swapped

    def get_word(self, addr):
        assert addr % self.word_size == 0
        data = []
        idxs = range(addr, addr+self.word_size)
        if self.swapped:
            idxs = reversed(idxs)
        for i in idxs:
            data.append(self[i])
        return data

    def get_word_bits(self, addr):
        return ''.join('{:08b}'.format(x) for x in self.get_word(addr))

    def map(self, index):
        return self._parent.map(self._start+index)

    @property
    def mapped_loc(self):
        return Location(self.map(0), self.map(len(self)))

    def dump(self):
        offset = self.map(0)
        loc = self.inner_loc + offset
        lines = []
        for line_loc in loc.range(step=16, align=True):
            line = ['{:08x}: '.format(line_loc.start)]
            for word_loc in line_loc.range(step=self.word_size):
                byte_range = list(word_loc.range())
                if self.swapped:
                    byte_range = reversed(byte_range)
                for byte_loc in byte_range:
                    if byte_loc & loc:
                        line.append('%02x' % self[byte_loc.start - offset])
                    else:
                        line.append('--')
                line.append(' ')
            lines.append(''.join(line[:-1]))
        return '\n'.join(lines)

    def dump_bits(self, bit_loc):
        bit_loc = bit_loc.reverse(self.word_size*8)

        assert len(self) == self.word_size

        mapped_loc = self.mapped_loc
        aligned_loc = mapped_loc.align(16)
        shift = mapped_loc.start - aligned_loc.start
        assert shift % self.word_size == 0

        line = ['{:08x}: '.format(mapped_loc.start)]

        bit_offset = self.word_size * 8 - bit_loc.stop

        mask_loc = (bit_loc//8).reverse(self.word_size)
        byte_range = list(self.inner_loc.range())
        if self.swapped:
            byte_range = reversed(byte_range)
        for byte_loc in byte_range:
            if byte_loc & mask_loc:
                line.append('%02x' % self[byte_loc.start])
            else:
                line.append('  ')
                bit_offset -= 8
        line.append(' = ')

        word_bits = self.get_word_bits(0)
        bits = '.'*bit_loc.start + \
                word_bits[bit_loc.start:bit_loc.stop] + \
                '.'*(self.word_size*8 - bit_loc.stop)

        assert len(bits) == self.word_size*8

        for i in range(0, len(bits), 4):
            line.append(bits[i:i+4])
            line.append('_')
        line.pop()

        return ''.join(line)
