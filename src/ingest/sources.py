from dataclasses import dataclass, field
from typing import Callable, List, Optional, Protocol, Tuple, Type, TypeVar

T = TypeVar("T")

RETRY_ATTEMPTS = 3
RETRY_BASE_DELAY_S = 2.0


class SourceError(Exception):
    pass


class ListingNotFound(SourceError):
    pass


class SourceUnavailable(SourceError):
    pass


class RetryableStatus(SourceError):
    pass


@dataclass
class SourceResult:
    records: List[dict] = field(default_factory=list)
    fetched: int = 0
    pages: int = 0
    covered_start: Optional[str] = None
    source_limit_hit: bool = False
    feed_gaps: int = 0


class ReviewSource(Protocol):
    platform: str

    def fetch(self, window_start: str, window_end: str) -> SourceResult:
        ...


def call_with_retries(
    call: Callable[[], T],
    retryable: Tuple[Type[BaseException], ...],
    sleep: Callable[[float], None],
    attempts: int = RETRY_ATTEMPTS,
    base_delay_s: float = RETRY_BASE_DELAY_S,
) -> T:
    last: Optional[BaseException] = None
    for attempt in range(1, attempts + 1):
        try:
            return call()
        except retryable as exc:
            last = exc
            if attempt < attempts:
                sleep(base_delay_s * 2 ** (attempt - 1))
    raise SourceUnavailable(f"Store unavailable after {attempts} attempts: {last}") from last


def finish_window(result: SourceResult, reached_start: bool, window_start: str) -> SourceResult:
    result.source_limit_hit = not reached_start or result.feed_gaps > 0
    if not result.source_limit_hit:
        result.covered_start = window_start
    elif result.records:
        result.covered_start = min(r["date"] for r in result.records)
    else:
        result.covered_start = None
    return result
