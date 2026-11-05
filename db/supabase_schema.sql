-- =============================================================================
-- MahaRainRisk: Supabase Cloud Database Production Schema & Security
-- Platform: Operational Taluka-Level Agritech Drought Early Warning System
-- Geographic Scope: 194 Monitored Rainfed Talukas across 36 Districts
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Master Geographic Metadata Table (194 Talukas)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS talukas (
    taluka_lgd_code INT PRIMARY KEY,
    taluka_name VARCHAR(100) NOT NULL,
    taluka_name_mr VARCHAR(100) NOT NULL,
    district_lgd_code INT NOT NULL,
    district_name VARCHAR(100) NOT NULL,
    district_name_mr VARCHAR(100) NOT NULL,
    division_name VARCHAR(50) NOT NULL,
    division_name_mr VARCHAR(50) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    agro_climatic_zone VARCHAR(100) NOT NULL,
    agro_climatic_zone_mr VARCHAR(100) NOT NULL,
    university_affiliation VARCHAR(150) NOT NULL,
    soil_type VARCHAR(100) NOT NULL,
    normal_annual_rainfall_mm DOUBLE PRECISION NOT NULL,
    major_crops TEXT,
    major_crops_mr TEXT
);

-- -----------------------------------------------------------------------------
-- 2. Daily Meteorological Time-Series Telemetry Table (484,224+ Observations)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS daily_weather (
    taluka_lgd_code INT NOT NULL REFERENCES talukas(taluka_lgd_code),
    record_date DATE NOT NULL,
    rainfall_mm DOUBLE PRECISION NOT NULL,
    temp_max_c DOUBLE PRECISION NOT NULL,
    temp_min_c DOUBLE PRECISION NOT NULL,
    et0_evapotranspiration_mm DOUBLE PRECISION NOT NULL,
    soil_moisture_root_zone DOUBLE PRECISION NOT NULL,
    is_rainy_day SMALLINT NOT NULL CHECK (is_rainy_day IN (0, 1)),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (taluka_lgd_code, record_date)
);

-- -----------------------------------------------------------------------------
-- 3. Pre-computed Drought Risk Snapshots & TreeSHAP Drivers Table (194 Talukas)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS taluka_risk_latest (
    taluka_lgd_code INT PRIMARY KEY REFERENCES talukas(taluka_lgd_code),
    as_of_date DATE NOT NULL,
    risk_category VARCHAR(30) NOT NULL,
    risk_score DOUBLE PRECISION NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    forecast_month VARCHAR(20) NOT NULL,
    predicted_risk_lead_1 VARCHAR(30) NOT NULL,
    spi_1 DOUBLE PRECISION,
    spi_3 DOUBLE PRECISION,
    spi_6 DOUBLE PRECISION,
    spei_3 DOUBLE PRECISION,
    soil_moisture_index DOUBLE PRECISION,
    max_consecutive_dry_days INT,
    district_dam_storage_pct DOUBLE PRECISION,
    groundwater_depth_mbgl DOUBLE PRECISION,
    shap_summary JSONB NOT NULL,
    bilingual_advisory JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- 3b. DB-02: Historical Drought Risk Audit Ledger (Preserves Time-Series Telemetry & ML History)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS taluka_risk_history (
    taluka_lgd_code INT NOT NULL REFERENCES talukas(taluka_lgd_code),
    as_of_date DATE NOT NULL,
    risk_category VARCHAR(30) NOT NULL,
    risk_score DOUBLE PRECISION NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    forecast_month VARCHAR(20) NOT NULL,
    predicted_risk_lead_1 VARCHAR(30) NOT NULL,
    spi_1 DOUBLE PRECISION,
    spi_3 DOUBLE PRECISION,
    spi_6 DOUBLE PRECISION,
    spei_3 DOUBLE PRECISION,
    soil_moisture_index DOUBLE PRECISION,
    max_consecutive_dry_days INT,
    district_dam_storage_pct DOUBLE PRECISION,
    groundwater_depth_mbgl DOUBLE PRECISION,
    shap_summary JSONB NOT NULL,
    bilingual_advisory JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (taluka_lgd_code, as_of_date)
);

CREATE INDEX IF NOT EXISTS idx_risk_history_date ON taluka_risk_history(as_of_date DESC);

-- -----------------------------------------------------------------------------
-- 4. High-Performance Indexing Strategy
-- -----------------------------------------------------------------------------
-- Time-series descending index for sub-millisecond range queries
CREATE INDEX IF NOT EXISTS idx_daily_weather_lookup 
ON daily_weather(taluka_lgd_code, record_date DESC);

-- District administrative rollup index
CREATE INDEX IF NOT EXISTS idx_talukas_district 
ON talukas(district_name);

-- GIN (Generalized Inverted Index) for fast JSONB querying on XAI drivers
CREATE INDEX IF NOT EXISTS idx_taluka_risk_shap_gin 
ON taluka_risk_latest USING GIN(shap_summary);

-- GIN index on bilingual advisories
CREATE INDEX IF NOT EXISTS idx_taluka_risk_advisory_gin 
ON taluka_risk_latest USING GIN(bilingual_advisory);

-- -----------------------------------------------------------------------------
-- 5. Row Level Security (RLS) & Role Privileges
-- -----------------------------------------------------------------------------
ALTER TABLE talukas ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_weather ENABLE ROW LEVEL SECURITY;
ALTER TABLE taluka_risk_latest ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS public_read_talukas ON talukas;
DROP POLICY IF EXISTS public_read_daily_weather ON daily_weather;
DROP POLICY IF EXISTS public_read_taluka_risk ON taluka_risk_latest;

-- Allow public read access (via anon key or authenticated clients)
CREATE POLICY public_read_talukas ON talukas FOR SELECT USING (true);
CREATE POLICY public_read_daily_weather ON daily_weather FOR SELECT USING (true);
CREATE POLICY public_read_taluka_risk ON taluka_risk_latest FOR SELECT USING (true);

-- Grant appropriate permissions to Supabase API roles
GRANT SELECT ON talukas, daily_weather, taluka_risk_latest TO anon, authenticated;
GRANT ALL ON talukas, daily_weather, taluka_risk_latest TO service_role;

