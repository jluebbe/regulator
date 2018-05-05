import binascii
import signal

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

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
