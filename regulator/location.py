import attr

@attr.s(frozen=True)
class Location:
    start = attr.ib()
    stop = attr.ib(default=None)

    @classmethod
    def from_str(cls, s, *, size=None):
        def from_hex_or_dec(s):
            if s.startswith('0x'):
                return int(s, 16)
            else:
                return int(s, 10)

        if isinstance(size, str):
            size = from_hex_or_dec(size)

        if '…' in s:
            start, end = s.split('…', 1)
            start = from_hex_or_dec(start)
            stop = from_hex_or_dec(end)+1
        elif '..' in s:
            start, end = s.split('..', 1)
            start = from_hex_or_dec(start)
            stop = from_hex_or_dec(end)+1
        else:
            start = from_hex_or_dec(s)
            if size is None:
                size = 1
            stop = start+size

        if size is not None:
            assert size == stop-start

        return cls(start, stop)

    @classmethod
    def from_size(cls, size):
        return cls(0, size)

    def __attrs_post_init__(self):
        if self.stop is None:
            object.__setattr__(self, "stop", self.start+1)

        if self.start >= self.stop:
            raise ValueError('start must be less than stop')

    def __and__(self, other):
        if not isinstance(other, Location):
            raise TypeError('other must by of type Location (not {})'.format(type(other)))
                
        if self.start < other.stop and other.start < self.stop:
            return Location(
                    max(self.start, other.start),
                    min(self.stop, other.stop)
            )

    def __add__(self, offset):
        assert isinstance(offset, int)
        return Location(self.start+offset, self.stop+offset)

    def __sub__(self, offset):
        return self.__add__(-offset)

    def __mul__(self, factor):
        assert isinstance(factor, int)
        return Location(self.start*factor, self.stop*factor)

    def __floordiv__(self, factor):
        assert isinstance(factor, int)
        return Location(self.start//factor, (self.stop+factor-1)//factor)

    def __len__(self):
        return self.stop - self.start

    def next(self):
        return Location(self.stop)

    def __str__(self):
        if len(self) == 1:
            return '{}'.format(self.start)
        else:
            return '{}…{}'.format(self.start, self.stop-1)

    def align(self, step):
        start = (self.start // step) * step
        stop = (self.stop // step + 1) * step
        return Location(start, stop)

    def range(self, *, step=1, align=False):
        assert step > 0
        if align:
            start = (self.start // step) * step
            stop = (self.stop // step + 1) * step
        else:
            start = self.start
            stop = self.stop
        for idx in range(start, stop, step):
            yield Location(idx, idx+step)

    def reverse(self, size):
        return Location(size-self.stop, size-self.start)
