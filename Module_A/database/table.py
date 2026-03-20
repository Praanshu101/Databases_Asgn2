# Table Abstraction Layer
# Provides a clean database table interface wrapping the B+ tree index.
# Abstracts away low-level B+ tree details from user code.

from __future__ import annotations

from .bplustree import BPlusTree


class Table:
    """Table abstraction backed by a B+ tree index.
    
    Provides a standard database table interface with columns abstracted as
    key-value records. All records are indexed by a primary key (integer).
    Supports insert, delete, update, search, range queries, and bulk retrieval.
    """

    def __init__(self, name: str, order: int = 4) -> None:
        """Initialize a table with specified name and B+ tree order.
        
        Args:
            name: Name of the table (for identification purposes).
            order: B+ tree order determining branching factor (default=4).
        """
        self.name = name  # Table identifier
        self.index = BPlusTree(order=order)  # B+ tree index for key-value storage

    def insert(self, key: int, record: object) -> None:
        """Insert or update a record in the table.
        
        Time Complexity: O(log n)
        
        Args:
            key: The primary key (integer) for this record.
            record: The record object (can be dict, tuple, or any Python object).
        """
        # Delegate to B+ tree insert operation
        self.index.insert(key, record)

    def delete(self, key: int) -> bool:
        """Delete a record from the table by primary key.
        
        Time Complexity: O(log n)
        
        Args:
            key: The primary key to delete.
        
        Returns:
            True if record was deleted, False if not found.
        """
        # Delegate to B+ tree delete operation
        return self.index.delete(key)

    def update(self, key: int, new_record: object) -> bool:
        """Update the record associated with a key.
        
        Time Complexity: O(log n)
        
        Args:
            key: The primary key to update.
            new_record: The new record value.
        
        Returns:
            True if record existed and was updated, False if not found.
        """
        # Delegate to B+ tree update operation
        return self.index.update(key, new_record)

    def select(self, key: int) -> object | None:
        """Retrieve a single record by primary key.
        
        Time Complexity: O(log n)
        
        Args:
            key: The primary key to search for.
        
        Returns:
            The record if found, None otherwise.
        """
        # Delegate to B+ tree search operation
        return self.index.search(key)

    def range_query(self, start_key: int, end_key: int) -> list[tuple[int, object]]:
        """Retrieve all records with keys in a range.
        
        Time Complexity: O(log n + k) where k is number of results.
        
        Args:
            start_key: Lower bound of range (inclusive).
            end_key: Upper bound of range (inclusive).
        
        Returns:
            List of (key, record) tuples for keys in range, sorted by key.
        """
        # Delegate to B+ tree range query operation
        return self.index.range_query(start_key, end_key)

    def all_records(self) -> list[tuple[int, object]]:
        """Retrieve all records from the table in sorted key order.
        
        Time Complexity: O(n)
        
        Returns:
            List of all (key, record) tuples sorted by key.
        """
        # Delegate to B+ tree get_all operation
        return self.index.get_all()
