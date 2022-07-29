import time
from typing import List
from collections.abc import Hashable
from collections import defaultdict


class HashTable:
    """
    Ordered Hash table using Robin Hood hashing. 
    Checks load factor and doubles capacity if necessary on insertion. 
    """
    def __init__(self, capacity: int = 16):
        self.table = [None] * capacity
        self.capacity = capacity
        self.size = 0
        self.items = DLList()

    def _insert(self, key, value):
        """Safe insertion (checks table capacity and packs an item into a HashedItem object)."""
        self.size += 1
        if self.size / self.capacity > 0.9:
            self.__increase_capacity()
        node = DLList.Node(HashTable.HashedItem(key, value))
        self.__dangerous_insert(node)

    def __dangerous_insert(self, original_node, reinsertion=False):
        """Actual insertion, not safe to use directly."""
        table = self.table
        node = original_node
        idx = node.item.hash
        node.item.probe = 0
        while True:
            idx = idx % self.capacity
            if not table[idx]:
                table[idx] = node
                break
            elif table[idx].item.key == node.item.key:
                table[idx].item = node.item # Change the value rather than insert new node
                reinsertion = True
                break
            elif table[idx].item.probe < node.item.probe:
                node, table[idx] = table[idx], node
            idx += 1
            node.item.probe += 1
        if not reinsertion:
            self.items.tail_insert(original_node)
            
    def __increase_capacity(self):
        """Double table capacity and reinserts items in proper buckets."""
        prev_items = self.table
        self.capacity *= 2
        self.table = [None] * self.capacity
        # Re-insert items
        for item in prev_items:
            if item is not None:
                self.__dangerous_insert(item, reinsertion=True)
 
    def _delete(self, idx):
        """Delete item using backwards shift technique.""" 
        self.size -= 1
        self.items.delete_node(self.table[idx])
        while self.table[idx]:
            prev = idx
            idx = (idx + 1) % self.capacity
            if self.table[idx] is None or self.table[idx].item.probe == 0:
                self.table[prev] = None
                break
            else:
                self.table[prev] = self.table[idx]
                self.table[prev].item.probe -= 1

    def _find(self, key):
        """Find item using linear probing (could be improved with smart probing)."""
        table = self.table
        idx = hash(key)
        probe = 0
        while True:
            idx = idx % self.capacity
            if not table[idx]:
                return None
            elif table[idx].item.key == key:
                return idx, table[idx].item.value
            elif table[idx].item.probe < probe:
                return None
            else:
                idx += 1
                probe +=1

    def pop(self, key):
        """Finds, deletes, and returns the item associated with the key."""
        if not self.__hashable(key):
            raise TypeError(f"unhashable type: {type(key).__name__}")
        if (result := self._find(key)) is not None:
            self._delete(result[0])
            return result[1]
        else:
            raise KeyError(key)

    def __hashable(self, key):
        return isinstance(key, Hashable)

    def __len__(self):
        return self.size

    def __contains__(self, key):
        """Returns boolean representing whether the key is in the table or not."""
        if not self.__hashable(key):
            raise TypeError(f"unhashable type: {type(key).__name__}")
        if self._find(key) is not None:
            return True
        else:
            return False

    def __getitem__(self, key):
        """Finds and returns item associated with key."""
        if not self.__hashable(key):
            raise TypeError(f"unhashable type: {type(key).__name__}")
        if (result := self._find(key)) is not None:
            return result[1]
        else:
            raise KeyError(key)

    def __setitem__(self, key, value):
        """Inserts a new item into the table."""
        if not self.__hashable(key):
            raise TypeError(f"unhashable type: {type(key).__name__}")
        self._insert(key, value)
    
    def __delitem__(self, key):
        """Delete item from table."""
        if not self.__hashable(key):
            raise TypeError(f"unhashable type: {type(key).__name__}")
        if (result := self._find(key)) is not None:
            self._delete(result[0])
        else:
            raise KeyError(key)

    def __iter__(self):
        """Yields an iterable for all keys in table."""
        for node in self.items:
            yield node.item.key

    class HashedItem:
        """Local class for wrapping a hash table value."""
        def __init__(self, key, value):
            self.value = value
            self.key = key
            self.hash = hash(key)
            self.probe = 0


class DLList:
    """Doubly linked list. Used to maintain insertion order in hash table."""
    def __init__(self, item=None):
        head = DLList.Node(float('inf'))
        self.head = head.prev = head.next = head
        if item:
            self.head_insert(item)

    def head_insert(self, node):
        """Inserts a node at head."""
        node.prev = self.head
        node.next = self.head.next
        node.prev.next = node
        node.next.prev = node
        return node

    def tail_insert(self, node):
        """Inserts a node at tail."""
        node.next = self.head
        node.prev = self.head.prev
        node.next.prev = node
        node.prev.next = node
        return node

    def delete_node(self, node):
        """Deletes a node."""
        node.prev.next = node.next
        node.next.prev = node.prev

    def __iter__(self):
        """Yields an iterable for all nodes in list."""
        cursor = self.head.next
        while cursor.item != float('inf'):
            yield cursor
            cursor = cursor.next

    class Node:
        def __init__(self, item):
            self.item = item
            self.prev = None
            self.next = None


class Graph:
    """Graph class used for calculating shortest routes using Floyd-Warshall all pairs shortest path algorithm."""
    def __init__(self):
        self.nodes = {}
        self.adj = defaultdict(lambda:defaultdict(lambda:float('inf')))
        self.paths = defaultdict(dict)
        self.valid = False

    def add_node(self, *nodes):
        """Inserts a node into the list of nodes."""
        for v in nodes:
            self.nodes[v] = time.time_ns()  # Touched time

    def add_edge(self, n1, n2, weight):
        """Adds edges and initial path between two nodes with a given weight."""
        self.valid = False
        self.adj[n1][n2] = weight
        self.adj[n2][n1] = weight
        self.add_node(n1, n2)
    
    def calculate_shortest_paths(self):
        """Floyd-Warshall algorithm."""
        paths = self.paths
        nodes = self.nodes
        # Add initial adjacency for path finding
        for n1 in nodes:
            for n2 in nodes:
                if n1 == n2:
                    paths[n1][n2] = Graph.Path(0)
                else:
                    paths[n1][n2] = Graph.Path(self.adj[n1][n2], [n1, n2])
        # Find shortest paths using dynamic programming
        for i in nodes:
            for n1 in nodes:
                for n2 in nodes:
                    test_weight = paths[n1][i].weight + paths[i][n2].weight
                    if test_weight < paths[n1][n2].weight:
                        # Change path
                        paths[n1][n2] = Graph.Path(test_weight, [*paths[n1][i].nodes, *paths[i][n2].nodes[1:]])
        self.valid = True
        
    def get_dist(self, start, end):
        """Returns the shortest path between two points, checks if shortest paths are valid or need to be recomputed."""
        if not self.valid:
            self.calculate_shortest_paths()
        return self.paths[start][end]


    class Path:
        """Class for storing a computed path of nodes."""
        def __init__(self, weight: float = 0, nodes: List = []):
            self.weight: float = weight
            self.nodes = nodes
            self.created = time.time_ns()

        def __lt__(self, other):
            return self.weight < other.weight
        
        def __repr__(self):
            return f"Weight: {self.weight} Path: {' -> '.join([n for n in self.nodes])}"