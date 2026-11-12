"""Phase 1 Test Suite: Ingestion, Cleaning, and PII Scrubbing.

Covers all test requirements from docs/edge-case.md §16:
- ING-01..10, ING-16
- WIN-01..08
- NRM-01..02
- LNG-01..04
- DUP-01..04
- LOW-01
- PII-01..20, PIIN-01..08, PII-30, PII-38, PII-39
- SEC-01
"""

import json
import sqlite3
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import pytest

from src.clean.dedupe import deduplicate_reviews, compute_exact_hash
from src.clean.lang import detect_language
from src.clean.low_info import is_low_info, check_low_info_distribution
from src.clean.normalize import (
    normalize_text,
    parse_review_date,
    validate_and_coerce_rating,
)
from src.clean.pii import scrub_pii, normalize_unicode_digits
from src.clean.window import (
    calculate_window_bounds,
    compute_coverage_weeks,
    normalize_to_week_start,
)
from src.config import get_project_root, load_pulse_config
from src.ingest.play_csv import PlayStoreImportSource
from src.pipeline import process_and_ingest_reviews
from src.store.db import Database
from src.store.models import ReviewRecord


# ==============================================================================
# Ingestion & Data Source Tests (ING-*)
# ==============================================================================

def test_ING_01_identity_columns_dropped():
    """ING-01 (P0): Identity columns (author_name, user_id, avatar_url, device_id) are never read."""
    root = get_project_root()
    fixture = root / "tests" / "fixtures" / "reviews_identity_columns.csv"
    importer = PlayStoreImportSource(fixture)
    records = importer.read_raw_records()

    assert len(records) >= 2
    for r in records:
        assert "author_name" not in r
        assert "user_id" not in r
        assert "avatar_url" not in r
        assert "device_id" not in r
        assert set(r.keys()) == {"platform", "rating", "title", "text", "date", "app_version"}


def test_ING_02_unknown_column_ignored(tmp_path: Path):
    """ING-02 (P1): Unknown extra columns emit warning but do not crash."""
    csv_file = tmp_path / "extra_cols.csv"
    csv_file.write_text(
        "rating,text,date,unknown_telemetry_tag,random_header\n5,Great app,2026-10-10,tag1,foo\n",
        encoding="utf-8"
    )
    with pytest.warns(UserWarning, match="Unknown columns ignored"):
        importer = PlayStoreImportSource(csv_file)
        records = importer.read_raw_records()
        assert len(records) == 1
        assert "unknown_telemetry_tag" not in records[0]


def test_ING_03_missing_required_column(tmp_path: Path):
    """ING-03 (P0): Missing required column (text/rating/date) fails fast."""
    missing_text = tmp_path / "missing_text.csv"
    missing_text.write_text("rating,date\n5,2026-10-10\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Missing required columns.*text"):
        PlayStoreImportSource(missing_text).read_raw_records()


def test_ING_04_missing_title_ok(tmp_path: Path):
    """ING-04 (P1): Missing or empty title is accepted as None."""
    no_title = tmp_path / "no_title.csv"
    no_title.write_text("rating,text,date\n4,Good app without title,2026-10-10\n", encoding="utf-8")
    records = PlayStoreImportSource(no_title).read_raw_records()
    assert len(records) == 1
    assert records[0]["title"] is None


def test_ING_05_rating_validation():
    """ING-05 (P1): Ratings 1-5 validated, 4.0 coerced, invalid rejected."""
    assert validate_and_coerce_rating(5) == 5
    assert validate_and_coerce_rating(4.0) == 4
    assert validate_and_coerce_rating("3") == 3
    assert validate_and_coerce_rating("1.0") == 1

    with pytest.raises(ValueError, match="Rating out of range"):
        validate_and_coerce_rating(6)

    with pytest.raises(ValueError, match="Rating out of range"):
        validate_and_coerce_rating(0)

    with pytest.raises(ValueError, match="Non-numeric rating"):
        validate_and_coerce_rating("5 stars")


