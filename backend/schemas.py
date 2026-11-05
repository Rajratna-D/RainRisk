"""
MahaRainRisk: Pydantic V2 Data Models & Strict Schema Contracts
Defines validated input/output schemas for all REST API endpoints.
Provides automatic type validation, serialization, and interactive OpenAPI documentation.
"""

import json
import hashlib
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


# -----------------------------------------------------------------------------
# BASE / UTILITY SCHEMAS
# -----------------------------------------------------------------------------

class ErrorEnvelope(BaseModel):
    error: str = Field(..., description="Short error type or status")
    detail: str = Field(..., description="Human-readable explanation of the error")
    timestamp: float = Field(..., description="Epoch timestamp when the error occurred")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Current system health status")
    platform: str = Field(..., description="Platform branding and name")
    talukas_covered: int = Field(..., description="Total active talukas in the platform")
    districts_covered: int = Field(..., description="Total districts covered")
    models: Dict[str, str] = Field(..., description="Active ML models and reported test accuracies")


# -----------------------------------------------------------------------------
# TALUKA SEARCH & AUTOCOMPLETE SCHEMAS
# -----------------------------------------------------------------------------

class TalukaSummaryItem(BaseModel):
    taluka_lgd_code: int = Field(..., description="Local Government Directory (LGD) code")
    taluka_name: str = Field(..., description="Official English name")
    taluka_name_mr: str = Field(..., description="Official Marathi Devanagari name")
    district_name: str = Field(..., description="District English name")
    district_name_mr: str = Field(..., description="District Marathi name")
    division_name: str = Field(..., description="Administrative division name")
    latitude: float = Field(..., description="Geographic latitude coordinate")
    longitude: float = Field(..., description="Geographic longitude coordinate")
    university: str = Field(..., description="Affiliated state agricultural university")
    risk_category: Optional[int] = Field(0, description="Current drought risk category code (0-4)")
    risk_label_en: Optional[str] = Field("Safe", description="English risk label")
    risk_label_mr: Optional[str] = Field("सुरक्षित", description="Marathi risk label")
    risk_color: Optional[str] = Field("#10B981", description="HEX risk color for map pin")


# -----------------------------------------------------------------------------
# ML DIAGNOSIS & 30-DAY FORECAST SCHEMAS
# -----------------------------------------------------------------------------

class RiskTierModel(BaseModel):
    category_code: int = Field(..., description="Risk tier code: 0=Safe, 1=Watch, 2=Alert, 3=Severe, 4=Extreme")
    label_en: str = Field(..., description="English severity label")
    label_mr: str = Field(..., description="Marathi severity label")
    confidence_pct: float = Field(..., description="Model certainty percentage (0-100%)")


# -----------------------------------------------------------------------------
# 4 SIMPLE FARMER TELEMETRY CARDS
# -----------------------------------------------------------------------------

class FarmerCardRainfall(BaseModel):
    title_en: str
    title_mr: str
    value_mm: float
    status_en: str
    status_mr: str
    color: str


class FarmerCardSoil(BaseModel):
    title_en: str
    title_mr: str
    value_pct: float
    status_en: str
    status_mr: str
    color: str


class FarmerCardDam(BaseModel):
    title_en: str
    title_mr: str
    value_pct: float
    status_en: str
    status_mr: str
    color: str
    dam_name: Optional[str] = None
    dam_name_mr: Optional[str] = None


class FarmerCardDryGap(BaseModel):
    title_en: str
    title_mr: str
    value_days: int
    status_en: str
    status_mr: str
    color: str


class FarmerCards(BaseModel):
    rainfall_deficit: FarmerCardRainfall
    soil_moisture: FarmerCardSoil
    dam_storage: FarmerCardDam
    dry_gap: FarmerCardDryGap


# -----------------------------------------------------------------------------
# MONSOON HISTORICAL RAINFALL CHART
# -----------------------------------------------------------------------------

class MonsoonChartPoint(BaseModel):
    year: int = Field(..., description="Monsoon year (e.g. 2018-2023)")
    monsoon_rainfall_mm: float = Field(..., description="Total rainfall during JJAS season in mm")


# -----------------------------------------------------------------------------
# BILINGUAL UNIVERSITY AGRONOMIC ADVISORY
# -----------------------------------------------------------------------------

class BilingualText(BaseModel):
    en: str
    mr: str


class PrescriptiveActions(BaseModel):
    moisture_conservation: BilingualText
    foliar_and_nutrients: BilingualText
    irrigation_strategy: BilingualText
    contingency_management: BilingualText


class UniversityAnchor(BaseModel):
    university_key: str
    university_name_en: str
    university_name_mr: str
    regional_focus: str


class GeographyContext(BaseModel):
    taluka_name: str
    district_name: str
    target_crop: str


class AdvisoryRiskLevel(BaseModel):
    category_code: int
    status_en: str
    status_mr: str
    badge_color: str


class AdvisoryTelemetryContext(BaseModel):
    soil_moisture_index_pct: float
    dam_storage_pct: float


