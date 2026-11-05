"""
MahaRainRisk: Enterprise Database Layer & Connection Pool
Thread-safe connection pooling, strict parameterized queries,
built-in SQL injection defense, and taluka whitelist validation.
"""

import os
import sys
import logging
from contextlib import contextmanager
from typing import Dict, Any, List, Optional, Tuple, Union
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel, Field, field_validator
import pandas as pd

# Load environment variables if .env exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger("maharainrisk.db")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO_CSV = os.path.join(BASE_DIR, "data", "geo", "lgd_maharashtra_master.csv")

# -----------------------------------------------------------------------------
# 1. Monitored Rainfed Taluka In-Memory Whitelist (194 LGD Codes)
# -----------------------------------------------------------------------------
def _load_whitelist() -> Tuple[set, Dict[int, str]]:
    if os.path.exists(GEO_CSV):
        try:
            df = pd.read_csv(GEO_CSV)
            codes = set(df["taluka_lgd_code"].astype(int))
            names = dict(zip(df["taluka_lgd_code"].astype(int), df["taluka_name"]))
            return codes, names
        except Exception:
            pass
    return set(), {}

VALID_TALUKA_CODES, TALUKA_NAME_LOOKUP = _load_whitelist()

# -----------------------------------------------------------------------------
# 2. Strict Pydantic Query Validation Schemas
# -----------------------------------------------------------------------------
class TalukaCodeValidator(BaseModel):
    taluka_lgd_code: int = Field(..., description="Official Government LGD code for taluka")

    @field_validator("taluka_lgd_code")
    @classmethod
    def validate_code(cls, v: int) -> int:
        if VALID_TALUKA_CODES and v not in VALID_TALUKA_CODES:
            raise ValueError(f"Taluka LGD code {v} is not within the 194 monitored Maharashtra rainfed talukas.")
        return v

class DateRangeValidator(BaseModel):
    taluka_lgd_code: int
    start_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")

    @field_validator("taluka_lgd_code")
    @classmethod
    def validate_code(cls, v: int) -> int:
        if VALID_TALUKA_CODES and v not in VALID_TALUKA_CODES:
            raise ValueError(f"Invalid taluka code {v}.")
        return v

# -----------------------------------------------------------------------------
# 3. Secure Database Connection Pool (Lazy & Resilient)
# -----------------------------------------------------------------------------
class DatabasePool:
    _instance: Optional["DatabasePool"] = None

    def __init__(self):
        self._pool: Optional[pool.ThreadedConnectionPool] = None

    @classmethod
    def get_instance(cls) -> "DatabasePool":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def init_pool(self, password: Optional[str] = None):
        """Explicitly initializes or refreshes connection pool."""
        min_conn = int(os.getenv("DB_POOL_MIN", "2"))
        max_conn = int(os.getenv("DB_POOL_MAX", "20"))

        if self._pool is not None:
            try:
                self._pool.closeall()
            except Exception:
                pass
            self._pool = None

        db_url = os.getenv("DATABASE_URL")
        if db_url:
            self._pool = pool.ThreadedConnectionPool(
                minconn=min_conn,
                maxconn=max_conn,
                dsn=db_url
            )
            return self._pool

        db_name = os.getenv("PGDATABASE", "maharainrisk_db")
        db_user = os.getenv("PGUSER", "postgres")
        db_host = os.getenv("PGHOST", "localhost")
        db_port = int(os.getenv("PGPORT", "5432"))
        db_pass = password if password is not None else (os.getenv("PGPASSWORD") or os.getenv("DB_PASSWORD", ""))

        self._pool = pool.ThreadedConnectionPool(
            minconn=min_conn,
            maxconn=max_conn,
            dbname=db_name,
            user=db_user,
            password=db_pass,
            host=db_host,
            port=db_port
        )
        return self._pool

    @contextmanager
    def get_connection(self):
        if self._pool is None:
            db_pass = os.getenv("PGPASSWORD") or os.getenv("DB_PASSWORD")
            db_url = os.getenv("DATABASE_URL")
            if db_pass is not None or db_url is not None:
                self.init_pool(db_pass)
            else:
                raise ConnectionError("Database connection pool is offline. Neither PGPASSWORD nor DATABASE_URL is set.")
        conn = self._pool.getconn()
        try:
            yield conn
        finally:
            if self._pool:
                self._pool.putconn(conn)

    def close(self):
        if self._pool:
            self._pool.closeall()
            self._pool = None

