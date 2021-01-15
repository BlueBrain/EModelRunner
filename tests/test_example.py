"""Sample nosetest file."""
from emodelrunner import example


def test_add_3_4():
    """Adding 3 and 4."""
    assert example.add(3, 4) == 7


def test_add_0_0():
    """Adding zero to zero."""
    assert example.add(0, 0) == 0
