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

CREATE OR REPLACE FUNCTION enforce_active_app_cap() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    PERFORM pg_advisory_xact_lock(hashtext('apps_active_cap'));
    IF NEW.status <> 'archived'
       AND (TG_OP = 'INSERT' OR OLD.status = 'archived')
       AND (SELECT COUNT(*) FROM apps WHERE status <> 'archived') >= 5 THEN
        RAISE EXCEPTION 'active_app_cap_reached' USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS apps_cap ON apps;
CREATE TRIGGER apps_cap BEFORE INSERT OR UPDATE OF status ON apps
    FOR EACH ROW EXECUTE FUNCTION enforce_active_app_cap();

CREATE OR REPLACE FUNCTION freeze_app_identity() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.app_key IS DISTINCT FROM OLD.app_key
       OR NEW.play_package_id IS DISTINCT FROM OLD.play_package_id
       OR NEW.app_store_id IS DISTINCT FROM OLD.app_store_id THEN
        RAISE EXCEPTION 'app_identity_frozen' USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS apps_identity_frozen ON apps;
CREATE TRIGGER apps_identity_frozen BEFORE UPDATE ON apps
    FOR EACH ROW EXECUTE FUNCTION freeze_app_identity();

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
    collection_id BIGSERIAL PRIMARY KEY,
    app_key TEXT NOT NULL REFERENCES apps (app_key),
    platform TEXT NOT NULL CHECK (platform IN ('play_store', 'app_store')),
    mode TEXT NOT NULL CHECK (mode IN ('backfill', 'daily', 'reconcile', 'csv_import')),
    window_start TEXT NOT NULL,
    window_end TEXT NOT NULL,
    covered_start TEXT,
    fetched INTEGER NOT NULL DEFAULT 0,
    inserted INTEGER NOT NULL DEFAULT 0,
    source_limit_hit INTEGER NOT NULL DEFAULT 0,
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
    avg_rating DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    coverage_weeks DOUBLE PRECISION NOT NULL DEFAULT 0.0,
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
    share_pct DOUBLE PRECISION NOT NULL,
    avg_rating DOUBLE PRECISION NOT NULL,
    is_top3 INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (app_key, theme_id),
    FOREIGN KEY (app_key, run_id) REFERENCES runs (app_key, run_id)
);

CREATE TABLE IF NOT EXISTS review_themes (
    app_key TEXT NOT NULL,
    review_id TEXT NOT NULL,
    theme_id TEXT NOT NULL,
    distance DOUBLE PRECISION,
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

ALTER TABLE apps ENABLE ROW LEVEL SECURITY;
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE collection_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE themes ENABLE ROW LEVEL SECURITY;
ALTER TABLE review_themes ENABLE ROW LEVEL SECURITY;
ALTER TABLE publish_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE embedding_cache ENABLE ROW LEVEL SECURITY;

INSERT INTO apps (app_key, display_name, play_package_id, app_store_id, country, lang, category, status, created_at)
SELECT 'groww', 'Groww', 'com.nextbillion.groww', NULL, 'in', 'en', 'Finance', 'active', '2026-11-23T00:00:00+00:00'
WHERE NOT EXISTS (SELECT 1 FROM apps WHERE app_key = 'groww');
