REVOKE EXECUTE ON FUNCTION enforce_active_app_cap(), freeze_app_identity() FROM PUBLIC;

DO $$
DECLARE
    client_role TEXT;
BEGIN
    FOR client_role IN SELECT rolname FROM pg_roles WHERE rolname IN ('anon', 'authenticated') LOOP
        EXECUTE format('REVOKE ALL ON apps, reviews, collection_runs, runs, themes, review_themes, publish_state, '
                       'embedding_cache FROM %I', client_role);
        EXECUTE format('REVOKE ALL ON SEQUENCE collection_runs_collection_id_seq FROM %I', client_role);
        EXECUTE format('REVOKE ALL ON FUNCTION enforce_active_app_cap(), freeze_app_identity() FROM %I', client_role);
        EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM %I', client_role);
        EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM %I', client_role);
        EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON FUNCTIONS FROM %I', client_role);
    END LOOP;
END;
$$;
