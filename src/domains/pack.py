from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class OneLinerRule:
    label_triggers: Tuple[str, ...]
    text: str


@dataclass(frozen=True)
class ActionBlueprint:
    owner: str
    text: str


@dataclass(frozen=True)
class DomainPack:
    name: str
    label_keywords: Dict[str, List[str]] = field(default_factory=dict)
    one_liners: Tuple[OneLinerRule, ...] = ()
    positive_one_liner: str = ""
    actions: Dict[str, ActionBlueprint] = field(default_factory=dict)
