from regulator.parse import Parser


def test_parse_hex_line():
    p = Parser()
    line = "f1022100: 00000000 00000011 00000001 03330007                ..............3."
    ms = p.parse_hex_line(line)
    s = str(ms)
    assert line[:len(s)] == s

def test_parse_short():
    p = Parser()
    assert p.parse_dirty("dsafasdfSADF") == []
    assert p.parse_dirty("\ndsafasdfSADF") == []
    assert p.parse_dirty("dsafasdfSADF\n") == []

def test_parse_bad():
    p = Parser()
    assert p.parse_dirty("\ndsafasdfSADF\n") == []

def test_parse_memtool():
    p = Parser()
    dump = """
~ # memtool md 0xf1022100
f1022100: 00000000 00000011 00000001 03330007                ..............3.
f1022110: 00000400 00000300 00000100 00000000                ................
f1022120: 00000001 00125924 00000000 0000003f                ....$Y......?...
f1022130: 00000000 00000000 00000000 00000000                ................
f1022140: 00000000 00000000 00000000 00000000                ................
f1022150: 00000000 00000000 00000000 00000000                ................
    """
    result = p.parse_dirty(dump)
    assert len(result) == 6
    assert p.map_base == 0x0
    ms = result[2]
    assert ms.base == 0xf1022120
    assert ms[0xf1022124:0xf1022128] == '00125924'

def test_parse_memedit():
    p = Parser()
    dump = """
->map 0x2600000 0x200000
mapping offset 0x02600000 (size 0x200000)
->md 0x30000 0x100
00030000: 04008b00 01df02ef 01df02ef 00000000 ................
00030010: 00000000 00000000 00000000 00000000 ................
00030020: ffffffff 00000000 00000000 00000000 ................
00030030: 00000000 00000000 00000000 00000000 ................
00030040: 00000000 00000000 00000000 00000000 ................
00030050: 00000000 00000000 00000000 00000000 ................
    """
    result = p.parse_dirty(dump)
    assert len(result) == 6
    assert p.map_base == 0x2600000
    ms = result[0]
    assert ms.base == 0x2630000
    assert ms[0x2630004:0x2630008] == '01df02ef'
