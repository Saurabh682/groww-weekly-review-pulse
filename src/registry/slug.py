import re
import unicodedata
from typing import Iterable

SLUG_MAX_CHARS = 40
DISPLAY_NAME_MAX_CHARS = 80
FALLBACK_SLUG = "app"
NON_SLUG = re.compile(r"[^a-z0-9]+")


class InvalidDisplayName(ValueError):
    pass


def clean_display_name(display_name: str) -> str:
    value = " ".join((display_name or "").split())[:DISPLAY_NAME_MAX_CHARS].strip()
    if not value:
        raise InvalidDisplayName("Display name is empty.")
    return value


def slugify(display_name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", display_name).encode("ascii", "ignore").decode("ascii")
    slug = NON_SLUG.sub("-", ascii_name.lower()).strip("-")[:SLUG_MAX_CHARS].strip("-")
    return slug or FALLBACK_SLUG


def unique_app_key(display_name: str, existing: Iterable[str]) -> str:
    taken = set(existing)
    base = slugify(display_name)
    if base not in taken:
        return base
    n = 2
    while True:
        suffix = f"-{n}"
        candidate = f"{base[:SLUG_MAX_CHARS - len(suffix)].rstrip('-')}{suffix}"
        if candidate not in taken:
            return candidate
        n += 1
