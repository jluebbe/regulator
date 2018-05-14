from regulator.location import Location
from regulator.memory import MemorySlice
from regulator.memory import MemoryView


def test_slice():
    ms = MemorySlice(0)
    assert len(ms) == 0
    ms[0:4] = '00112233'
    assert len(ms) == 4
    ms[4:8] = '44556677'
    assert ms[0] == 0x33

    ms[0x10] = 0xff
    assert ms[0x0f] == 0x00
    assert ms[0x10] == 0xff

    assert ms[0:4] == '00112233'

def test_slice_base():
    ms = MemorySlice(0x1000)
    ms[0x1000:0x1002] = 'ffff'
    assert len(ms) == 2
    assert ms[0x1000] == 0xff

    assert str(ms) == '00001000: ff ff'

def test_view():
    ms = MemorySlice(0x1000, word_size=4)
    ms[0x1000:0x1004] = 'deadbeef'
    assert ms[0x1000] == 0xef
    mv = MemoryView(ms, Location(0x1000, 0x1004))
    assert len(mv) == 4

    word = mv.get_word(0)
    assert word == [0xde, 0xad, 0xbe, 0xef]
    assert mv.dump() == '00001000: deadbeef -------- -------- --------'

    word_bits = mv.get_word_bits(0)
    assert word_bits == '11011110101011011011111011101111'
    assert mv.dump_bits(Location(4, 12)) == '00001000:     beef = ...._...._...._...._...._1110_1110_....'
