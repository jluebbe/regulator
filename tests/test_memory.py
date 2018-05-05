from regulator.memory import MemorySlice

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
