from io import StringIO
from pprint import pprint
from textwrap import dedent

from regulator.memory import MemorySlice
from regulator.decode import Location, Decoder

def test_location():
    assert Location(1) == Location(1, 2)
    assert Location(1, 2)+2 == Location(3)
    assert Location(1) < Location(2)
    assert Location(1) < Location(1, 3)

    assert (Location(1, 4) & Location(3,6)) == Location(3)
    assert (Location(1) & Location(2)) == None

    assert len(Location(0)) == 1
    assert len(Location(0, 2)) == 2

    assert Location(0).next() == Location(1)
    assert Location(0, 3).next() == Location(3)
    
    assert str(Location(0)) == '0'
    assert str(Location(0, 2)) == '0…1'

def test_decoder():
    layout = StringIO(dedent("""
    clusters:
      IPU_Base:
        size: 0xe8
        word_size: 4
        types:
          r32 IPUx_CONF:
            fields:
              u1 00: CSI0_EN
              u1 01: CSI1_EN
              u1 02: IC_EN
              u1 03: IRT_EN
              u1 05: DP_EN
              u1 28:
                name: CSI0_DATA_SOURCE
                enum:
                  0: Parallel interface is connected to CSI0
                  1: MCT (MIPI) is connected to CSI0
        registers:
          r32 00: IPUx_CONF
    instances:
      IPU_Base 0x260000: IPU1_Base
      IPU_Base 0x2A0000: IPU2_Base
    """))
    d = Decoder(layout)
    pprint(d.layout['clusters'], width=120)
    pprint(d.clusters, width=120)
    pprint(d.instances, width=120)
    assert len(d.clusters) == 1
    assert d.clusters['IPU_Base'].size == 0xe8
    assert d.clusters['IPU_Base'].types['IPUx_CONF'].kind == 'r32'
    pprint(d.clusters['IPU_Base'].types['IPUx_CONF'].fields)
    assert d.clusters['IPU_Base'].types['IPUx_CONF'].fields[28].kind == 'u1'
    assert d.clusters['IPU_Base'].types['IPUx_CONF'].fields[28].name == 'CSI0_DATA_SOURCE'
    assert len(d.instances) == 2
    assert False
