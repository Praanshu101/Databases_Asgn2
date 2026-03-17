from __future__ import annotations

from bisect import bisect_left, bisect_right
from dataclasses import dataclass, field
from itertools import count

from graphviz import Digraph


@dataclass
class BPlusTreeNode:
    is_leaf: bool = False
    keys: list[int] = field(default_factory=list)
    children: list[BPlusTreeNode] = field(default_factory=list)
    values: list[object] = field(default_factory=list)
    next: BPlusTreeNode | None = None


class BPlusTree:
    """In-memory B+ tree supporting insert, delete, exact/range query, and visualization."""

    def __init__(self, order: int = 4) -> None:
        if order < 3:
            raise ValueError("B+ tree order must be at least 3")
        self.order = order
        self.max_keys = order - 1
        self.min_keys = (order + 1) // 2 - 1
        self.root = BPlusTreeNode(is_leaf=True)

    def search(self, key: int) -> object | None:
        node = self._find_leaf(key)
        idx = bisect_left(node.keys, key)
        if idx < len(node.keys) and node.keys[idx] == key:
            return node.values[idx]
        return None

    def insert(self, key: int, value: object) -> None:
        if len(self.root.keys) == self.max_keys:
            new_root = BPlusTreeNode(is_leaf=False, children=[self.root])
            self._split_child(new_root, 0)
            self.root = new_root
        self._insert_non_full(self.root, key, value)

    def _insert_non_full(self, node: BPlusTreeNode, key: int, value: object) -> None:
        if node.is_leaf:
            idx = bisect_left(node.keys, key)
            if idx < len(node.keys) and node.keys[idx] == key:
                node.values[idx] = value
                return
            node.keys.insert(idx, key)
            node.values.insert(idx, value)
            return

        idx = bisect_right(node.keys, key)
        if len(node.children[idx].keys) == self.max_keys:
            self._split_child(node, idx)
            if key >= node.keys[idx]:
                idx += 1
        self._insert_non_full(node.children[idx], key, value)

    def _split_child(self, parent: BPlusTreeNode, index: int) -> None:
        child = parent.children[index]
        mid = len(child.keys) // 2

        new_node = BPlusTreeNode(is_leaf=child.is_leaf)
        if child.is_leaf:
            new_node.keys = child.keys[mid:]
            new_node.values = child.values[mid:]
            child.keys = child.keys[:mid]
            child.values = child.values[:mid]

            new_node.next = child.next
            child.next = new_node

            parent.keys.insert(index, new_node.keys[0])
            parent.children.insert(index + 1, new_node)
            return

        promote_key = child.keys[mid]
        new_node.keys = child.keys[mid + 1 :]
        new_node.children = child.children[mid + 1 :]
        child.keys = child.keys[:mid]
        child.children = child.children[: mid + 1]

        parent.keys.insert(index, promote_key)
        parent.children.insert(index + 1, new_node)

    def delete(self, key: int) -> bool:
        deleted = self._delete(self.root, key)
        if not self.root.is_leaf and len(self.root.keys) == 0:
            self.root = self.root.children[0]
        return deleted

    def _delete(self, node: BPlusTreeNode, key: int) -> bool:
        if node.is_leaf:
            idx = bisect_left(node.keys, key)
            if idx >= len(node.keys) or node.keys[idx] != key:
                return False
            node.keys.pop(idx)
            node.values.pop(idx)
            return True

        idx = bisect_right(node.keys, key)
        child = node.children[idx]

        if len(child.keys) == self.min_keys:
            self._fill_child(node, idx)
            idx = min(idx, len(node.children) - 1)

        deleted = self._delete(node.children[idx], key)

        # Keep separator keys aligned with right child minimum keys.
        for i in range(len(node.keys)):
            if node.children[i + 1].keys:
                node.keys[i] = node.children[i + 1].keys[0]

        return deleted

    def _fill_child(self, node: BPlusTreeNode, index: int) -> None:
        if index > 0 and len(node.children[index - 1].keys) > self.min_keys:
            self._borrow_from_prev(node, index)
            return
        if index < len(node.children) - 1 and len(node.children[index + 1].keys) > self.min_keys:
            self._borrow_from_next(node, index)
            return

        if index < len(node.children) - 1:
            self._merge(node, index)
        else:
            self._merge(node, index - 1)

    def _borrow_from_prev(self, node: BPlusTreeNode, index: int) -> None:
        child = node.children[index]
        sibling = node.children[index - 1]

        if child.is_leaf:
            child.keys.insert(0, sibling.keys.pop())
            child.values.insert(0, sibling.values.pop())
            node.keys[index - 1] = child.keys[0]
            return

        child.keys.insert(0, node.keys[index - 1])
        child.children.insert(0, sibling.children.pop())
        node.keys[index - 1] = sibling.keys.pop()

    def _borrow_from_next(self, node: BPlusTreeNode, index: int) -> None:
        child = node.children[index]
        sibling = node.children[index + 1]

        if child.is_leaf:
            child.keys.append(sibling.keys.pop(0))
            child.values.append(sibling.values.pop(0))
            if sibling.keys:
                node.keys[index] = sibling.keys[0]
            return

        child.keys.append(node.keys[index])
        child.children.append(sibling.children.pop(0))
        node.keys[index] = sibling.keys.pop(0)

    def _merge(self, node: BPlusTreeNode, index: int) -> None:
        left = node.children[index]
        right = node.children[index + 1]

        if left.is_leaf:
            left.keys.extend(right.keys)
            left.values.extend(right.values)
            left.next = right.next
            node.keys.pop(index)
            node.children.pop(index + 1)
            return

        left.keys.append(node.keys.pop(index))
        left.keys.extend(right.keys)
        left.children.extend(right.children)
        node.children.pop(index + 1)

    def update(self, key: int, new_value: object) -> bool:
        node = self._find_leaf(key)
        idx = bisect_left(node.keys, key)
        if idx < len(node.keys) and node.keys[idx] == key:
            node.values[idx] = new_value
            return True
        return False

    def range_query(self, start_key: int, end_key: int) -> list[tuple[int, object]]:
        if start_key > end_key:
            start_key, end_key = end_key, start_key

        node = self._find_leaf(start_key)
        result: list[tuple[int, object]] = []

        while node:
            for i, k in enumerate(node.keys):
                if k > end_key:
                    return result
                if start_key <= k <= end_key:
                    result.append((k, node.values[i]))
            node = node.next

        return result

    def get_all(self) -> list[tuple[int, object]]:
        node = self.root
        while not node.is_leaf:
            node = node.children[0]

        out: list[tuple[int, object]] = []
        while node:
            out.extend(zip(node.keys, node.values))
            node = node.next
        return out

    def visualize_tree(self) -> Digraph:
        dot = Digraph(comment="B+ Tree")
        id_gen = count()
        node_ids: dict[int, str] = {}

        self._add_nodes(dot, self.root, node_ids, id_gen)
        self._add_edges(dot, self.root, node_ids)
        return dot

    def _add_nodes(
        self,
        dot: Digraph,
        node: BPlusTreeNode,
        node_ids: dict[int, str],
        id_gen,
    ) -> None:
        nid = f"n{next(id_gen)}"
        node_ids[id(node)] = nid

        if node.is_leaf:
            label = " | ".join(str(k) for k in node.keys) if node.keys else "<empty>"
            dot.node(nid, f"Leaf: {label}", shape="box")
        else:
            label = " | ".join(str(k) for k in node.keys) if node.keys else "<root>"
            dot.node(nid, f"Internal: {label}")
            for child in node.children:
                self._add_nodes(dot, child, node_ids, id_gen)

    def _add_edges(self, dot: Digraph, node: BPlusTreeNode, node_ids: dict[int, str]) -> None:
        if node.is_leaf:
            if node.next is not None:
                dot.edge(node_ids[id(node)], node_ids[id(node.next)], style="dashed", color="blue")
            return

        for child in node.children:
            dot.edge(node_ids[id(node)], node_ids[id(child)])
            self._add_edges(dot, child, node_ids)

    def _find_leaf(self, key: int) -> BPlusTreeNode:
        node = self.root
        while not node.is_leaf:
            idx = bisect_right(node.keys, key)
            node = node.children[idx]
        return node
