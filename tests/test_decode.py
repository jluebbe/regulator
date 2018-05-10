from io import StringIO
from textwrap import dedent

import pytest

from regulator.decode import Decoder, Kind
from regulator.location import Location
from regulator.memory import MemorySlice

@pytest.fixture
def decoder():
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
              u1 06: DI0_EN
              u1 07: DI1_EN
              u1 08: SMFC_EN
              u1 09: DC_EN
              u1 10: DMFC_EN
              u1 28:
                name: CSI0_DATA_SOURCE
                enum:
                  0: Parallel interface is connected to CSI0
                  1: MCT (MIPI) is connected to CSI0
          r32 IPUx_SISG_CTRL0:
            fields:
              u1 00: VSYNC_RST_CNT
              u3 01…03: NO_VSYNC_2_STRT_CNT
        registers:
          r32 0x00: IPUx_CONF
          r32 0x04: IPUx_SISG_CTRL0
    instances:
      IPU_Base 0x260000: IPU1_Base
      IPU_Base 0x2A0000: IPU2_Base
    """))
    return Decoder(layout)

def test_load(decoder):
    d = decoder
    pretty(d.layout['clusters'], width=120)
    pretty(d.clusters, width=120)
    pretty(d.instances, width=120)
    assert len(d.clusters) == 1
    assert d.clusters['IPU_Base'].size == 0xe8
    assert d.clusters['IPU_Base'].types['IPUx_CONF'].kind == Kind('r', 32)
    assert d.clusters['IPU_Base'].types['IPUx_CONF'].find_field(28).kind == Kind('u', 1)
    assert d.clusters['IPU_Base'].types['IPUx_CONF'].find_field(28).name == 'CSI0_DATA_SOURCE'
    assert len(d.instances) == 2

    assert Location(0x260000) & d.instances['IPU1_Base'].location
    assert d.find_instance(0x260000) == d.instances['IPU1_Base']
    assert d.find_instance(0x260020) == d.instances['IPU1_Base']
    assert d.find_instance(0x270020) == None

    cluster_loc, cluster = d.find_cluster(0x260000)
    assert cluster_loc == Location(0x260000, 0x2600e8)
    assert cluster.find_register(0x00).name == 'IPUx_CONF'
    reg_type = cluster.find_type(0x00)
    assert reg_type.name == 'IPUx_CONF'
    assert reg_type.find_field(28).name == 'CSI0_DATA_SOURCE'

def test_decode_ms(decoder):
    ms = MemorySlice(0x260000, word_size=4)
    ms[0x260000:0x260004] = '00000761'
    ms[0x260004:0x260008] = '00000000'
    decoder.decode(ms)
