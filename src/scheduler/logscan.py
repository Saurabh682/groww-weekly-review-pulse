import os
import re
from typing import Dict, Iterable, Iterator, List, Mapping, Set, Tuple

SECRET_ENV_NAMES = (
    "SUPABASE_DB_URL",
    "COMPOSIO_API_KEY",
    "COMPOSIO_GOOGLEDOCS_ACCOUNT_ID",
    "COMPOSIO_GMAIL_ACCOUNT_ID",
    "GITHUB_DISPATCH_TOKEN",
    "GITHUB_TOKEN",
    "SUPABASE_JWT_SECRET",
    "GEMINI_API_KEY",
)
SECRET_PATTERNS = (
    re.compile(r"Bearer\s+[0-9a-f]{24,}", re.IGNORECASE),
    re.compile(r"\b[0-9a-f]{48}\b"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    re.compile(r"\bck_[A-Za-z0-9_\-]{16,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{30,}"),
    re.compile(r"postgres(?:ql)?://[^\s:/]+:[^\s@\[]+@"),
)
EMAIL_PATTERN = re.compile(r"[\w.+\-]+@[\w\-]+(?:\.[\w\-]+)+")
WORD_PATTERN = re.compile(r"\w+")
FRAGMENT_WORDS = 5
SHORT_REVIEW_MIN_WORDS = 3
MIN_SECRET_LENGTH = 8


def words_of(text: str) -> List[str]:
    return WORD_PATTERN.findall(text.casefold())


def fragments(words: List[str], size: int) -> Iterator[Tuple[str, ...]]:
    return (tuple(words[i : i + size]) for i in range(len(words) - size + 1))


class LogScanner:
    def __init__(self, log_text: str, environ: Mapping[str, str] = os.environ):
        self._text = log_text
        self._environ = environ
        words = words_of(log_text)
        self._fragments: Dict[int, Set[Tuple[str, ...]]] = {
            size: set(fragments(words, size)) for size in range(SHORT_REVIEW_MIN_WORDS, FRAGMENT_WORDS + 1)
        }

    def has_secret(self) -> bool:
        values = (self._environ.get(name, "").strip() for name in SECRET_ENV_NAMES)
        leaked_value = any(len(v) >= MIN_SECRET_LENGTH and v in self._text for v in values)
        return leaked_value or any(p.search(self._text) for p in SECRET_PATTERNS)

    def has_email(self) -> bool:
        return EMAIL_PATTERN.search(self._text) is not None

    def has_review_text(self, review_texts: Iterable[str]) -> bool:
        return any(self._quotes(words_of(text)) for text in review_texts)

    def _quotes(self, review_words: List[str]) -> bool:
        size = min(len(review_words), FRAGMENT_WORDS)
        if size < SHORT_REVIEW_MIN_WORDS:
            return False
        return any(f in self._fragments[size] for f in fragments(review_words, size))

    def findings(self, review_texts: Iterable[str]) -> List[str]:
        checks = (
            ("secret", self.has_secret()),
            ("email", self.has_email()),
            ("review_text", self.has_review_text(review_texts)),
        )
        return [name for name, hit in checks if hit]
