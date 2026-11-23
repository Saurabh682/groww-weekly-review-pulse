import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import List

from src.clean.dedupe import deduplicate_reviews
from src.clean.lang import detect_language
from src.clean.low_info import check_low_info_distribution, is_low_info
from src.clean.pii import scrub_pii
from src.store.models import ReviewRecord

RAW_ARCHIVE_FIELDS = ("platform", "rating", "title", "text", "date", "app_version")


@dataclass
class CleanBatch:
    records: List[ReviewRecord]
    dedupe_dropped: int
    pii_redacted_reviews: int
    pii_tokens_scrubbed: int
    low_info_count: int
    low_info_share: float
    all_low_info: bool


def review_id_for(platform: str, date: str, cleaned_text: str) -> str:
    return hashlib.sha256(f"{platform}|{date}|{cleaned_text}".encode("utf-8")).hexdigest()[:16]


def archive_raw_records(raw_records: List[dict], archive_path: Path) -> None:
    archive_dir = archive_path.parent
    archive_dir.mkdir(parents=True, exist_ok=True)
    with open(archive_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RAW_ARCHIVE_FIELDS)
        writer.writeheader()
        for r in raw_records:
            writer.writerow({k: r.get(k) for k in RAW_ARCHIVE_FIELDS})


def clean_raw_record(r: dict) -> tuple[ReviewRecord, int]:
    title_res = scrub_pii(r.get("title") or "", is_title=True)
    text_res = scrub_pii(r.get("text") or "")
    pii_found = 1 if (title_res.pii_found or text_res.pii_found) else 0
    lang_res = detect_language(text_res.cleaned_text)
    record = ReviewRecord(
        review_id=review_id_for(r["platform"], r["date"], text_res.cleaned_text),
        platform=r["platform"],
        rating=r["rating"],
        title=title_res.cleaned_text or None,
        text=text_res.cleaned_text,
        date=r["date"],
        app_version=r.get("app_version"),
        lang=lang_res.lang,
        low_info=1 if is_low_info(text_res.cleaned_text) else 0,
        pii_found=pii_found,
        quote_eligible=1 if (lang_res.quote_eligible and text_res.quote_eligible and not pii_found) else 0,
        raw_hash=hashlib.sha256(r["text"].encode("utf-8")).hexdigest()[:16],
    )
    return record, title_res.redaction_count + text_res.redaction_count


def clean_raw_reviews(raw_records: List[dict], archive_path: Path) -> CleanBatch:
    deduped, dropped = deduplicate_reviews(raw_records)
    archive_raw_records(deduped, archive_path)
    records: List[ReviewRecord] = []
    redacted_reviews = 0
    tokens = 0
    for raw in deduped:
        record, redactions = clean_raw_record(raw)
        if record.pii_found:
            redacted_reviews += 1
            tokens += redactions
        records.append(record)
    distribution = check_low_info_distribution(records)
    return CleanBatch(
        records=records,
        dedupe_dropped=dropped,
        pii_redacted_reviews=redacted_reviews,
        pii_tokens_scrubbed=tokens,
        low_info_count=distribution["low_info_count"],
        low_info_share=distribution["low_info_share"],
        all_low_info=distribution["all_low_info"],
    )
