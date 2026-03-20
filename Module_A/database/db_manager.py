"""Database Manager and Performance Analysis Module.

This module provides high-level database management functionality and comprehensive
performance benchmarking capabilities. It includes:

- DatabaseManager: Multi-table management system
- PerformanceAnalyzer: Automated benchmarking framework with performance metrics
- BenchmarkResult: Data container for benchmark results

The PerformanceAnalyzer compares B+ Tree operations against a BruteForce baseline
to demonstrate performance improvements across insert, delete, search, and range
query operations.
"""

from dataclasses import dataclass
from typing import Dict, List

import time
import random
import tracemalloc

from .bplustree import BPlusTree
from .bruteforce import BruteForceDB
from .table import Table


@dataclass
class BenchmarkResult:
    """Container for individual benchmark results.
    
    Attributes:
        size: Number of records in the dataset
        insert_bptree_s: Time (seconds) for B+ Tree insertions
        insert_bruteforce_s: Time (seconds) for BruteForce insertions
        search_bptree_s: Time (seconds) for B+ Tree searches
        search_bruteforce_s: Time (seconds) for BruteForce searches
        delete_bptree_s: Time (seconds) for B+ Tree deletions
        delete_bruteforce_s: Time (seconds) for BruteForce deletions
        range_bptree_s: Time (seconds) for B+ Tree range queries
        range_bruteforce_s: Time (seconds) for BruteForce range queries
        mem_bptree_kb: Peak memory usage (KB) for B+ Tree structure
        mem_bruteforce_kb: Peak memory usage (KB) for BruteForce structure
    """
    size: int
    insert_bptree_s: float
    insert_bruteforce_s: float
    search_bptree_s: float
    search_bruteforce_s: float
    delete_bptree_s: float
    delete_bruteforce_s: float
    range_bptree_s: float
    range_bruteforce_s: float
    mem_bptree_kb: float
    mem_bruteforce_kb: float


class DatabaseManager:
    """Multi-table database management system.
    
    Manages creation, retrieval, and deletion of multiple Table instances
    with B+ Tree backing. Each table is indexed by a unique name.
    
    Attributes:
        _tables: Dictionary mapping table names to Table instances
    """
    
    def __init__(self):
        """Initialize an empty database manager."""
        self._tables: Dict[str, Table] = {}
    
    def create_table(self, name: str, order: int = 4) -> Table:
        """Create a new table with B+ Tree backing.
        
        Time Complexity: O(1)
        
        Args:
            name: Unique table name
            order: B+ Tree order (default 4)
        
        Returns:
            The newly created Table instance
        
        Raises:
            ValueError: If table with that name already exists
        """
        if name in self._tables:
            raise ValueError(f"Table '{name}' already exists")
        
        # Create new Table with specified order
        table = Table(name, order=order)
        self._tables[name] = table
        return table
    
    def get_table(self, name: str) -> Table:
        """Retrieve an existing table by name.
        
        Time Complexity: O(1)
        
        Args:
            name: Table name to retrieve
        
        Returns:
            The Table instance
        
        Raises:
            KeyError: If table does not exist
        """
        if name not in self._tables:
            raise KeyError(f"Table '{name}' does not exist")
        return self._tables[name]
    
    def drop_table(self, name: str) -> None:
        """Delete a table from the database.
        
        Time Complexity: O(1)
        
        Args:
            name: Table name to drop
        
        Raises:
            KeyError: If table does not exist
        """
        if name not in self._tables:
            raise KeyError(f"Table '{name}' does not exist")
        
        # Remove table from dictionary (Python garbage collector handles cleanup)
        del self._tables[name]
    
    def list_tables(self) -> List[str]:
        """Get list of all table names.
        
        Time Complexity: O(n) where n = number of tables
        
        Returns:
            List of table names currently in database
        """
        return list(self._tables.keys())