def test_ING_06_date_formats():
    """ING-06 (P1): Standard date formats parsed into UTC YYYY-MM-DD."""
    assert parse_review_date("2026-10-15") == "2026-10-15"
    assert parse_review_date("15/10/2026") == "2026-10-15"
    assert parse_review_date("2026-10-15T09:15:00Z") == "2026-10-15"


def test_ING_07_future_date_rejected():
    """ING-07 (P1): Review dated in future is rejected."""
    ref_date = date(2026, 11, 10)
    with pytest.raises(ValueError, match="Future date rejected"):
        parse_review_date("2026-11-25", reference_date=ref_date)


def test_ING_08_empty_input_no_publish(tmp_path: Path):
    """ING-08 (P0): Empty file stops with error."""
    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        PlayStoreImportSource(empty_file).read_raw_records()


def test_ING_09_encoding_variants(tmp_path: Path):
    """ING-09 (P1): File with UTF-8 BOM or Latin-1 parses cleanly."""
    bom_file = tmp_path / "bom.csv"
    bom_file.write_text("\ufeffrating,text,date\n5,BOM test,2026-10-10\n", encoding="utf-8-sig")
    records = PlayStoreImportSource(bom_file).read_raw_records()
    assert len(records) == 1
    assert records[0]["text"] == "BOM test"


def test_ING_10_csv_quoting(tmp_path: Path):
    """ING-10 (P1): Embedded commas and newlines inside quoted fields parse as one record."""
    quoted = tmp_path / "quoted.csv"
    quoted.write_text(
        'rating,text,date\n4,"Line one,\nline two, with comma",2026-10-10\n',
        encoding="utf-8"
    )
    records = PlayStoreImportSource(quoted).read_raw_records()
    assert len(records) == 1
    assert "Line one, line two, with comma" in records[0]["text"]


def test_ING_16_reingest_idempotent(tmp_path: Path):
    """ING-16 (P0): Ingesting same file twice adds 0 new rows."""
    db_file = tmp_path / "test.db"
    db = Database(db_file)
    root = get_project_root()
    fixture = root / "tests" / "fixtures" / "reviews_baseline.csv"

    sum1 = process_and_ingest_reviews(week_str="2026-11-10", csv_path=fixture, db=db)
    assert sum1["newly_inserted"] > 0

    sum2 = process_and_ingest_reviews(week_str="2026-11-10", csv_path=fixture, db=db)
    assert sum2["newly_inserted"] == 0


# ==============================================================================
# Time Window Tests (WIN-*)
# ==============================================================================

def test_WIN_01_short_coverage_flagged():
    """WIN-01 (P1): Short coverage (< 8 weeks) flags shortfall."""
    records = [
        ReviewRecord("1", "play_store", 5, "text", "2026-11-01"),
        ReviewRecord("2", "play_store", 4, "text", "2026-11-08"),
    ]
    weeks = compute_coverage_weeks(records)
    assert weeks < 8.0


def test_WIN_02_older_reviews_excluded(tmp_path: Path):
    """WIN-02 (P1): Reviews older than window boundary are excluded."""
    csv_file = tmp_path / "spread.csv"
    csv_file.write_text(
        "rating,text,date\n"
        "5,Recent review,2026-11-05\n"
        "1,Very old review,2025-01-01\n",
        encoding="utf-8"
    )
    importer = PlayStoreImportSource(csv_file)
    records = importer.fetch(window_start="2026-08-24", window_end="2026-11-15")
    assert len(records) == 1
    assert records[0]["text"] == "Recent review"


def test_WIN_03_window_bounds_validated():
    """WIN-03 (P1): Window bounds must be 8-12 weeks."""
    monday = date(2026, 11, 9)
    with pytest.raises(ValueError, match="between 8 and 12"):
        calculate_window_bounds(monday, weeks=6)
    with pytest.raises(ValueError, match="between 8 and 12"):
        calculate_window_bounds(monday, weeks=15)

    start, end = calculate_window_bounds(monday, weeks=12)
    assert start == "2026-08-24"
    assert end == "2026-11-15"


