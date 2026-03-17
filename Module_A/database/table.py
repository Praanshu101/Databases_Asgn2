from __future__ import annotations

from .bplustree import BPlusTree


class Table:
    """Table abstraction backed by a B+ tree index."""

    def __init__(self, name: str, order: int = 4) -> None:
        self.name = name
        self.index = BPlusTree(order=order)

    def insert(self, key: int, record: object) -> None:
        self.index.insert(key, record)

    def delete(self, key: int) -> bool:
        return self.index.delete(key)

    def update(self, key: int, new_record: object) -> bool:
        return self.index.update(key, new_record)

    def select(self, key: int) -> object | None:
        return self.index.search(key)

    def range_query(self, start_key: int, end_key: int) -> list[tuple[int, object]]:
        return self.index.range_query(start_key, end_key)

    def all_records(self) -> list[tuple[int, object]]:
        return self.index.get_all()