class PerformanceAnalyzer:
    """Benchmarking framework for comparing B+ Tree vs BruteForce implementations.
    
    Conducts systematic performance tests across multiple dataset sizes and
    measures execution time and memory usage for all major operations.
    """
    
    @staticmethod
    def benchmark(
        dataset_sizes: List[int],
        seed: int = 42,
        order: int = 4,
        search_percent: float = 0.2,
        delete_percent: float = 0.2
    ) -> List[BenchmarkResult]:
        """Execute comprehensive performance benchmark suite.
        
        Compares B+ Tree and BruteForce implementations across insert, search,
        delete, and range query operations. Uses consistent random data across
        both implementations for fair comparison.
        
        Time Complexity: O(n * log(n)) for B+ Tree, O(n^2) for BruteForce
        
        Args:
            dataset_sizes: List of dataset sizes to benchmark (e.g., [100, 500, 1000])
            seed: Random seed for reproducible data generation (default 42)
            order: B+ Tree order (default 4)
            search_percent: Fraction of records to search (default 0.2)
            delete_percent: Fraction of records to delete (default 0.2)
        
        Returns:
            List of BenchmarkResult objects, one per dataset size
        """
        results: List[BenchmarkResult] = []
        
        # Iterate through each dataset size
        for n in dataset_sizes:
            # Set seed for reproducible random data
            random.seed(seed)
            
            # DATA GENERATION PHASE 
            # Generate n random (key, value) pairs with consistent values
            keys = list(range(1, n + 1))
            random.shuffle(keys)
            values = [f"value_{k}" for k in keys]
            
            # Select random subsets for search and delete operations
            num_search = max(1, int(n * search_percent))
            num_delete = max(1, int(n * delete_percent))
            
            search_keys = random.sample(keys, num_search)
            delete_keys = random.sample(keys, num_delete)
            
            # Range query parameters: find all keys between lo and hi
            lo = keys[n // 4]  # 25th percentile
            hi = keys[3 * n // 4]  # 75th percentile
            
            # TABLE INITIALIZATION 
            # Create B+ Tree-backed table and BruteForce baseline
            table = Table("benchmark", order=order)
            brute = BruteForceDB()
            
            # INSERTION BENCHMARK 
            # B+ Tree: Insert all (key, value) pairs sequentially
            t0 = time.perf_counter()
            for k, v in zip(keys, values):
                table.insert(k, v)
            insert_bptree = time.perf_counter() - t0
            
            # BruteForce: Insert same keys and values in same order
            t0 = time.perf_counter()
            for k, v in zip(keys, values):
                brute.insert(k, v)
            insert_bruteforce = time.perf_counter() - t0
            
            # SEARCH BENCHMARK 
            # B+ Tree: Search for 20% of randomly selected keys
            t0 = time.perf_counter()
            for k in search_keys:
                table.select(k)
            search_bptree = time.perf_counter() - t0
            
            # BruteForce: Same search operations
            t0 = time.perf_counter()
            for k in search_keys:
                brute.search(k)
            search_bruteforce = time.perf_counter() - t0
            
            # RANGE QUERY BENCHMARK 
            # B+ Tree: Range query from lo to hi
            t0 = time.perf_counter()
            table.range_query(lo, hi)
            range_bptree = time.perf_counter() - t0
            
            # BruteForce: Same range query
            t0 = time.perf_counter()
            brute.range_query(lo, hi)
            range_bruteforce = time.perf_counter() - t0
            
            # DELETION BENCHMARK 
            # B+ Tree: Delete 20% of randomly selected keys
            t0 = time.perf_counter()
            for k in delete_keys:
                table.delete(k)
            delete_bptree = time.perf_counter() - t0
            
            # BruteForce: Delete same keys
            t0 = time.perf_counter()
            for k in delete_keys:
                brute.delete(k)
            delete_bruteforce = time.perf_counter() - t0
            
            # MEMORY USAGE BENCHMARK 
            # Measure peak memory consumption for each implementation
            mem_bptree = PerformanceAnalyzer._measure_memory_kb(table)
            mem_bruteforce = PerformanceAnalyzer._measure_memory_kb(brute)
            
            # RESULT STORAGE 
            # Store all metrics in BenchmarkResult object
            results.append(
                BenchmarkResult(
                    size=n,
                    insert_bptree_s=insert_bptree,
                    insert_bruteforce_s=insert_bruteforce,
                    search_bptree_s=search_bptree,
                    search_bruteforce_s=search_bruteforce,
                    delete_bptree_s=delete_bptree,
                    delete_bruteforce_s=delete_bruteforce,
                    range_bptree_s=range_bptree,
                    range_bruteforce_s=range_bruteforce,
                    mem_bptree_kb=mem_bptree,
                    mem_bruteforce_kb=mem_bruteforce,
                )
            )
        
        return results
    
    @staticmethod
    def _measure_memory_kb(obj: object) -> float:
        """Measure peak memory usage of an object in kilobytes.
        
        Uses Python's tracemalloc module to track memory allocation during
        object traversal. This gives an estimate of the memory footprint of
        the data structure.
        
        Time Complexity: O(n) where n = number of nodes in tree
        
        Args:
            obj: Object whose memory usage should be measured
        
        Returns:
            Peak memory usage in kilobytes (float)
        """
        # Start memory tracking to measure allocation across all threads
        tracemalloc.start()
        
        # Force object traversal by converting to string representation
        # This ensures Python evaluates the entire object structure
        _ = repr(obj)
        
        # Get peak memory usage recorded during object traversal
        _, peak = tracemalloc.get_traced_memory()
        
        # Stop memory tracking to clean up profiling overhead
        tracemalloc.stop()
        
        # Convert bytes to kilobytes
        return peak / 1024.0
