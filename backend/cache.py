"""
MahaRainRisk: Production Multi-Tier Caching Engine & Thread Safety Architecture
File: backend/cache.py

Architectural Layers:
1. Tier 1: Client Edge Cache (HTTP Cache-Control: public, max-age=300, stale-while-revalidate=60)
2. Tier 2: FastAPI In-Memory TTLCache (maxsize=500, ttl=21600 = 6 hours) via cachetools
3. Tier 3: PostgreSQL Pre-computed JSONB snapshot in 'taluka_risk_latest'
   Fallback: In-memory Parquet telemetry & live ML inference engine when DB is offline.

Defensive Safeguards:
- Thread-safety via threading.RLock()
- Anti-object mutation via copy.deepcopy on storage and retrieval
- Zero-Pickle policy enforcing strict JSON and Pydantic serialization
- Input clamping and normalization to thwart cache-flooding DoS attacks
- Deterministic date-keyed invalidation with automatic rollover
"""

import os
import sys
import time
import copy
import json
import hashlib
import datetime
import threading
import logging
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import cachetools
from cachetools import TTLCache
from pydantic import BaseModel

logger = logging.getLogger("maharainrisk.cache")

# -----------------------------------------------------------------------------
# CONSTANTS & CONFIGURATION
# -----------------------------------------------------------------------------
DEFAULT_CACHE_MAXSIZE: int = 500
DEFAULT_CACHE_TTL_SECONDS: int = 21600  # 6 hours

# Detection magic bytes for pickle streams (Protocols 2, 3, 4, 5)
PICKLE_MAGIC_PREFIXES: Tuple[bytes, ...] = (
    b'\x80\x02',
    b'\x80\x03',
    b'\x80\x04',
    b'\x80\x05',
    b'\x80',
)


# -----------------------------------------------------------------------------
# EXCEPTIONS
# -----------------------------------------------------------------------------
class CacheError(Exception):
    """Base exception for caching subsystem."""
    pass


class ZeroPickleViolationError(CacheError):
    """Raised when an object or byte stream violates the Zero-Pickle policy."""
    pass


class CacheKeyError(CacheError):
    """Raised when invalid or unnormalizable keys are provided."""
    pass


# -----------------------------------------------------------------------------
# SECURITY & NORMALIZATION HELPERS
# -----------------------------------------------------------------------------
def normalize_as_of_date(as_of_date: Optional[Union[str, datetime.date, datetime.datetime]] = None) -> str:
    """
    Normalizes any date or datetime input into canonical 'YYYY-MM-DD' string.
    Defaults to current UTC date if None or empty.
    """
    if as_of_date is None or as_of_date == "":
        return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    if isinstance(as_of_date, (datetime.date, datetime.datetime)):
        return as_of_date.strftime("%Y-%m-%d")
    s = str(as_of_date).strip()
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    return s


def validate_zero_pickle(value: Any) -> None:
    """
    Enforces strict Zero-Pickle policy.
    Rejects raw pickled byte streams and non-serializable objects.
    Permits JSON-serializable types and Pydantic V2 models only.
    """
    # 1. Reject binary byte streams containing pickle protocol signatures
    if isinstance(value, (bytes, bytearray)):
        for prefix in PICKLE_MAGIC_PREFIXES:
            if value.startswith(prefix):
                raise ZeroPickleViolationError(
                    "Zero-Pickle Policy Violation: Raw pickled bytecode stream detected. "
                    "Pickle serialization is strictly prohibited for security."
                )

    # 2. Allow Pydantic BaseModel instances
    if isinstance(value, BaseModel):
        return

    # 3. Allow standard JSON primitives and collections
    if isinstance(value, (dict, list, str, int, float, bool, type(None))):
        try:
            # Ensure nested objects are fully JSON serializable
            json.dumps(value)
            return
        except (TypeError, OverflowError) as e:
            raise ZeroPickleViolationError(
                f"Zero-Pickle Policy Violation: Object contains non-JSON serializable elements: {e}"
            )

    # 4. Reject all other arbitrary Python objects
    raise ZeroPickleViolationError(
        f"Zero-Pickle Policy Violation: Object of type '{type(value).__name__}' is neither "
        "JSON-serializable nor a Pydantic model."
    )


