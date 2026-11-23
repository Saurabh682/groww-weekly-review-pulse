CREATE TABLE IF NOT EXISTS apps (
    app_key TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    play_package_id TEXT,
    app_store_id TEXT,
    country TEXT NOT NULL DEFAULT 'in',
    lang TEXT NOT NULL DEFAULT 'en',
    category TEXT,
    status TEXT NOT NULL CHECK (status IN ('pending_backfill', 'backfilling', 'active', 'archived', 'failed')),
    created_at TEXT NOT NULL,
    archived_at TEXT,
    CHECK (play_package_id IS NOT NULL OR app_store_id IS NOT NULL)
);

CREATE UNIQUE INDEX IF NOT EXISTS apps_play_live ON apps (play_package_id)
    WHERE status <> 'archived' AND play_package_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS apps_ios_live ON apps (app_store_id)
    WHERE status <> 'archived' AND app_store_id IS NOT NULL;

CREATE TRIGGER IF NOT EXISTS apps_cap_on_insert BEFORE INSERT ON apps
WHEN NEW.status <> 'archived' AND (SELECT COUNT(*) FROM apps WHERE status <> 'archived') >= 5
BEGIN
    SELECT RAISE(ABORT, 'active_app_cap_reached');
END;

CREATE TRIGGER IF NOT EXISTS apps_cap_on_unarchive BEFORE UPDATE OF status ON apps
WHEN OLD.status = 'archived' AND NEW.status <> 'archived'
    AND (SELECT COUNT(*) FROM apps WHERE status <> 'archived') >= 5
BEGIN
    SELECT RAISE(ABORT, 'active_app_cap_reached');
END;

DROP TRIGGER IF EXISTS apps_identity_frozen;
CREATE TRIGGER apps_identity_frozen BEFORE UPDATE OF app_key, play_package_id, app_store_id ON apps
WHEN NEW.app_key IS NOT OLD.app_key
    OR (OLD.play_package_id IS NOT NULL AND NEW.play_package_id IS NOT OLD.play_package_id)
    OR (OLD.app_store_id IS NOT NULL AND NEW.app_store_id IS NOT OLD.app_store_id)
BEGIN
    SELECT RAISE(ABORT, 'app_identity_frozen');
END;

CREATE TABLE IF NOT EXISTS reviews (
    app_key TEXT NOT NULL REFERENCES apps (app_key),
    review_id TEXT NOT NULL,
    platform TEXT NOT NULL CHECK (platform IN ('play_store', 'app_store')),
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title TEXT,
    text TEXT NOT NULL,
    date TEXT NOT NULL,
    app_version TEXT,
    lang TEXT NOT NULL DEFAULT 'en',
    low_info INTEGER NOT NULL DEFAULT 0,
    pii_found INTEGER NOT NULL DEFAULT 0,
    quote_eligible INTEGER NOT NULL DEFAULT 1,
    raw_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (app_key, review_id)
);

CREATE INDEX IF NOT EXISTS reviews_app_date ON reviews (app_key, date);

CREATE TABLE IF NOT EXISTS collection_runs (
    collection_id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_key TEXT NOT NULL REFERENCES apps (app_key),
    platform TEXT NOT NULL CHECK (platform IN ('play_store', 'app_store')),
    mode TEXT NOT NULL CHECK (mode IN ('backfill', 'daily', 'reconcile', 'csv_import')),
    window_start TEXT NOT NULL,
    window_end TEXT NOT NULL,
    covered_start TEXT,
    fetched INTEGER NOT NULL DEFAULT 0,
    inserted INTEGER NOT NULL DEFAULT 0,
    source_limit_hit INTEGER NOT NULL DEFAULT 0,
    feed_gaps INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL CHECK (status IN ('running', 'ok', 'failed', 'skipped_disabled')),
    error TEXT,
    started_at TEXT NOT NULL,
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS runs (
    app_key TEXT NOT NULL REFERENCES apps (app_key),
    run_id TEXT NOT NULL,
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
    finished_at TEXT,
    PRIMARY KEY (app_key, run_id)
);

CREATE TABLE IF NOT EXISTS themes (
    app_key TEXT NOT NULL,
    theme_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    label TEXT NOT NULL,
    description TEXT NOT NULL,
    review_count INTEGER NOT NULL,
    share_pct REAL NOT NULL,
    avg_rating REAL NOT NULL,
    is_top3 INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (app_key, theme_id),
    FOREIGN KEY (app_key, run_id) REFERENCES runs (app_key, run_id)
);

CREATE TABLE IF NOT EXISTS review_themes (
    app_key TEXT NOT NULL,
    review_id TEXT NOT NULL,
    theme_id TEXT NOT NULL,
    distance REAL,
    PRIMARY KEY (app_key, review_id, theme_id),
    FOREIGN KEY (app_key, review_id) REFERENCES reviews (app_key, review_id),
    FOREIGN KEY (app_key, theme_id) REFERENCES themes (app_key, theme_id)
);

CREATE TABLE IF NOT EXISTS publish_state (
    app_key TEXT NOT NULL REFERENCES apps (app_key),
    week_start TEXT NOT NULL,
    doc_id TEXT,
    doc_url TEXT,
    draft_id TEXT,
    content_hash TEXT,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (app_key, week_start)
);

CREATE TABLE IF NOT EXISTS embedding_cache (
    app_key TEXT NOT NULL REFERENCES apps (app_key),
    review_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    vector_json TEXT NOT NULL,
    PRIMARY KEY (app_key, review_id, model_name)
);

INSERT INTO apps (app_key, display_name, play_package_id, app_store_id, country, lang, category, status, created_at)
SELECT 'groww', 'Groww', 'com.nextbillion.groww', NULL, 'in', 'en', 'Finance', 'active', '2026-11-23T00:00:00+00:00'
WHERE NOT EXISTS (SELECT 1 FROM apps WHERE app_key = 'groww');

UPDATE apps SET app_store_id = '1404871703'
WHERE app_key = 'groww' AND app_store_id IS NULL;
