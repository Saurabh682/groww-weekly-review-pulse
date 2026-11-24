from typing import Optional

from src.domains.finance import FINANCE_PACK
from src.domains.generic import GENERIC_PACK
from src.domains.pack import ActionBlueprint, DomainPack, OneLinerRule

CATEGORY_PACKS = {
    "finance": FINANCE_PACK,
}


def domain_pack_for(category: Optional[str]) -> DomainPack:
    return CATEGORY_PACKS.get((category or "").strip().lower(), GENERIC_PACK)


__all__ = ["ActionBlueprint", "DomainPack", "OneLinerRule", "domain_pack_for", "FINANCE_PACK", "GENERIC_PACK"]