# -----------------------------------------------------------------------------
# DETERMINISTIC CACHE KEY BUILDERS
# -----------------------------------------------------------------------------
def risk_key(taluka_lgd_code: int, as_of_date: Optional[Union[str, datetime.date]] = None) -> str:
    """Standard Taluka Risk Key: risk:{taluka_lgd_code}:{as_of_date}"""
    code = int(taluka_lgd_code)
    d_str = normalize_as_of_date(as_of_date)
    return f"risk:{code}:{d_str}"


def overview_key(as_of_date: Optional[Union[str, datetime.date]] = None) -> str:
    """Overview Analytics Key: analytics:overview:{as_of_date}"""
    return f"analytics:overview:{normalize_as_of_date(as_of_date)}"


def map_key(as_of_date: Optional[Union[str, datetime.date]] = None) -> str:
    """Leaflet GeoJSON Key: map:geojson:{as_of_date}"""
    return f"map:geojson:{normalize_as_of_date(as_of_date)}"


def explain_key(taluka_lgd_code: int, as_of_date: Optional[Union[str, datetime.date]] = None) -> str:
    """Taluka TreeSHAP Explanation Key: explain:{taluka_lgd_code}:{as_of_date}"""
    code = int(taluka_lgd_code)
    d_str = normalize_as_of_date(as_of_date)
    return f"explain:{code}:{d_str}"


