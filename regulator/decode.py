from prettyprinter import pprint

from .memory import MemoryView
from .location import Location

from sortedcontainers import SortedListWithKey

import attr
import yaml
import bitstruct

@attr.s
class Kind:
    hint = attr.ib()
    bits = attr.ib()

    @classmethod
    def from_str(cls, s):
        hint = s[0:1]
        bits = int(s[1:])
        return cls(hint, bits)

    def __attrs_post_init__(self):
        if not self.hint in ['r', 'u']:
            raise ValueError("unknown kind {}".format(self.kind))

    def __len__(self):
        assert not self.bits % 8
        return self.bits//8

    def __str__(self):
        return self.hint+str(self.bits)

@attr.s
class Field:
    name = attr.ib()
    kind = attr.ib()
    location = attr.ib()
    enum = attr.ib(default=None)

    def __attrs_post_init__(self):
        self.kind = Kind.from_str(self.kind)
        self.location = Location.from_str(self.location, size=self.kind.bits)

    def decode(self, value):
        if self.enum is not None:
            return self.enum[value]

@attr.s
class Type:
    name = attr.ib()
    kind = attr.ib()
    fields = attr.ib()

    def __attrs_post_init__(self):
        self.kind = Kind.from_str(self.kind)
        fields = SortedListWithKey(key=lambda x: x.location)
        for k, v in self.fields.items():
            kind, location = k.split()
            if isinstance(v, str):
                name = v
                config = {}
            else:
                name = v.pop('name')
                config = v
            field = Field(name, kind, location, **config)
            fields.add(field)
        self.fields = fields

    def __len__(self):
        return len(self.kind)

    def find_field(self, addr):
        addr = Location(addr)
        for field in self.fields:
            if field.location & addr:
                return field

@attr.s
class Register:
    name = attr.ib()
    kind = attr.ib()
    location = attr.ib()
    type_name = attr.ib(default=None)

    def __attrs_post_init__(self):
        self.kind = Kind.from_str(self.kind)
        assert self.kind.bits % 8 == 0
        self.location = Location.from_str(self.location, size=self.kind.bits//8)
        if self.type_name is None:
            self.type_name = self.name

@attr.s
class Cluster:
    name = attr.ib()
    size = attr.ib()
    types = attr.ib()
    registers = attr.ib()
    word_size = attr.ib(default=4)

    def __attrs_post_init__(self):
        types = {}
        for k, v in self.types.items():
            kind, name = k.split()
            assert kind in ['r32']
            types[name] = Type(name, kind, **v)
        self.types = types

        registers = SortedListWithKey(key=lambda x: x.location)
        for k, v in self.registers.items():
            kind, location = k.split(' ', 1)
            if isinstance(v, str):
                name = v
                config = {}
            else:
                name = v.pop('name')
                config = v
            register = Register(name, kind, location, config.get('type'))
            registers.add(register)
        self.registers = registers

    @property
    def inner_loc(self):
        return Location.from_size(self.size)

    def find_register(self, addr):
        addr = Location(addr)
        for register in self.registers:
            if register.location & addr:
                return register

    def find_type(self, addr):
        register = self.find_register(addr)
        return self.types[register.type_name]

    def iterate(self, loc):
        for register in self.registers.irange_key(
                min_key=Location(loc.start),
                max_key=Location(loc.stop),
                inclusive=(True, False)):
            yield (register, self.types[register.type_name])

@attr.s
class Instance:
    name = attr.ib()
    cluster = attr.ib()
    location = attr.ib()

class Decoder:
    def __init__(self, layout):
        self.layout = yaml.load(layout)

        self.clusters = {}
        for name, config in self.layout['clusters'].items():
            cluster = Cluster(name, **config)
            self.clusters[name] = cluster

        self.instances = {}
        for k, v in self.layout['instances'].items():
            cluster_name, start = k.split(' ', 1)
            start = int(start, 0)
            name = v
            cluster = self.clusters[cluster_name]
            location = Location(start, start+cluster.size)
            instance = Instance(name, cluster_name, location)
            self.instances[name] = instance

    def find_instance(self, addr):
        addr = Location(addr)
        for instance in self.instances.values():
            if instance.location & addr:
                return instance

    def find_cluster(self, addr):
        instance = self.find_instance(addr)
        if instance is None:
            return None, None
        cluster_name = instance.cluster
        cluster = self.clusters[cluster_name]
        return instance.location, cluster

    def decode_fields(self, mv, reg_type):
        assert len(mv) == len(reg_type.kind)
        word = mv.get_word(0)
        values = []
        for field in reg_type.fields:
            # use native math instead?
            offset = reg_type.kind.bits - field.location.stop
            fmt = "p{}{}".format(offset, str(field.kind))
            value = bitstruct.unpack(fmt, word)[0]
            decoded = field.decode(value)
            values.append((field.location, field.name, value, decoded))
        return list(reversed(values))

    def decode(self, ms):
        cluster_loc, cluster = self.find_cluster(ms.base)
        if cluster is None:
            print('no instance found')
            return
        mv = MemoryView(ms, cluster_loc)
        loc = mv.outer_loc - cluster_loc.start
        assert loc is not None
        for reg, reg_type in cluster.iterate(loc):
            reg_mv = MemoryView(mv, reg.location)
            print(reg_mv.dump())
            #pretty((reg, reg_type))
            for loc, name, value, decoded in self.decode_fields(reg_mv, reg_type):
                if decoded:
                    print(reg_mv.dump_bits(loc)+' # {}: {} = {} '.format(name, value, decoded))
                else:
                    print(reg_mv.dump_bits(loc)+' # {}: {}'.format(name, value))
