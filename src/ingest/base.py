"""Base interface for review ingestion adapters."""

from typing import Iterable, Protocol


class ReviewSource(Protocol):
    name: str

    def fetch(self, window_start: str, window_end: str) -> Iterable[dict]:
        """Fetch raw review records for the given date window."""
        ...