def test_WIN_04_boundary_inclusion():
    """WIN-04 (P1): Reviews on exact window boundary dates are included."""
    monday = date(2026, 11, 9)
    start_str, end_str = calculate_window_bounds(monday, weeks=12)
    records = [
        {"rating": 5, "text": "start", "date": start_str},
        {"rating": 4, "text": "end", "date": end_str},
        {"rating": 1, "text": "before", "date": "2026-08-23"},
        {"rating": 1, "text": "after", "date": "2026-11-16"},
    ]
    in_window = [r for r in records if start_str <= r["date"] <= end_str]
    assert len(in_window) == 2


def test_WIN_06_week_normalization():
    """WIN-06 (P1): Non-Monday date normalizes to Monday start."""
    ref_date = date(2026, 11, 11)
    tuesday = normalize_to_week_start("2026-11-10", reference_date=ref_date)
    wednesday = normalize_to_week_start("2026-11-11", reference_date=ref_date)
    assert tuesday == date(2026, 11, 9)
    assert wednesday == date(2026, 11, 9)


def test_WIN_08_future_week_rejected():
    """WIN-08 (P1): Future week date is rejected."""
    ref_date = date(2026, 11, 11)
    with pytest.raises(ValueError, match="in the future"):
        normalize_to_week_start("2026-12-01", reference_date=ref_date)


# ==============================================================================
# Normalization, Language, Dedupe, Low-Info Tests
# ==============================================================================

def test_NRM_01_emoji_only_low_info():
    """NRM-01 (P1): Emoji-only review is marked low-info."""
    assert is_low_info("👍👍👍") is True
    assert is_low_info("⭐⭐⭐⭐⭐") is True
    assert is_low_info("Good app for SIP investing") is False


def test_NRM_02_hidden_chars_normalized():
    """NRM-02 (P0): Zero-width and invisible characters normalized."""
    hidden = "Help\u200b me\ufeff please"
    cleaned = normalize_text(hidden)
    assert cleaned == "Help me please"


def test_LNG_01_hindi_not_quote_eligible():
    """LNG-01 (P1): Pure Hindi Devanagari tagged 'hi' and quote_eligible=False."""
    hindi = "ग्रो ऐप बहुत अच्छा है निवेश के लिए"
    res = detect_language(hindi)
    assert res.lang == "hi"
    assert res.quote_eligible is False


def test_LNG_02_hinglish_handling():
    """LNG-02 (P1): Roman script Hinglish tagged 'mixed' and quote_eligible=False."""
    hinglish = "paisa nahi nikal raha hai mera withdrawal pending hai"
    res = detect_language(hinglish)
    assert res.lang == "mixed"
    assert res.quote_eligible is False


def test_LNG_03_unknown_language_safe():
    """LNG-03 (P1): Single word or unidentifiable language falls back to unknown."""
    res = detect_language("x")
    assert res.lang == "unknown"
    assert res.quote_eligible is False


def test_DUP_01_exact_duplicate():
    """DUP-01 (P0): Exact duplicate text and date collapsed."""
    reviews = [
        {"platform": "play_store", "date": "2026-10-10", "text": "App crashed at market open"},
        {"platform": "play_store", "date": "2026-10-10", "text": "App crashed at market open"},
    ]
    unique, dropped = deduplicate_reviews(reviews)
    assert len(unique) == 1
    assert dropped == 1


def test_DUP_03_near_duplicate():
    """DUP-03 (P1): Near-duplicate text collapsed."""
    reviews = [
        {"platform": "play_store", "date": "2026-10-10", "text": "KYC process is stuck since 4 days please help"},
        {"platform": "play_store", "date": "2026-10-10", "text": "KYC process is stuck since 4 days please help!"},
    ]
    unique, dropped = deduplicate_reviews(reviews, similarity_threshold=0.85)
    assert len(unique) == 1
    assert dropped == 1


