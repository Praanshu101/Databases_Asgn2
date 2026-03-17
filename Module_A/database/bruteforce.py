from __future__ import annotations


class BruteForceDB:
    """Simple baseline key-value store with linear scans for benchmarking."""

    def __init__(self) -> None:
        self._records: list[tuple[int, object]] = []

    def insert(self, key: int, value: object) -> None:
        for i, (k, _) in enumerate(self._records):
            if k == key:
                self._records[i] = (key, value)
                return
        self._records.append((key, value))

    def search(self, key: int) -> object | None:
        for k, v in self._records:
            if k == key:
                return v
        return None

    def delete(self, key: int) -> bool:
        for i, (k, _) in enumerate(self._records):
            if k == key:
                self._records.pop(i)
                return True
        return False

    def update(self, key: int, value: object) -> bool:
        for i, (k, _) in enumerate(self._records):
            if k == key:
                self._records[i] = (key, value)
                return True
        return False

    def range_query(self, start_key: int, end_key: int) -> list[tuple[int, object]]:
        out = [(k, v) for k, v in self._records if start_key <= k <= end_key]
        out.sort(key=lambda x: x[0])
        return out

    def get_all(self) -> list[tuple[int, object]]:
        return sorted(self._records, key=lambda x: x[0])