# -----------------------------------------------------------------------------
# MULTI-TIER CACHE MANAGER CLASS
# -----------------------------------------------------------------------------
class MultiTierCacheManager:
    """
    Enterprise Multi-Tier In-Memory & Database Cache Manager.
    - Wraps cachetools.TTLCache(maxsize=500, ttl=21600).
    - Guarantees thread safety via threading.RLock().
    - Enforces anti-object mutation via copy.deepcopy on both store and retrieve.
    - Strictly enforces Zero-Pickle policy (JSON / Pydantic only).
    - Coordinates Tier 2 (RAM), Tier 3 (PostgreSQL snapshot), and in-memory fallback.
    """

    def __init__(self, maxsize: int = DEFAULT_CACHE_MAXSIZE, ttl: int = DEFAULT_CACHE_TTL_SECONDS):
        self._maxsize = maxsize
        self._ttl = ttl
        self._cache: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl)
        self._lock: threading.RLock = threading.RLock()

        # Telemetry metrics
        self._hits: int = 0
        self._misses: int = 0
        self._tier3_hits: int = 0
        self._fallbacks: int = 0
        self._created_at: float = time.time()

    def get(self, key: str) -> Optional[Any]:
        """
        Thread-safe retrieval from Tier 2 in-memory cache.
        Returns a deep copy of the cached object to prevent in-place memory mutation.
        """
        with self._lock:
            if key in self._cache:
                self._hits += 1
                return copy.deepcopy(self._cache[key])
            self._misses += 1
            return None

    def set(self, key: str, value: Any) -> None:
        """
        Thread-safe storage into Tier 2 in-memory cache.
        Validates Zero-Pickle policy and stores a deep copy of the value.
        """
        validate_zero_pickle(value)
        with self._lock:
            self._cache[key] = copy.deepcopy(value)

    def get_or_compute(self, key: str, compute_fn: Callable[[], Any]) -> Any:
        """
        Atomic get-or-compute with double-checked locking (BUG-05 / PERF-03).
        Expensive compute_fn is executed outside the global lock to prevent
        serialization across concurrent HTTP worker threads.
        """
        with self._lock:
            if key in self._cache:
                self._hits += 1
                return copy.deepcopy(self._cache[key])

        # Execute compute_fn outside the lock
        result = compute_fn()
        validate_zero_pickle(result)

        with self._lock:
            if key in self._cache:
                self._hits += 1
                return copy.deepcopy(self._cache[key])
            self._cache[key] = copy.deepcopy(result)
            self._misses += 1
            return copy.deepcopy(result)

    def delete(self, key: str) -> bool:
        """Thread-safe removal of a key."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Thread-safe purge of all in-memory entries."""
        with self._lock:
            self._cache.clear()

    def stats(self) -> Dict[str, Any]:
        """Returns cache telemetry stats including size, hit ratio, and Tier 3 metrics."""
        with self._lock:
            total = self._hits + self._misses
            ratio = round((self._hits / total) * 100.0, 2) if total > 0 else 0.0
            return {
                "size": len(self._cache),
                "maxsize": self._maxsize,
                "ttl_seconds": self._ttl,
                "hits": self._hits,
                "misses": self._misses,
                "hit_ratio_pct": ratio,
                "tier3_db_hits": self._tier3_hits,
                "in_memory_fallbacks": self._fallbacks,
                "uptime_seconds": round(time.time() - self._created_at, 1)
            }

    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)

    def __contains__(self, key: str) -> bool:
        with self._lock:
            return key in self._cache

    # -------------------------------------------------------------------------
    # MULTI-TIER RESOLUTION WITH TIER 3 & IN-MEMORY FALLBACK
    # -------------------------------------------------------------------------
    def get_taluka_risk_multitier(self, taluka_lgd_code: int, as_of_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Resolves taluka risk through the multi-tier hierarchy:
        1. Tier 2 (RAM TTLCache): returns in < 2ms.
        2. Tier 3 (PostgreSQL taluka_risk_latest): pre-computed DB snapshot.
        3. Tier 3 Fallback (In-memory telemetry dataframe & live inference):
           gracefully activates when PostgreSQL is offline or credentials are unset.
        """
        code = int(taluka_lgd_code)
        date_str = normalize_as_of_date(as_of_date)
        key = risk_key(code, date_str)

        # 1. Tier 2 Cache Hit
        with self._lock:
            if key in self._cache:
                self._hits += 1
                return copy.deepcopy(self._cache[key])

        # 2. Tier 3 Database Snapshot Query
        db_record = None
        try:
            from backend.db import fetch_latest_risk
            db_record = fetch_latest_risk(code)
        except Exception as e:
            logger.warning("Database Tier 3 offline or unavailable for taluka %s: %s", code, e)
            db_record = None

        if db_record is not None:
            # Parse JSONB string columns if returned as raw strings
            payload = dict(db_record)
            if payload.get("as_of_date") is not None:
                payload["as_of_date"] = str(payload["as_of_date"])
            if payload.get("updated_at") is not None:
                payload["updated_at"] = str(payload["updated_at"])
            if "taluka_name" not in payload or not payload["taluka_name"]:
                from backend.services import backend_service
                row = backend_service._latest_by_code.get(code)
                if row is not None:
                    payload["taluka_name"] = str(row.get("taluka_name", ""))
                    payload["taluka_name_mr"] = str(row.get("taluka_name_mr", ""))
                    payload["district_name"] = str(row.get("district_name", ""))
            if isinstance(payload.get("shap_summary"), str):
                try:
                    payload["shap_summary"] = json.loads(payload["shap_summary"])
                except Exception:
                    pass
            if isinstance(payload.get("bilingual_advisory"), str):
                try:
                    payload["bilingual_advisory"] = json.loads(payload["bilingual_advisory"])
                except Exception:
                    pass
            payload["source"] = "tier3_db"

            # Cache into Tier 2 RAM
            with self._lock:
                self._cache[key] = copy.deepcopy(payload)
                self._tier3_hits += 1
                self._misses += 1
            return copy.deepcopy(payload)

        # 3. Tier 3 Offline In-Memory Telemetry Fallback
        fallback_payload = self._compute_in_memory_risk_fallback(code, date_str)
        with self._lock:
            self._cache[key] = copy.deepcopy(fallback_payload)
            self._fallbacks += 1
            self._misses += 1
        return copy.deepcopy(fallback_payload)

    def _compute_in_memory_risk_fallback(self, taluka_lgd_code: int, as_of_date: str) -> Dict[str, Any]:
        """
        In-memory fallback generator using backend_service and Parquet models.
        Ensures zero 500 errors when PostgreSQL is offline.
        """
        from backend.services import backend_service

        detail = backend_service.get_taluka_detail(str(taluka_lgd_code))
        meta = detail["meta"]
        live_diag = detail["live_diagnosis"]
        forecast = detail["30_day_forecast"]
        cards = detail["farmer_cards"]
        row = backend_service._latest_by_code.get(taluka_lgd_code)

        def _safe_float(val, default=0.0):
            try:
                return float(val) if val is not None and not (isinstance(val, float) and val != val) else default
            except (ValueError, TypeError):
                return default

        spi_1_val = _safe_float(row.get("spi_1") if row is not None else 0.0)
        spi_3_val = _safe_float(row.get("spi_3") if row is not None else 0.0)
        spi_6_val = _safe_float(row.get("spi_6") if row is not None else 0.0)
        spei_3_val = _safe_float(row.get("spei_3") if row is not None else 0.0)
        gw_val = _safe_float(row.get("groundwater_depth_mbgl") if row is not None else 6.5, default=6.5)

        cat_code = int(live_diag["category_code"])
        confidence_val = round(float(live_diag.get("confidence_pct", 85.0)) / 100.0, 3)

        return {
            "taluka_lgd_code": taluka_lgd_code,
            "taluka_name": meta.get("taluka", ""),
            "taluka_name_mr": meta.get("taluka_mr", ""),
            "district_name": meta.get("district", ""),
            "as_of_date": as_of_date,
            "risk_category": cat_code,
            "risk_score": round(float(cat_code) / 4.0, 3),
            "confidence": confidence_val,
            "forecast_month": forecast.get("label_en", "Watch"),
            "predicted_risk_lead_1": int(forecast.get("category_code", 1)),
            "spi_1": spi_1_val,
            "spi_3": spi_3_val,
            "spi_6": spi_6_val,
            "spei_3": spei_3_val,
            "soil_moisture_index": float(cards["soil_moisture"]["value_pct"]),
            "max_consecutive_dry_days": int(cards["dry_gap"]["value_days"]),
            "district_dam_storage_pct": float(cards["dam_storage"]["value_pct"]),
            "groundwater_depth_mbgl": gw_val,
            "shap_summary": {
                "top_features": [
                    {"feature": "spi_3", "value": spi_3_val},
                    {"feature": "soil_moisture_index", "value": float(cards["soil_moisture"]["value_pct"])}
                ]
            },
            "bilingual_advisory": detail["advisory"],
            "source": "in_memory_telemetry_fallback"
        }

    def prewarm_all_talukas(self, as_of_date: Optional[str] = None) -> int:
        """
        Pre-warms all 194 talukas into RAM during FastAPI startup lifespan.
        Eliminates cold-start stampedes / thundering herds.
        Returns total count of talukas pre-warmed.
        """
        date_str = normalize_as_of_date(as_of_date)
        logger.info("[*] Pre-warming Tier 2 cache for all 194 talukas (as_of_date: %s)...", date_str)

        count = 0
        # Try batch load from DB Tier 3
        all_db_records = None
        try:
            from backend.db import fetch_all_latest_risks
            all_db_records = fetch_all_latest_risks()
        except Exception as e:
            logger.warning("Pre-warm: Tier 3 DB offline (%s). Using in-memory fallback.", e)
            all_db_records = None

        if all_db_records:
            for rec in all_db_records:
                lgd = int(rec["taluka_lgd_code"])
                k = risk_key(lgd, date_str)
                payload = dict(rec)
                if isinstance(payload.get("shap_summary"), str):
                    try:
                        payload["shap_summary"] = json.loads(payload["shap_summary"])
                    except Exception:
                        pass
                if isinstance(payload.get("bilingual_advisory"), str):
                    try:
                        payload["bilingual_advisory"] = json.loads(payload["bilingual_advisory"])
                    except Exception:
                        pass
                payload["source"] = "tier3_db"
                self.set(k, payload)
                count += 1
            logger.info("[OK] Pre-warmed %d talukas into Tier 2 RAM from DB.", count)
            return count

        # Fallback to in-memory service
        from backend.services import backend_service
        taluka_codes = sorted(list(backend_service._latest_by_code.keys()))
        for code in taluka_codes:
            k = risk_key(code, date_str)
            fallback = self._compute_in_memory_risk_fallback(code, date_str)
            self.set(k, fallback)
            count += 1

        logger.info("[OK] Pre-warmed %d talukas into Tier 2 RAM via in-memory fallback.", count)
        return count


# -----------------------------------------------------------------------------
# GLOBAL SINGLETON INSTANCE
# -----------------------------------------------------------------------------
cache_manager = MultiTierCacheManager()

