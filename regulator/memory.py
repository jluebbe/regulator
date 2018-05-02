#!/usr/bin/env python3

import binascii
import signal

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

class MemorySlice:
    def __init__(self, base, swapped=True):
        self.base = base
        self.data = bytearray()
        self.swapped = swapped # little endian

    def __setitem__(self, index, value):
        print(index, value)
        value = binascii.unhexlify(value)
        assert len(value) in [1, 2, 4, 8]
        if self.swapped:
            value[::-1]
        size = max(len(self.data), index+len(value))
        if len(self.data) < size:
            self.data.extend(b'\00' * (size-len(self.data)))
        self.data[index:index+len(value)] = value

    def __str__(self):
        return "{:08x}: {}".format(self.addr, self.data)

def process_line(line):
    print(line)
    line = line.strip()
    if not ':' in line:
        return
    addr, data = line.split(':')
    addr = int(addr, 16)
    data = data[:-16].split()
    word_size = len(data[0])/2

    slice = MemorySlice(addr)
    for word in data:
        assert len(word) == word_size * 2
        slice[addr] = word
        addr += word_size

    print(slice)


def process_dump(text):
    lines = text.split('\n')
    if len(lines) < 3:
        return
    lines = lines[1:-1]
    for line in lines:
        process_line(line)

def on_change(*args):
    text = selection.wait_for_text()
    if text is None:
        return
    process_dump(text)




selection = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY,)
selection.connect('owner-change', on_change)
signal.signal(signal.SIGINT, signal.SIG_DFL)
Gtk.main()
