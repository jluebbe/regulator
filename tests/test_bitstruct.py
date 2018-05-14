import bitstruct


def test_bitstruct():
    word = [0xde, 0xad, 0xbe, 0xef]
    assert bitstruct.unpack_from('u4', word, offset=28)[0] == 0xf
    assert bitstruct.unpack('p28u4', word)[0] == 0xf
    assert bitstruct.unpack('p0u4', word)[0] == 0xd
