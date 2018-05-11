import re

from .memory import MemorySlice

class Parser:
    MAP_MESSAGE = re.compile(r"^mapping offset (\S+) \(size (\S+)\)$")

    def __init__(self):
        self.map_base = 0x0

    def parse_map(self, line):
        m = self.MAP_MESSAGE.match(line)
        if not m:
            return False
        self.map_base = int(m.group(1), 16)
        print('parser base set to 0x{:x}'.format(self.map_base))
        return True

    def parse_hex_line(self, line):
        line = line.strip()
        if not ':' in line:
            return
        addr, data = line.split(':')
        addr = int(addr, 16) + self.map_base
        data = data[:-16].split()
        word_size = len(data[0])//2
        slice = MemorySlice(addr, word_size=word_size)
        for word in data:
            assert len(word) == word_size * 2
            slice[addr:addr+word_size] = word
            addr += word_size
        return slice

    def parse(self, text):
        lines = text.split('\n')
        if len(lines) < 3:
            return []
        lines = lines[1:-1]
        slices = []
        for line in lines:
            if self.parse_map(line):
                continue
            else:
                slice = self.parse_hex_line(line)
                if slice:
                    slices.append(slice)
        return slices
