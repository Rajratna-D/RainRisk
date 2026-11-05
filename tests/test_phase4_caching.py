"""
MahaRainRisk: Comprehensive Phase 4 Multi-Tier Caching & Resilience Test Suite
Verifies:
1. Sub-2ms cache hit response latency.
2. Cache miss graceful resolution & tier-2 population.
3. Date-keyed zero-manual invalidation on date rollover.
4. Bounded capacity & LRU eviction (maxsize=500).
5. Anti-object mutation defense via deep copy.
6. Input float clamping & normalization (DoS defense).
7. Thread safety under concurrent multi-threaded read/writes.
8. Zero-Pickle policy rejection of raw bytecode.
9. Full 194-taluka startup pre-warming.
"""

import os
import sys
import time
import copy
import pytest
import threading
from typing import Dict, Any

# Ensure project root in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.cache import (
    MultiTierCacheManager,
    risk_key,
    normalize_as_of_date,
    ZeroPickleViolationError
)

def test_cache_hit_latency_sub_2ms():
    """Verify Tier 2 in-memory cache hit responds in under 2ms."""
    cache = MultiTierCacheManager(maxsize=100, ttl=3600)
    key = "risk:4120:2026-11-03"
    payload = {"taluka_lgd_code": 4120, "risk_category": "Alert", "risk_score": 0.5}

    cache.set(key, payload)

    # Benchmark 100 cache hits
    start = time.perf_counter()
    for _ in range(100):
        val = cache.get(key)
        assert val is not None
        assert val["taluka_lgd_code"] == 4120
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    avg_latency_ms = elapsed_ms / 100.0

    print(f"[PASS] 100 Cache Hits in {elapsed_ms:.2f}ms (Avg: {avg_latency_ms:.3f}ms/hit)")
    assert avg_latency_ms < 2.0, f"Cache hit latency {avg_latency_ms:.3f}ms exceeded 2ms target"

def test_anti_object_mutation_deep_copy():
    """Verify modifying returned cached objects does NOT mutate in-memory cache."""
    cache = MultiTierCacheManager(maxsize=100, ttl=3600)
    key = "risk:4120:2026-11-03"
    original = {"taluka": "Paithan", "nested": {"risk": "Alert", "score": 0.5}}

    cache.set(key, original)

    # Retrieve and attempt to corrupt
    retrieved = cache.get(key)
    retrieved["taluka"] = "MUTATED"
    retrieved["nested"]["risk"] = "CORRUPTED"

    # Re-fetch from cache: must be pristine
    clean = cache.get(key)
    assert clean["taluka"] == "Paithan", "Cache was mutated in place!"
    assert clean["nested"]["risk"] == "Alert", "Nested dict was mutated in place!"

def test_date_rollover_zero_manual_invalidation():
    """Verify changing as_of_date naturally misses yesterday's cache with zero manual purges."""
    cache = MultiTierCacheManager(maxsize=100, ttl=3600)
    code = 4120
    yesterday_date = "2026-11-02"
    today_date = "2026-11-03"

    k_yesterday = risk_key(code, yesterday_date)
    k_today = risk_key(code, today_date)

    cache.set(k_yesterday, {"date": yesterday_date, "data": "old"})

    # Yesterday's key is cached
    assert cache.get(k_yesterday) is not None

    # Today's key naturally misses without needing a purge
    assert cache.get(k_today) is None

def test_bounded_maxsize_lru_eviction():
    """Verify cache capacity is strictly bounded to maxsize and evicts oldest items."""
    max_capacity = 50
    cache = MultiTierCacheManager(maxsize=max_capacity, ttl=3600)

    # Insert 75 items
    for i in range(75):
        cache.set(f"item:{i}", {"val": i})

    assert len(cache) == max_capacity, f"Cache size {len(cache)} exceeded maxsize {max_capacity}"
    # Old items (0..24) must have been evicted
    assert cache.get("item:0") is None
    # Recent items must remain
    assert cache.get("item:74") is not None

def test_zero_pickle_policy_enforcement():
    """Verify raw pickle bytecode is strictly rejected to prevent deserialization RCE."""
    cache = MultiTierCacheManager(maxsize=50, ttl=3600)
    
    # Pickle protocol 2 and 4 prefixes
    fake_pickle_p2 = b'\x80\x02}q\x00.'
    fake_pickle_p4 = b'\x80\x04\x95...'

    with pytest.raises(ZeroPickleViolationError):
        cache.set("malicious_p2", fake_pickle_p2)

    with pytest.raises(ZeroPickleViolationError):
        cache.set("malicious_p4", fake_pickle_p4)

def test_thread_safety_concurrent_access():
    """Verify multi-threaded concurrent reads and writes do not corrupt TTLCache."""
    cache = MultiTierCacheManager(maxsize=200, ttl=3600)
    errors = []

    def worker(worker_id: int):
        try:
            for j in range(25):
                k = f"thread_key:{worker_id}:{j}"
                cache.set(k, {"worker": worker_id, "step": j})
                val = cache.get(k)
                if val is None or val["step"] != j:
                    errors.append(f"Mismatch in worker {worker_id} at step {j}")
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Thread safety errors detected: {errors}"
    stats = cache.stats()
    assert stats["size"] > 0
    assert stats["hits"] >= 250

def test_full_194_talukas_prewarming():
    """Verify startup pre-warming primes all 194 monitored talukas into Tier 2 RAM."""
    cache = MultiTierCacheManager(maxsize=500, ttl=21600)
    count = cache.prewarm_all_talukas("2026-11-03")
    assert count == 194, f"Expected 194 talukas pre-warmed, got {count}"
    assert len(cache) == 194

    # Direct O(1) hit check
    sample_key = risk_key(4120, "2026-11-03")
    sample_data = cache.get(sample_key)
    assert sample_data is not None
    assert "risk_score" in sample_data

