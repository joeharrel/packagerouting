import pytest

from packagerouting.datastructures import Graph


@pytest.fixture
def setup():
    yield Graph()


def test_pathfind(setup):
    graph = setup
    graph.add_edge(0, 1, 1.0)
    graph.add_edge(1, 2, 2.0)
    graph.add_edge(0, 2, 4.0)
    assert graph.get_dist(0, 2).weight == 3.0


def test_newedge(setup):
    graph = setup
    graph.add_edge(0, 1, 1.0)
    graph.add_edge(1, 2, 4.0)
    graph.add_edge(0, 2, 4.0)
    assert graph.get_dist(0, 2).weight == 4.0
    graph.add_edge(1, 2, 2.0)
    assert graph.get_dist(0, 2).weight == 3.0