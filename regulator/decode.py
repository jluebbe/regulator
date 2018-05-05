from pprint import pprint

import attr
import yaml

@attr.s
class Location:
    start = attr.ib()
    stop = attr.ib(default=None)

    def __attrs_post_init__(self):
        if self.stop is None:
            self.stop = self.start+1

    def __and__(self, other):
        assert isinstance(other, Location)
        if self.start < other.stop and other.start < self.stop:
            return Location(
                    max(self.start, other.start),
                    min(self.stop, other.stop)
            )

    def __add__(self, offset):
        assert isinstance(offset, int)
        return Location(self.start+offset, self.stop+offset)

    def __len__(self):
        return self.stop - self.start

    def next(self):
        return Location(self.stop)

    def __str__(self):
        if len(self) == 1:
            return '{}'.format(self.start)
        else:
            return '{}…{}'.format(self.start, self.stop-1)

@attr.s
class Field:
    name = attr.ib()
    kind = attr.ib()
    location = attr.ib()
    enum = attr.ib(default=None)

@attr.s
class Type:
    name = attr.ib()
    kind = attr.ib()
    fields = attr.ib()

    def __attrs_post_init__(self):
        fields = {}
        for k, v in self.fields.items():
            kind, location = k.split()
            if isinstance(v, str):
                name = v
                config = {}
            else:
                name = v.pop('name')
                config = v
            fields[int(location)] = Field(name, kind, location, **config)
        self.fields = fields

@attr.s
class Register:
    name = attr.ib()
    kind = attr.ib()
    location = attr.ib()

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

        registers = {}
        for k, v in self.registers.items():
            kind, location = k.split(' ', 1)
            type_name = v
            registers[int(location)] = Register(name, kind, location)
        self.registers = registers

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
            pprint(config)
            cluster = Cluster(name, **config)
            self.clusters[name] = cluster

        self.instances = {}
        for k, v in self.layout['instances'].items():
            cluster_name, location = k.split(' ', 1)
            name = v
            instance = Instance(name, cluster_name, location)
            self.instances[name] = instance
