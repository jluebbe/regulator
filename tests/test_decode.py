from io import StringIO
from textwrap import dedent

import pytest

from regulator.decode import Decoder
from regulator.decode import Kind
from regulator.location import Location
from regulator.memory import MemorySlice
from regulator.memory import MemoryView
from regulator.parse import Parser


@pytest.fixture
def decoder_mx6(pytestconfig):
    layout = open(str(pytestconfig.rootdir.join('layouts/imx6.yaml')))
    return Decoder(layout)

@pytest.fixture
def decoder_mx23(pytestconfig):
    layout = open(str(pytestconfig.rootdir.join('layouts/imx23.yaml')))
    return Decoder(layout)

def test_load(decoder_mx6):
    d = decoder_mx6
    pretty(d.layout['clusters'], width=120)
    pretty(d.clusters, width=120)
    pretty(d.instances, width=120)
    assert len(d.clusters) == 3
    assert d.clusters['IPU_Base'].size == 0xe8
    assert d.clusters['IPU_Base'].types['IPUx_CONF'].kind == Kind('r', 32)
    assert d.clusters['IPU_Base'].types['IPUx_CONF'].find_field(28).kind == Kind('u', 1)
    assert d.clusters['IPU_Base'].types['IPUx_CONF'].find_field(28).name == 'CSI0_DATA_SOURCE'
    assert len(d.instances) == 5

    assert Location(0x2600000) & d.instances['IPU1_Base'].location
    assert d.find_instance(0x2600000) == d.instances['IPU1_Base']
    assert d.find_instance(0x2600020) == d.instances['IPU1_Base']
    assert d.find_instance(0x2700020) == None

    assert d.find_cluster(0xdeadbeef) == (None, None)

    cluster_loc, cluster = d.find_cluster(0x2600000)
    assert cluster_loc == Location(0x2600000, 0x26000e8)
    assert cluster.find_register(0x00).name == 'IPUx_CONF'
    reg_type = cluster.find_type(0x00)
    assert reg_type.name == 'IPUx_CONF'
    assert reg_type.find_field(28).name == 'CSI0_DATA_SOURCE'

def test_cluster_iterate_mx6(decoder_mx6):
    cluster_loc, cluster = decoder_mx6.find_cluster(0x2600000)
    assert cluster_loc == Location(0x2600000, 0x26000e8)

    regs = list(cluster.iterate(Location(0x0, 0x4)))
    assert len(regs) == 1
    assert regs[0][0].location == Location(0, 4)

    regs = list(cluster.iterate(Location(0x4, 0x8)))
    assert len(regs) == 1
    assert regs[0][0].location == Location(4, 8)

def test_cluster_iterate_mx23(decoder_mx23):
    cluster_loc, cluster = decoder_mx23.find_cluster(0x8005c000)
    assert cluster_loc == Location(0x8005c000, 0x8005C100)

    regs = list(cluster.iterate(Location(0x00, 0x10)))
    assert len(regs) == 1
    assert regs[0][0].name == 'HW_RTC_CTRL'
    assert regs[0][0].location == Location(0x00, 0x04)

    regs = list(cluster.iterate(Location(0x04, 0x08)))
    assert len(regs) == 0

    regs = list(cluster.iterate(Location(0x10, 0x20)))
    assert len(regs) == 1
    assert regs[0][0].name == 'HW_RTC_STAT'
    assert regs[0][0].location == Location(0x10, 0x14)

def test_decode_ms(decoder_mx6):
    ms = MemorySlice(0x2600000, word_size=4)
    ms[0x2600000:0x2600004] = '00000761'
    ms[0x2600004:0x2600008] = '00000000'
    ms[0x2600008:0x260000c] = '00000000'
    ms[0x260000c:0x2600010] = '00000000'
    ms[0x2600010:0x2600014] = '00000000'

    print()
    decoder_mx6.decode(ms)

def test_decode_mx23(decoder_mx23):
    dump = """
8005c000: 00000008 00000008 00000008 00000008                ................
8005c010: e0000000 e0000000 e0000000 e0000000                ................
8005c020: 00169885 00169886 00169887 00169888                ................
8005c030: 000005c8 000005c8 000005c8 000005c8                ................
8005c040: 00000000 00000000 00000000 00000000                ................
8005c050: ffffffff ffffffff ffffffff ffffffff                ................
    """.strip().splitlines()
    p = Parser()
    result = p.parse_lines(dump)

    assert len(result) == 6
    assert result[0].base == 0x8005c000
    assert result[1].base == 0x8005c010

    print()
    decoder_mx23.decode(result[0])
    decoder_mx23.decode(result[1])
