-- =============================================================================
-- MahaRainRisk: Enterprise PostgreSQL Security Hardening & Indexing
-- Protects database against SQL injection, unauthorized wipes, DoS, and slow scans.
-- =============================================================================

\c maharainrisk_db;

-- -----------------------------------------------------------------------------
-- 1. High-Performance Indexing (Mitigates Query DoS & Slow Scans)
-- -----------------------------------------------------------------------------
-- Composite time-series descending index for sub-millisecond range queries
CREATE INDEX IF NOT EXISTS idx_daily_weather_taluka_date 
ON daily_weather (taluka_lgd_code, record_date DESC);

-- District lookup index
CREATE INDEX IF NOT EXISTS idx_talukas_district 
ON talukas (district_name);

-- DB-04: Drop non-functional GIN indexes on 194-row table to reduce write overhead
DROP INDEX IF EXISTS idx_risk_shap_gin;
DROP INDEX IF EXISTS idx_risk_advisory_gin;

-- -----------------------------------------------------------------------------
-- 2. Row Level Security (RLS) - Threat 3 Defense
-- -----------------------------------------------------------------------------
ALTER TABLE talukas ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_weather ENABLE ROW LEVEL SECURITY;
ALTER TABLE taluka_risk_latest ENABLE ROW LEVEL SECURITY;

-- Drop existing public policies if present to prevent duplicate errors
DROP POLICY IF EXISTS public_read_talukas ON talukas;
DROP POLICY IF EXISTS public_read_daily_weather ON daily_weather;
DROP POLICY IF EXISTS public_read_taluka_risk ON taluka_risk_latest;

-- Allow SELECT access to all roles
CREATE POLICY public_read_talukas ON talukas FOR SELECT USING (true);
CREATE POLICY public_read_daily_weather ON daily_weather FOR SELECT USING (true);
CREATE POLICY public_read_taluka_risk ON taluka_risk_latest FOR SELECT USING (true);

-- -----------------------------------------------------------------------------
-- 3. Principle of Least Privilege: Application Role Setup
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'maharain_app') THEN
        -- SEC-05: Provision role without hardcoded password in VCS; set via ALTER ROLE in deployment
        CREATE ROLE maharain_app WITH LOGIN;
    END IF;
END
$$;

GRANT CONNECT ON DATABASE maharainrisk_db TO maharain_app;
GRANT USAGE ON SCHEMA public TO maharain_app;
GRANT SELECT ON talukas, daily_weather, taluka_risk_latest TO maharain_app;

-- Explicitly revoke destructive permissions from application role
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON talukas, daily_weather, taluka_risk_latest FROM maharain_app;
REVOKE CREATE ON SCHEMA public FROM maharain_app;

