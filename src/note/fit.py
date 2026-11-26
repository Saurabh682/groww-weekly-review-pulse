import re
from typing import Dict, Iterable, List

from src.domains.pack import DomainPack

DISAMBIGUATION_SUFFIX = re.compile(r"\s+\d+$")
LABEL_WORD = re.compile(r"[a-z]{3,}")


def base_label(label: str) -> str:
    return DISAMBIGUATION_SUFFIX.sub("", label).strip()


def theme_keywords(label: str, pack: DomainPack) -> List[str]:
    base = base_label(label)
    return pack.label_keywords.get(base) or LABEL_WORD.findall(base.lower())


def keyword_hits(sentence: str, keywords: Iterable[str]) -> int:
    lowered = sentence.lower()
    return sum(1 for kw in keywords if re.search(r"\b" + re.escape(kw), lowered))


def fits_theme(sentence: str, label: str, pack: DomainPack) -> bool:
    own = keyword_hits(sentence, theme_keywords(label, pack))
    if own == 0:
        return False
    rivals: Dict[str, List[str]] = {k: v for k, v in pack.label_keywords.items() if k != base_label(label)}
    return all(keyword_hits(sentence, kws) <= own for kws in rivals.values())