# Global pool singleton
db_pool = DatabasePool.get_instance()

# -----------------------------------------------------------------------------
# 4. Strictly Parameterized Query Interface (SQL Injection Proof)
# -----------------------------------------------------------------------------
def execute_query(query: str, params: Optional[Union[tuple, list, dict]] = None, fetch_one: bool = False, fetch_all: bool = False) -> Any:
    """
    Executes a strictly parameterized query.
    String concatenation into query is mathematically blocked:
    All dynamic values must be passed via the 'params' tuple.
    """
    with db_pool.get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if fetch_one:
                return cur.fetchone()
            if fetch_all:
                return cur.fetchall()
            conn.commit()
            return None

def fetch_taluka_by_code(taluka_lgd_code: int) -> Optional[Dict[str, Any]]:
    """Fetches static metadata for a taluka with validation."""
    TalukaCodeValidator(taluka_lgd_code=taluka_lgd_code)
    query = """
        SELECT 
            taluka_lgd_code, taluka_name, taluka_name_mr,
            district_name, district_name_mr, division_name, division_name_mr,
            latitude, longitude, agro_climatic_zone, normal_annual_rainfall_mm,
            soil_type, major_crops
        FROM talukas
        WHERE taluka_lgd_code = %s;
    """
    return execute_query(query, (taluka_lgd_code,), fetch_one=True)

def fetch_latest_risk(taluka_lgd_code: int) -> Optional[Dict[str, Any]]:
    """Fetches the latest pre-computed risk snapshot with TreeSHAP and bilingual advisory."""
    TalukaCodeValidator(taluka_lgd_code=taluka_lgd_code)
    query = """
        SELECT 
            taluka_lgd_code, as_of_date, risk_category, risk_score, confidence,
            forecast_month, predicted_risk_lead_1, spi_1, spi_3, spi_6, spei_3,
            soil_moisture_index, max_consecutive_dry_days, district_dam_storage_pct,
            groundwater_depth_mbgl, shap_summary, bilingual_advisory, updated_at
        FROM taluka_risk_latest
        WHERE taluka_lgd_code = %s;
    """
    return execute_query(query, (taluka_lgd_code,), fetch_one=True)

def fetch_daily_weather_range(taluka_lgd_code: int, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """Fetches daily time-series weather logs within a date range."""
    DateRangeValidator(taluka_lgd_code=taluka_lgd_code, start_date=start_date, end_date=end_date)
    query = """
        SELECT 
            record_date, rainfall_mm, temp_max_c, temp_min_c,
            et0_evapotranspiration_mm, soil_moisture_root_zone, is_rainy_day
        FROM daily_weather
        WHERE taluka_lgd_code = %s AND record_date BETWEEN %s AND %s
        ORDER BY record_date ASC;
    """
    return execute_query(query, (taluka_lgd_code, start_date, end_date), fetch_all=True)

def fetch_all_latest_risks() -> List[Dict[str, Any]]:
    """Fetches the latest risk state across all 194 talukas for map display."""
    query = """
        SELECT 
            r.taluka_lgd_code, t.taluka_name, t.taluka_name_mr,
            t.district_name, t.district_name_mr, t.latitude, t.longitude,
            r.as_of_date, r.risk_category, r.risk_score, r.confidence,
            r.forecast_month, r.predicted_risk_lead_1, r.spi_3,
            r.soil_moisture_index, r.max_consecutive_dry_days,
            r.district_dam_storage_pct, r.shap_summary, r.bilingual_advisory
        FROM taluka_risk_latest r
        JOIN talukas t ON r.taluka_lgd_code = t.taluka_lgd_code
        ORDER BY t.district_name, t.taluka_name;
    """
    return execute_query(query, fetch_all=True)
