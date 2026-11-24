DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'themes' AND column_name = 'neg_share'
    ) THEN
        ALTER TABLE themes ADD COLUMN neg_share DOUBLE PRECISION NOT NULL DEFAULT 0.0;
        ALTER TABLE themes ADD COLUMN priority_score DOUBLE PRECISION NOT NULL DEFAULT 0.0;
        UPDATE themes t SET neg_share = s.neg_share
        FROM (
            SELECT rt.app_key, rt.theme_id,
                   ROUND(AVG(CASE WHEN r.rating <= 2 THEN 1.0 ELSE 0.0 END), 4) AS neg_share
            FROM review_themes rt
            JOIN reviews r ON r.app_key = rt.app_key AND r.review_id = rt.review_id
            GROUP BY rt.app_key, rt.theme_id
        ) s
        WHERE s.app_key = t.app_key AND s.theme_id = t.theme_id;
        UPDATE themes SET priority_score = ROUND((share_pct * (0.6 + 0.4 * neg_share))::numeric, 5);
    END IF;
END;
$$;
