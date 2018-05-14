from hypothesis import assume
from hypothesis import given
from hypothesis.strategies import integers

from regulator.location import Location


def test_location():
    assert Location(1) == Location(1, 2)
    assert Location(1, 2)+2 == Location(3)
    assert Location(3)-2 == Location(1)
    assert Location(1) < Location(2)
    assert Location(1) < Location(1, 3)

    assert (Location(1, 4) & Location(3,6)) == Location(3)
    assert (Location(1) & Location(1, 3)) ==  Location(1)
    assert (Location(1) & Location(2)) == None

    assert len(Location(0)) == 1
    assert len(Location(0, 2)) == 2

    assert Location(0).next() == Location(1)
    assert Location(0, 3).next() == Location(3)
    
    assert str(Location(0)) == '0'
    assert str(Location(0, 2)) == '0…1'

    assert Location.from_str('1') == Location(1)
    assert Location.from_str('1…2') == Location(1, 3)
    assert Location.from_str('1..2') == Location(1, 3)

    assert Location(8, 16).reverse(32) == Location(16, 24)

@given(start=integers())
def test_start(start):
    assert Location(start).start == start

@given(start=integers(0), size=integers(1))
def test_size(start, size):
    l = Location(start, start+size)
    assert l.start == start
    assert l.stop == start+size
    assert len(l) == size

@given(start=integers(0), size=integers(1), width=integers(1))
def test_reverse(start, size, width):
    assume(size<=width)

    l = Location(start, start+size)
    assert l.start == start
    assert len(l) == size
    r = l.reverse(width)
    assert len(l) == size
    assert r.start == width-l.stop