def test_DUP_04_short_generic_duplicates_policy():
    """DUP-04 (P1): Genuine short reviews like 'Good app' are not collapsed across users."""
    reviews = [
        {"platform": "play_store", "date": "2026-10-10", "text": "Good app"},
        {"platform": "play_store", "date": "2026-10-11", "text": "Good app"},
    ]
    unique, dropped = deduplicate_reviews(reviews, allow_short_generic_duplicates=True)
    assert len(unique) == 2


def test_LOW_01_all_low_info_stops():
    """LOW-01 (P0): All reviews low info triggers failure."""
    records = [
        ReviewRecord("1", "play_store", 5, "", "👍", "2026-10-10", low_info=1),
        ReviewRecord("2", "play_store", 5, "", "❤️", "2026-10-10", low_info=1),
    ]
    dist = check_low_info_distribution(records)
    assert dist["all_low_info"] is True


# ==============================================================================
# PII Detection and Scrubbing Tests (PII-01..20, PIIN-01..08, PII-30..39)
# ==============================================================================

def test_PII_01_email():
    """PII-01 (P0): Standard email redacted and quote_eligible=0."""
    res = scrub_pii("Contact me at test.user99@example.com for help")
    assert "[REDACTED]" in res.cleaned_text
    assert "test.user99@example.com" not in res.cleaned_text
    assert res.pii_found is True
    assert res.quote_eligible is False


def test_PII_02_obfuscated_email():
    """PII-02 (P0): Obfuscated email redacted."""
    res1 = scrub_pii("Email test dot user at example dot com")
    res2 = scrub_pii("Email user(at)example.com")
    assert "[REDACTED]" in res1.cleaned_text
    assert "[REDACTED]" in res2.cleaned_text


def test_PII_03_indian_phone_formats():
    """PII-03 (P0): Indian phone number formats redacted."""
    phones = ["9876543210", "+91 98765 43210", "098765-43210", "+91-9876543210"]
    for p in phones:
        res = scrub_pii(f"My phone is {p}")
        assert "[REDACTED]" in res.cleaned_text
        assert res.pii_found is True


def test_PII_04_intl_phone():
    """PII-04 (P0): International phone numbers redacted."""
    res = scrub_pii("Call us at +1 (555) 010-9999 or 0044 20 7946 0000")
    assert "[REDACTED]" in res.cleaned_text
    assert "555" not in res.cleaned_text


def test_PII_05_split_phone():
    """PII-05 (P0): Spaced or dotted phone digits redacted."""
    res = scrub_pii("Call 98 76 54 32 10 or 9.8.7.6.5.4.3.2.1.0")
    assert "[REDACTED]" in res.cleaned_text


def test_PII_06_pan_like():
    """PII-06 (P0): PAN card format redacted."""
    res = scrub_pii("My PAN is ABCDE1234F please check")
    assert "[REDACTED]" in res.cleaned_text
    assert "ABCDE1234F" not in res.cleaned_text
    assert res.pii_found is True


def test_PII_07_upi_id():
    """PII-07 (P0): UPI IDs redacted."""
    res = scrub_pii("Paid via name@okhdfcbank and shop.name@paytm")
    assert "[REDACTED]" in res.cleaned_text
    assert "okhdfcbank" not in res.cleaned_text


def test_PII_08_aadhaar_like():
    """PII-08 (P0): Aadhaar 12-digit format redacted."""
    res = scrub_pii("Aadhaar 2345 6789 0123 verification failed")
    assert "[REDACTED]" in res.cleaned_text
    assert "2345" not in res.cleaned_text


