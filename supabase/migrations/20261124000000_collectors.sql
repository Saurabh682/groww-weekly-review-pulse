CREATE OR REPLACE FUNCTION freeze_app_identity() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.app_key IS DISTINCT FROM OLD.app_key
       OR (OLD.play_package_id IS NOT NULL AND NEW.play_package_id IS DISTINCT FROM OLD.play_package_id)
       OR (OLD.app_store_id IS NOT NULL AND NEW.app_store_id IS DISTINCT FROM OLD.app_store_id) THEN
        RAISE EXCEPTION 'app_identity_frozen' USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END;
$$;

UPDATE apps SET app_store_id = '1404871703'
WHERE app_key = 'groww' AND app_store_id IS NULL;

ALTER TABLE collection_runs ADD COLUMN IF NOT EXISTS feed_gaps INTEGER NOT NULL DEFAULT 0;
