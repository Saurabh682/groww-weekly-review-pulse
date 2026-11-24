CREATE TABLE IF NOT EXISTS reviews (
    review_id TEXT PRIMARY KEY,
    platform TEXT NOT NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title TEXT,
    text TEXT NOT NULL,
    date TEXT NOT NULL,
    app_version TEXT,
    lang TEXT NOT NULL DEFAULT 'en',
    low_info INTEGER NOT NULL DEFAULT 0,
    pii_found INTEGER NOT NULL DEFAULT 0,
    quote_eligible INTEGER NOT NULL DEFAULT 1,
    raw_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reviews_date ON reviews(date);
CREATE INDEX IF NOT EXISTS idx_reviews_platform_date ON reviews(platform, date);
CREATE INDEX IF NOT EXISTS idx_reviews_low_info ON reviews(low_info);

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    week_start TEXT NOT NULL,
    status TEXT NOT NULL,
    total_reviews INTEGER NOT NULL DEFAULT 0,
    analyzed_reviews INTEGER NOT NULL DEFAULT 0,
    avg_rating REAL NOT NULL DEFAULT 0.0,
    coverage_weeks REAL NOT NULL DEFAULT 0.0,
    created_at TEXT NOT NULL,
    window_start TEXT,
    window_end TEXT,
    error TEXT,
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS themes (
    theme_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    label TEXT NOT NULL,
    description TEXT NOT NULL,
    review_count INTEGER NOT NULL,
    share_pct REAL NOT NULL,
    avg_rating REAL NOT NULL,
    is_top3 INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS review_themes (
    review_id TEXT NOT NULL,
    theme_id TEXT NOT NULL,
    distance REAL,
    PRIMARY KEY (review_id, theme_id),
    FOREIGN KEY(review_id) REFERENCES reviews(review_id),
    FOREIGN KEY(theme_id) REFERENCES themes(theme_id)
);

CREATE TABLE IF NOT EXISTS publish_state (
    week_start TEXT PRIMARY KEY,
    doc_id TEXT,
    doc_url TEXT,
    draft_id TEXT,
    content_hash TEXT,
    updated_at TEXT NOT NULL
);
