import pytest

from packagerouting.datastructures import HashTable


@pytest.fixture
def setup():
    yield HashTable()


def test_insert(setup):
    table = setup
    table[-1] = "testing"
    assert table[-1] == "testing"


def test_updatevalue(setup):
    table = setup
    table[-1] = "testing"
    table[-1] = "testing123"
    assert table[-1] == "testing123"


def test_delete(setup):
    table = setup
    table[-1] = "testing"
    del table[-1]
    with pytest.raises(KeyError):
        print(table[-1])