class AdvisoryPayload(BaseModel):
    geography: GeographyContext
    university_anchor: UniversityAnchor
    risk_level: AdvisoryRiskLevel
    telemetry_context: AdvisoryTelemetryContext
    prescriptive_actions: PrescriptiveActions
    source_citation: str


# -----------------------------------------------------------------------------
# COMPOSITE TALUKA DETAIL RESPONSE
# -----------------------------------------------------------------------------

class TalukaMeta(BaseModel):
    taluka: str
    district: str
    period: str
    taluka_mr: str
    district_mr: str


class TalukaDetailResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    meta: TalukaMeta
    live_diagnosis: RiskTierModel
    forecast_30_day: RiskTierModel = Field(..., alias="30_day_forecast")
    farmer_cards: FarmerCards
    chart_history: List[MonsoonChartPoint]
    advisory: AdvisoryPayload


# -----------------------------------------------------------------------------
# RESERVOIR SCHEMAS
# -----------------------------------------------------------------------------

class ReservoirItem(BaseModel):
    dam_name: str
    dam_name_mr: str
    district: str
    river: str
    storage_pct: float
    live_capacity_tmc: float
    is_critical: bool


# -----------------------------------------------------------------------------
# MACRO ANALYTICS & DISTRICT OVERVIEW SCHEMAS
# -----------------------------------------------------------------------------

class RiskTierDistribution(BaseModel):
    safe_count: int = Field(..., description="Total talukas currently in Safe status")
    watch_count: int = Field(..., description="Total talukas under Watch")
    alert_count: int = Field(..., description="Total talukas under Alert")
    severe_count: int = Field(..., description="Total talukas under Severe drought")
    extreme_count: int = Field(..., description="Total talukas under Extreme drought")


class DroughtHotspotItem(BaseModel):
    taluka_name: str
    taluka_name_mr: str
    district_name: str
    risk_tier: str
    category_code: int
    spi_3: float
    soil_moisture_index: float
    dry_spell_days: int


class OverviewResponse(BaseModel):
    total_talukas: int = Field(194, description="Total talukas analyzed")
    total_districts: int = Field(36, description="Total districts")
    state_avg_rainfall_deficit_pct: float = Field(..., description="State-wide 3-month rainfall deficit average")
    state_avg_soil_moisture_pct: float = Field(..., description="State-wide average root-zone soil moisture")
    state_avg_dam_storage_pct: float = Field(..., description="State-wide major dam storage average")
    risk_distribution: RiskTierDistribution
    top_hotspots: List[DroughtHotspotItem] = Field(..., description="Top 5 highest drought risk talukas")


class DistrictRollupItem(BaseModel):
    district_name: str
    district_name_mr: str
    division_name: str
    taluka_count: int
    avg_soil_moisture: float
    avg_dam_storage: float
    dominant_risk_category: int
    dominant_risk_label: str
    primary_university: str


class TalukaComparisonResponse(BaseModel):
    taluka_1: TalukaDetailResponse
    taluka_2: TalukaDetailResponse
    analysis_delta: Dict[str, Any] = Field(..., description="Computed differentials between the two talukas")


# -----------------------------------------------------------------------------
# PHASE 4 MULTI-TIER CACHING SCHEMAS
# -----------------------------------------------------------------------------

class TalukaRiskResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    taluka_lgd_code: int
    taluka_name: str
    taluka_name_mr: str
    district_name: str
    as_of_date: str
    risk_category: Union[int, str]
    risk_score: float
    confidence: float
    forecast_month: str
    predicted_risk_lead_1: Union[int, str]
    spi_1: Optional[float] = None
    spi_3: Optional[float] = None
    spi_6: Optional[float] = None
    spei_3: Optional[float] = None
    soil_moisture_index: Optional[float] = None
    max_consecutive_dry_days: Optional[int] = None
    district_dam_storage_pct: Optional[float] = None
    groundwater_depth_mbgl: Optional[float] = None
    shap_summary: Dict[str, Any]
    bilingual_advisory: Dict[str, Any]
    source: Optional[str] = "tier2_cache"


class CacheStatsResponse(BaseModel):
    size: int
    maxsize: int
    ttl_seconds: int
    hits: int
    misses: int
    hit_ratio_pct: float
    tier3_db_hits: int
    in_memory_fallbacks: int
    uptime_seconds: float


# -----------------------------------------------------------------------------
# PHASE 6 EXPLAINABLE AI (XAI) SCHEMAS
# -----------------------------------------------------------------------------

class FeatureAttributionItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    feature_key: str
    name_en: str
    name_mr: str
    icon: str
    raw_value: Optional[float] = None
    unit: str
    shap_value: float
    impact_pct: float
    is_escalator: bool


class TalukaExplainResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    taluka_lgd_code: int
    taluka_name: str
    taluka_name_mr: str
    district_name: str
    as_of_date: str
    predicted_tier: Dict[str, Any]
    confidence_pct: float
    top_risk_escalators: List[FeatureAttributionItem]
    top_mitigating_buffers: List[FeatureAttributionItem]
    all_drivers: List[FeatureAttributionItem]
    farmer_summary: Dict[str, str]
    computation_time_ms: float
    source: Optional[str] = "xai_engine"


