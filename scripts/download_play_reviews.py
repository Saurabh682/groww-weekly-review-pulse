"""Download public reviews for Groww from Google Play Store.

Enforces:
- Explicit allowlist mapping: rating, title, text, date, app_version.
- Drops reviewer identity fields (userName, userImage, reviewId) at the extraction point.
- Saves clean CSV to data/imports/play_reviews.csv.
"""

import csv
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from google_play_scraper import reviews, Sort


def download_groww_reviews(
    app_id: str = "com.nextbillion.groww",
    output_path: str = "groww-weekly-review-pulse/data/imports/play_reviews.csv",
    weeks: int = 12,
    max_reviews: int = 3500
):
    print(f"Downloading reviews for '{app_id}' from Google Play Store...")
    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    cutoff_date = datetime.now(timezone.utc) - timedelta(weeks=weeks)
    cutoff_date_str = cutoff_date.strftime("%Y-%m-%d")
    print(f"Target window: Last {weeks} weeks (cutoff: {cutoff_date_str})")

    all_downloaded = []
    continuation_token = None
    batch_size = 200

    while len(all_downloaded) < max_reviews:
        batch, continuation_token = reviews(
            app_id,
            lang="en",
            country="in",
            sort=Sort.NEWEST,
            count=batch_size,
            continuation_token=continuation_token
        )

        if not batch:
            print("No more reviews returned by Play Store.")
            break

        reached_cutoff = False
        for item in batch:
            review_at = item.get("at")
            if isinstance(review_at, datetime):
                # Ensure UTC
                if review_at.tzinfo is None:
                    review_at = review_at.replace(tzinfo=timezone.utc)
                if review_at < cutoff_date:
                    reached_cutoff = True
                    break
                date_str = review_at.strftime("%Y-%m-%d")
            else:
                date_str = str(review_at)[:10]

            # Allowlist mapping only - NEVER store userName or userImage
            all_downloaded.append({
                "rating": int(item.get("score", 0)),
                "title": "",
                "text": str(item.get("content", "")).replace("\r\n", " ").replace("\n", " ").strip(),
                "date": date_str,
                "app_version": item.get("reviewCreatedVersion") or item.get("appVersion") or "",
            })

        print(f"Fetched {len(all_downloaded)} reviews so far (latest batch date: {batch[-1].get('at')})...")

        if reached_cutoff or not continuation_token:
            if reached_cutoff:
                print(f"Reached 12-week cutoff ({cutoff_date_str}).")
            break

    # Filter out empty texts
    valid_reviews = [r for r in all_downloaded if r["text"]]

    # Write to CSV
    fieldnames = ["rating", "title", "text", "date", "app_version"]
    with open(dest, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(valid_reviews)

    dates = [r["date"] for r in valid_reviews]
    min_date = min(dates) if dates else "N/A"
    max_date = max(dates) if dates else "N/A"

    print("\nDownload complete:")
    print(f"- File saved: {dest.resolve()}")
    print(f"- Total valid reviews: {len(valid_reviews)}")
    print(f"- Date span: {min_date} to {max_date}")

    return valid_reviews


if __name__ == "__main__":
    download_groww_reviews()
