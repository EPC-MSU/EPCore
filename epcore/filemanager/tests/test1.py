from ..filemanager import save
from ..filemanager import Pin


def test_file():
    assert save([Pin()]) == 4


def other_test():
    assert 2 * 2 == 4
