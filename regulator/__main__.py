#!/usr/bin/env python3

from . import memory

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
