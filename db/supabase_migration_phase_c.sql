-- =============================================================================
-- MahaRainRisk: Phase C Supabase Cloud Database Migration
-- Tables: taluka_risk_history, Performance Indexes, Row Level Security (RLS)
-- Execution Target: Supabase Dashboard -> SQL Editor
-- =============================================================================

-- 1. Historical Drought Risk Audit Ledger (DB-02)
CREATE TABLE IF NOT EXISTS public.taluka_risk_history (
    taluka_lgd_code INT NOT NULL REFERENCES public.talukas(taluka_lgd_code),
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

-- 2. Performance Indexes (DB-02, DB-03)
CREATE INDEX IF NOT EXISTS idx_risk_history_date 
ON public.taluka_risk_history(as_of_date DESC);

CREATE INDEX IF NOT EXISTS idx_daily_weather_taluka_date 
ON public.daily_weather (taluka_lgd_code, record_date DESC);

CREATE INDEX IF NOT EXISTS idx_talukas_district 
ON public.talukas (district_name);

-- 3. Row-Level Security (RLS)
ALTER TABLE public.taluka_risk_history ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS public_read_taluka_risk_history ON public.taluka_risk_history;
CREATE POLICY public_read_taluka_risk_history ON public.taluka_risk_history FOR SELECT USING (true);
