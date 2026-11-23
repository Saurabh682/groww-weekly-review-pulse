"""Data models for the weekly pulse note and validation (Phase 3)."""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Quote:
    """A verbatim sentence extracted from an eligible review."""
    text: str
    source_review_id: str
    rating: int
    theme_label: str
    date: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ThemeSummary:
    """Summary of a theme included in the weekly pulse."""
    theme_id: str
    label: str
    description: str
    one_liner: str
    review_count: int
    share_pct: float
    avg_rating: float
    neg_share: float
    is_top3: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ActionItem:
    """An action item tied to a top-3 theme."""
    theme_label: str
    text: str
    owner_team: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


STORE_LABELS = {"play_store": "Google Play", "app_store": "App Store"}


@dataclass
class StoreCoverage:
    platform: str
    reviews: int
    caveat: Optional[str] = None

    @property
    def label(self) -> str:
        return STORE_LABELS[self.platform]

    def to_dict(self) -> Dict[str, Any]:
        return {"platform": self.platform, "reviews": self.reviews, "caveat": self.caveat}


def default_store_coverage() -> List[StoreCoverage]:
    return [StoreCoverage("play_store", 0)]


@dataclass
class WeeklyPulseNote:
    """The complete structured weekly review pulse note."""
    week_start: str
    window_start: str
    window_end: str
    app_name: str
    store_coverage: List[StoreCoverage] = field(default_factory=default_store_coverage)
    total_reviews: int = 0
    analyzed_reviews: int = 0
    avg_rating: float = 0.0
    top_themes: List[ThemeSummary] = field(default_factory=list)
    quotes: List[Quote] = field(default_factory=list)
    actions: List[ActionItem] = field(default_factory=list)
    coverage_weeks: float = 8.0
    short_coverage_flag: bool = False
    policy_allows_fewer: bool = False

    @property
    def top_theme_labels(self) -> List[str]:
        return [t.label for t in self.top_themes]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "week_start": self.week_start,
            "app_name": self.app_name,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "store_coverage": [c.to_dict() for c in self.store_coverage],
            "total_reviews": self.total_reviews,
            "analyzed_reviews": self.analyzed_reviews,
            "avg_rating": round(self.avg_rating, 2),
            "coverage_weeks": round(self.coverage_weeks, 1),
            "short_coverage_flag": self.short_coverage_flag,
            "top_themes": [t.to_dict() for t in self.top_themes],
            "quotes": [q.to_dict() for q in self.quotes],
            "actions": [a.to_dict() for a in self.actions],
        }
