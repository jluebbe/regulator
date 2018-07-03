import textwrap
from io import StringIO

from pytest import raises

from regulator.decode import Decoder


def decoder_from_string(s):
    f = StringIO(textwrap.dedent(s))
    return Decoder(f)

def test_field_unknown_kind(capsys):
    with raises(ValueError, match="unknown kind g1"):
        decoder_from_string("""
            clusters:
              IPU_Base:
                size: 0xe8
                word_size: 4
                types:
                  r32 IPUx_CONF:
                    fields:
                      g1 0: CSI0_EN
                registers:
                  r32 0x00: IPUx_CONF
            instances:
              IPU_Base 0x2600000: IPU1_Base
        """)
    out, err = capsys.readouterr()
    assert "in field 'g1 0'" in err
    assert "in type 'r32 IPUx_CONF'" in err
    assert "in cluster 'IPU_Base'" in err

def test_field_size_mismatch(capsys):
    with raises(AssertionError):
        decoder_from_string("""
            clusters:
              IPU_Base:
                size: 0xe8
                word_size: 4
                types:
                  r32 IPUx_CONF:
                    fields:
                      u1 0…2: CSI0_EN
                registers:
                  r32 0x00: IPUx_CONF
            instances:
              IPU_Base 0x2600000: IPU1_Base
        """)
    out, err = capsys.readouterr()
    assert "in field 'u1 0…2'" in err
    assert "in type 'r32 IPUx_CONF'" in err
    assert "in cluster 'IPU_Base'" in err

def test_unknown_instance(capsys):
    with raises(KeyError, match="IPU_XXXX"):
        decoder_from_string("""
            clusters:
              IPU_Base:
                size: 0xe8
                word_size: 4
                types:
                  r32 IPUx_CONF:
                    fields:
                      u1 1: CSI0_EN
                registers:
                  r32 0x00: IPUx_CONF
            instances:
              IPU_XXXX 0x2600000: IPU1_Base
        """)
    out, err = capsys.readouterr()
    assert "in instance 'IPU_XXXX 0x2600000'" in err

def test_unknown_enum(capsys):
    with raises(AssertionError):
        decoder_from_string("""
            clusters:
              IPU_Base:
                size: 0xe8
                word_size: 4
                types:
                  r32 IPUx_CONF:
                    enums:
                      my_enum:
                        0x0: the value
                    fields:
                      u2 1..2:
                        name: CSI0_EN
                        enum: my_nonexistent_enum
                registers:
                  r32 0x00: IPUx_CONF
            instances:
              IPU_Base 0x2600000: IPU1_Base
        """)
    out, err = capsys.readouterr()
    assert "in field 'u2 1..2'" in err
    assert "in type 'r32 IPUx_CONF'" in err
    assert "in cluster 'IPU_Base'" in err

def test_unknown_register_type(capsys):
    with raises(AssertionError):
        decoder_from_string("""
            clusters:
              IPU_Base:
                size: 0xe8
                word_size: 4
                types:
                  r32 IPUx_CONF:
                    fields:
                      u2 1..2: CSI0_EN
                registers:
                  r23 0x00: IPUx_CONF
            instances:
              IPU_Base 0x2600000: IPU1_Base
        """)
    out, err = capsys.readouterr()
    assert "in register 'r23 0x00'" in err
    assert "in cluster 'IPU_Base'" in err
