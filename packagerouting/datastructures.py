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

    def insert(self, key, value):
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
 
    def delete(self, idx):
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

    def find(self, key):
        """Find item using linear probing (could be improved with smart probing)."""
        table = self.table
        idx = hash(key)
        probe = 0
        while True:
            idx = idx % self.capacity
            if not table[idx]:
                return None
            elif table[idx].item.key == key:
                return table[idx].item.value
            elif table[idx].item.probe < probe:
                return None
            else:
                idx += 1
                probe +=1


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