import pytest

import packagerouting.__main__ as main


@pytest.fixture(scope="session")
def setup():
    main.load_data()


def test_distance_graph(setup):
    assert ('1' in main.distance_graph.nodes) == True


def test_location_dict(setup):
    assert ('1' in main.location_dict) == True


def test_package_table(setup):
    assert ('1' in main.package_table) == True