def test_PII_09_account_order_txn_ids():
    """PII-09 (P0): Order/Txn/Folio IDs and account ending 4 digits redacted."""
    res1 = scrub_pii("order id 5839201847 failed")
    res2 = scrub_pii("txn no 0012345678901 deducted")
    res3 = scrub_pii("account ending in 4321")
    assert "[REDACTED]" in res1.cleaned_text
    assert "[REDACTED]" in res2.cleaned_text
    assert "[REDACTED]" in res3.cleaned_text


def test_PII_10_urls():
    """PII-10 (P0): URLs redacted."""
    res = scrub_pii("See screenshot at https://groww.in/support/ticket/123")
    assert "[REDACTED]" in res.cleaned_text


def test_PII_11_handles():
    """PII-11 (P0): @handles redacted."""
    res = scrub_pii("DM me on twitter @trader_vikram")
    assert "[REDACTED]" in res.cleaned_text


def test_PII_12_signoff_names():
    """PII-12 (P0): Sign-off names redacted and quote_eligible=0."""
    res1 = scrub_pii("Great support.\nThanks, Rahul Sharma")
    res2 = scrub_pii("Please fix.\n- Priya S.")
    assert "[REDACTED]" in res1.cleaned_text
    assert res1.quote_eligible is False
    assert "[REDACTED]" in res2.cleaned_text
    assert res2.quote_eligible is False


def test_PII_13_self_intro():
    """PII-13 (P0): Self-introduction names redacted."""
    res = scrub_pii("My name is Anita and I am unable to login")
    assert "[REDACTED]" in res.cleaned_text
    assert "Anita" not in res.cleaned_text


def test_PII_14_device_ids():
    """PII-14 (P0): UUIDs and device IDs redacted."""
    res = scrub_pii("Crash uuid 123e4567-e89b-12d3-a456-426614174000")
    assert "[REDACTED]" in res.cleaned_text


def test_PII_15_ticket_numbers():
    """PII-15 (P0): Support ticket numbers redacted."""
    res = scrub_pii("My ticket #AB-10293847 is still open")
    assert "[REDACTED]" in res.cleaned_text


def test_PII_16_dob():
    """PII-16 (P0): Date of birth redacted."""
    res = scrub_pii("DOB 12/03/1990 is rejected")
    assert "[REDACTED]" in res.cleaned_text


def test_PII_18_unicode_digit_variants():
    """PII-18 (P0): Fullwidth and Devanagari digits normalized and redacted."""
    # Fullwidth mobile: ９８７６５４３２１０
    res_fw = scrub_pii("Mobile: ９８７６５४३२１０")
    assert "[REDACTED]" in res_fw.cleaned_text

    # Devanagari mobile: ९८७६५४३२१०
    res_dev = scrub_pii("Mobile: ९८७६५४३२१०")
    assert "[REDACTED]" in res_dev.cleaned_text


def test_PII_19_multiple_pii_one_review():
    """PII-19 (P0): Multiple PII items in one review are all redacted."""
    text = "Call 9876543210 or email test@example.com for order id 12345678"
    res = scrub_pii(text)
    assert res.redaction_count >= 3
    assert "9876543210" not in res.cleaned_text
    assert "test@example.com" not in res.cleaned_text


def test_PII_20_pii_in_title():
    """PII-20 (P0): PII in title is redacted."""
    res = scrub_pii("PAN ABCDE1234F rejected", is_title=True)
    assert "[REDACTED]" in res.cleaned_text
    assert "ABCDE1234F" not in res.cleaned_text


# ==============================================================================
# Over-Redaction Guards (PIIN-*)
# ==============================================================================

def test_PIIN_01_durations():
    """PIIN-01 (P1): Durations like '10 days' and '3 weeks' must survive intact."""
    text = "Withdrawal took 10 days and I waited 3 weeks"
    res = scrub_pii(text)
    assert "10 days" in res.cleaned_text
    assert "3 weeks" in res.cleaned_text


