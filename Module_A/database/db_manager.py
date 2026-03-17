from __future__ import annotations

import random
import time
import tracemalloc
from dataclasses import dataclass

from .bruteforce import BruteForceDB
from .table import Table


class DatabaseManager:
    """Simple in-memory database manager for multiple tables."""

    def __init__(self, default_order: int = 4) -> None:
        self.default_order = default_order
        self._tables: dict[str, Table] = {}

    def create_table(self, table_name: str, order: int | None = None) -> Table:
        if table_name in self._tables:
            raise ValueError(f"Table '{table_name}' already exists")
        table = Table(table_name, order=order or self.default_order)
        self._tables[table_name] = table
        return table

    def get_table(self, table_name: str) -> Table:
        if table_name not in self._tables:
            raise KeyError(f"Table '{table_name}' does not exist")
        return self._tables[table_name]

    def drop_table(self, table_name: str) -> None:
        if table_name not in self._tables:
            raise KeyError(f"Table '{table_name}' does not exist")
        del self._tables[table_name]

    def list_tables(self) -> list[str]:
        return sorted(self._tables.keys())


@dataclass
class BenchmarkResult:
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


class PerformanceAnalyzer:
    """Compares B+ tree-backed table with brute-force storage."""

    def benchmark(self, sizes: list[int], seed: int = 7) -> list[BenchmarkResult]:
        random.seed(seed)
        results: list[BenchmarkResult] = []

        for n in sizes:
            keys = random.sample(range(n * 20), n)
            search_keys = random.sample(keys, min(200, n))
            delete_keys = random.sample(keys, min(200, n))
            lo, hi = sorted(random.sample(keys, 2)) if n >= 2 else (0, 0)

            table = Table("bench", order=8)
            brute = BruteForceDB()

            t0 = time.perf_counter()
            for k in keys:
                table.insert(k, {"id": k})
            insert_bptree = time.perf_counter() - t0

            t0 = time.perf_counter()
            for k in keys:
                brute.insert(k, {"id": k})
            insert_bruteforce = time.perf_counter() - t0

            t0 = time.perf_counter()
            for k in search_keys:
                table.select(k)
            search_bptree = time.perf_counter() - t0

            t0 = time.perf_counter()
            for k in search_keys:
                brute.search(k)
            search_bruteforce = time.perf_counter() - t0

            t0 = time.perf_counter()
            table.range_query(lo, hi)
            range_bptree = time.perf_counter() - t0

            t0 = time.perf_counter()
            brute.range_query(lo, hi)
            range_bruteforce = time.perf_counter() - t0

            t0 = time.perf_counter()
            for k in delete_keys:
                table.delete(k)
            delete_bptree = time.perf_counter() - t0

            t0 = time.perf_counter()
            for k in delete_keys:
                brute.delete(k)
            delete_bruteforce = time.perf_counter() - t0

            mem_bptree = self._measure_memory_kb(table)
            mem_bruteforce = self._measure_memory_kb(brute)

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
        tracemalloc.start()
        _ = repr(obj)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return peak / 1024.0
