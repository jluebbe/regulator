import attr
import bitstruct
import sys
import yaml
from prettyprinter import pprint
from sortedcontainers import SortedListWithKey

from .location import Location
from .memory import MemoryView


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
    enums = attr.ib(default=None)

    def __attrs_post_init__(self):
        self.kind = Kind.from_str(self.kind)
        fields = SortedListWithKey(key=lambda x: x.location)
        for k, v in self.fields.items():
            try:
                kind, location = k.split()
                if isinstance(v, str):
                    name = v
                    config = {}
                else:
                    name = v.pop('name')
                    config = v
                if "enum" in config.keys() and isinstance(config["enum"], str):
                    assert config["enum"] in self.enums.keys()
                    config["enum"] = self.enums[config["enum"]]
                field = Field(name, kind, location, **config)
                fields.add(field)
            except:
                sys.stderr.write("Note: in field '{}':\n".format(k))
                raise
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
            try:
                kind, name = k.split()
                assert kind in ['r32']
                types[name] = Type(name, kind, **v)
            except:
                sys.stderr.write("Note: in type '{}':\n".format(k))
                raise
        self.types = types

        registers = SortedListWithKey(key=lambda x: x.location)
        for k, v in self.registers.items():
            try:
                kind, location = k.split(' ', 1)
                if isinstance(v, str):
                    name = v
                    config = {}
                else:
                    name = v.pop('name')
                    config = v
                register = Register(name, kind, location, config.get('type'))
                registers.add(register)
            except:
                sys.stderr.write("Note: in register '{}':\n".format(k))
                raise
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
    def __init__(self, f):
        if isinstance(f, str):
            self.filename = f
            self.reload()
        else:
            self.load(f)

    def reload(self):
        self.load(open(self.filename, 'r'))

    def load(self, stream):
        layout = yaml.load(stream)

        clusters = {}
        for name, config in layout['clusters'].items():
            try:
                cluster = Cluster(name, **config)
                clusters[name] = cluster
            except:
                sys.stderr.write("Note: in cluster '{}':\n".format(name))
                raise

        instances = {}
        for k, v in layout['instances'].items():
            try:
                cluster_name, start = k.split(' ', 1)
                start = int(start, 0)
                name = v
                cluster = clusters[cluster_name]
                location = Location(start, start+cluster.size)
                instance = Instance(name, cluster_name, location)
                instances[name] = instance
            except:
                sys.stderr.write("Note: in instance '{}':\n".format(k))
                raise

        self.layout = layout
        self.clusters = clusters
        self.instances = instances

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
        return instance, cluster

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
        instance, cluster = self.find_cluster(ms.base)
        if instance is None:
            print('no instance found')
            return
        mv = MemoryView(ms, instance.location)
        loc = mv.outer_loc - instance.location.start
        assert loc is not None
        for reg, reg_type in cluster.iterate(loc):
            reg_mv = MemoryView(mv, reg.location - loc.start)
            print(reg_mv.dump()+' # {} {}'.format(instance.name, reg.name))
            #pretty((reg, reg_type))
            for field_loc, name, value, decoded in self.decode_fields(reg_mv, reg_type):
                if decoded:
                    print(reg_mv.dump_bits(field_loc)+' # {}: {} = {} '.format(name, value, decoded))
                else:
                    print(reg_mv.dump_bits(field_loc)+' # {}: {}'.format(name, value))