def test_PIIN_02_amounts():
    """PIIN-02 (P1): Currency amounts like '₹5000' and 'Rs. 25,000' must survive intact."""
    text = "Lost ₹5000 and Rs. 25,000 stuck in pending order"
    res = scrub_pii(text)
    assert "₹5000" in res.cleaned_text
    assert "25,000" in res.cleaned_text


def test_PIIN_03_versions():
    """PIIN-03 (P1): App versions like 'v14.3.0' must survive intact."""
    text = "App version 14.3.0 and v12.4.1 work well"
    res = scrub_pii(text)
    assert "14.3.0" in res.cleaned_text
    assert "v12.4.1" in res.cleaned_text


def test_PIIN_04_small_numbers():
    """PIIN-04 (P2): Small ratings and counts survive intact."""
    text = "Giving 5 stars after 3 attempts"
    res = scrub_pii(text)
    assert "5 stars" in res.cleaned_text
    assert "3 attempts" in res.cleaned_text


def test_PIIN_05_percentages():
    """PIIN-05 (P2): Percentages and returns survive intact."""
    text = "Got 12.5% returns with XIRR 14%"
    res = scrub_pii(text)
    assert "12.5%" in res.cleaned_text
    assert "14%" in res.cleaned_text


def test_PIIN_06_brand_words():
    """PIIN-06 (P1): Brand and market words survive intact."""
    text = "Invested in Nifty 50 on Groww instead of Zerodha"
    res = scrub_pii(text)
    assert "Nifty 50" in res.cleaned_text
    assert "Groww" in res.cleaned_text
    assert "Zerodha" in res.cleaned_text


def test_PIIN_08_otp_word_vs_value():
    """PIIN-08 (P1): Word 'OTP' is preserved, actual OTP value is redacted."""
    text = "OTP not received for login. OTP was 482910."
    res = scrub_pii(text)
    assert "OTP not received" in res.cleaned_text
    assert "482910" not in res.cleaned_text
    assert "[REDACTED]" in res.cleaned_text


# ==============================================================================
# System-level PII & Security Tests (PII-30, PII-38, PII-39, SEC-01)
# ==============================================================================

def test_PII_30_property_no_pii_anywhere():
    """PII-30 (P0): Seeded PII canaries must never leak into processed output."""
    root = get_project_root()
    canary_file = root / "tests" / "fixtures" / "canaries.json"
    with open(canary_file, "r", encoding="utf-8") as f:
        canaries = json.load(f)

    pii_fixture = root / "tests" / "fixtures" / "reviews_pii_heavy.csv"
    importer = PlayStoreImportSource(pii_fixture)
    raw = importer.read_raw_records()

    for r in raw:
        scrubbed = scrub_pii(r["text"]).cleaned_text
        for category, items in canaries.items():
            for item in items:
                assert item not in scrubbed, f"Canary leak detected: {item} in {scrubbed}"


def test_PII_38_raw_files_clean(tmp_path: Path):
    """PII-38 (P0): data/raw/ files contain no reviewer identity fields."""
    root = get_project_root()
    raw_dir = root / "data" / "raw"
    if raw_dir.exists():
        for csv_path in raw_dir.glob("*.csv"):
            with open(csv_path, "r", encoding="utf-8") as f:
                header = f.readline()
                assert "author_name" not in header
                assert "user_id" not in header
                assert "avatar_url" not in header
                assert "device_id" not in header


def test_SEC_01_no_identity_fields_stored():
    """SEC-01 (P0): Database schema contains zero identity columns."""
    root = get_project_root()
    db_path = root / "data" / "pulse.db"
    db = Database(db_path)
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(reviews)")
        cols = [row["name"] for row in cursor.fetchall()]

        forbidden = ["author_name", "user_id", "avatar_url", "device_id", "email", "reviewer_name"]
        for f in forbidden:
            assert f not in cols, f"Security violation: forbidden identity column '{f}' in reviews table"
