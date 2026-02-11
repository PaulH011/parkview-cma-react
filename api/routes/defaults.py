"""
Default values endpoint.

Exposes all default input values for the frontend.
Loads dynamically from Supabase if available, with fallback to hardcoded values.
"""

import os
import time
import json
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()

# ---- Hardcoded fallback defaults (original source of truth) ----
INPUT_DEFAULTS = {
    "macro": {
        "us": {
            "inflation_forecast": 2.29,
            "rgdp_growth": 1.20,
            "tbill_forecast": 3.79,
            "population_growth": 0.40,
            "productivity_growth": 1.20,
            "my_ratio": 2.1,
            "current_headline_inflation": 2.50,
            "long_term_inflation": 2.20,
            "current_tbill": 3.67,
            "country_factor": 0.00,
        },
        "eurozone": {
            "inflation_forecast": 2.06,
            "rgdp_growth": 0.80,
            "tbill_forecast": 2.70,
            "population_growth": 0.10,
            "productivity_growth": 1.00,
            "my_ratio": 2.3,
            "current_headline_inflation": 2.20,
            "long_term_inflation": 2.00,
            "current_tbill": 2.04,
            "country_factor": 0.00,
        },
        "japan": {
            "inflation_forecast": 1.65,
            "rgdp_growth": 0.30,
            "tbill_forecast": 1.00,
            "population_growth": -0.50,
            "productivity_growth": 0.80,
            "my_ratio": 2.5,
            "current_headline_inflation": 2.00,
            "long_term_inflation": 1.50,
            "current_tbill": 0.75,
            "country_factor": 0.00,
        },
        "em": {
            "inflation_forecast": 3.80,
            "rgdp_growth": 3.00,
            "tbill_forecast": 5.50,
            "population_growth": 1.00,
            "productivity_growth": 2.50,
            "my_ratio": 1.5,
            "current_headline_inflation": 4.50,
            "long_term_inflation": 3.50,
            "current_tbill": 6.00,
            "country_factor": 0.00,
        },
    },
    "bonds": {
        "global": {
            "current_yield": 3.50,
            "duration": 7.0,
            "fair_term_premium": 1.50,
            "current_term_premium": 1.00,
        },
        "hy": {
            "current_yield": 7.50,
            "duration": 4.0,
            "credit_spread": 2.71,
            "fair_credit_spread": 4.00,
            "default_rate": 5.50,
            "recovery_rate": 40.0,
        },
        "em": {
            "current_yield": 5.77,
            "duration": 5.5,
            "fair_term_premium": 2.00,
            "current_term_premium": 1.50,
            "default_rate": 2.80,
            "recovery_rate": 55.0,
        },
    },
    "equity": {
        "us": {
            "dividend_yield": 1.13,
            "current_caey": 2.48,
            "fair_caey": 5.00,
            "real_eps_growth": 1.80,
            "regional_eps_growth": 1.60,
            "reversion_speed": 100,
        },
        "europe": {
            "dividend_yield": 3.00,
            "current_caey": 5.50,
            "fair_caey": 5.50,
            "real_eps_growth": 1.20,
            "regional_eps_growth": 1.60,
            "reversion_speed": 100,
        },
        "japan": {
            "dividend_yield": 2.20,
            "current_caey": 5.50,
            "fair_caey": 5.00,
            "real_eps_growth": 0.80,
            "regional_eps_growth": 1.60,
            "reversion_speed": 100,
        },
        "em": {
            "dividend_yield": 3.00,
            "current_caey": 6.50,
            "fair_caey": 6.00,
            "real_eps_growth": 3.00,
            "regional_eps_growth": 2.80,
            "reversion_speed": 100,
        },
    },
    "absolute_return": {
        "trading_alpha": 1.00,
        "beta_market": 0.30,
        "beta_size": 0.10,
        "beta_value": 0.05,
        "beta_profitability": 0.05,
        "beta_investment": 0.05,
        "beta_momentum": 0.10,
    },
}

# ---- In-memory cache for Supabase defaults ----
_cached_defaults: Optional[Dict[str, Any]] = None
_cache_timestamp: float = 0.0
_CACHE_TTL_SECONDS = 300  # 5 minutes


def _get_supabase_client():
    """Get a Supabase client for fetching defaults."""
    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        if url and key:
            return create_client(url, key)
    except Exception as e:
        logger.warning("Could not create Supabase client: %s", e)
    return None


def invalidate_defaults_cache():
    """Invalidate the in-memory cache so next request fetches fresh data."""
    global _cached_defaults, _cache_timestamp
    _cached_defaults = None
    _cache_timestamp = 0.0


def get_current_defaults() -> Dict[str, Any]:
    """
    Get the current defaults, loading from Supabase if available.
    Falls back to hardcoded INPUT_DEFAULTS.
    Results are cached in memory with a 5-minute TTL.
    """
    global _cached_defaults, _cache_timestamp

    now = time.time()

    # Return cached if still valid
    if _cached_defaults is not None and (now - _cache_timestamp) < _CACHE_TTL_SECONDS:
        return _cached_defaults

    # Try loading from Supabase
    try:
        client = _get_supabase_client()
        if client:
            result = client.table("default_assumptions").select("defaults_json").eq("id", 1).execute()
            if result.data and len(result.data) > 0:
                db_defaults = result.data[0]["defaults_json"]
                if isinstance(db_defaults, str):
                    db_defaults = json.loads(db_defaults)
                _cached_defaults = db_defaults
                _cache_timestamp = now
                logger.info("Loaded defaults from Supabase")
                return _cached_defaults
    except Exception as e:
        logger.warning("Could not load from Supabase, using hardcoded: %s", e)

    # Fallback to hardcoded
    _cached_defaults = INPUT_DEFAULTS
    _cache_timestamp = now
    return _cached_defaults


@router.get("/all")
async def get_all_defaults():
    """
    Get all default input values.

    Returns the complete set of default assumptions used when no override is specified.
    Values are in percentage points (e.g., 2.29 means 2.29%).

    Loads dynamically from Supabase if available, with fallback to hardcoded values.
    """
    return get_current_defaults()


@router.get("/macro/{region}")
async def get_macro_defaults(region: str):
    """
    Get macro defaults for a specific region.

    Parameters:
        region: us, eurozone, japan, or em
    """
    defaults = get_current_defaults()
    region_lower = region.lower()
    if region_lower not in defaults["macro"]:
        return {"error": f"Unknown region: {region}. Valid: us, eurozone, japan, em"}
    return defaults["macro"][region_lower]


@router.get("/bonds/{bond_type}")
async def get_bond_defaults(bond_type: str):
    """
    Get bond defaults for a specific type.

    Parameters:
        bond_type: global, hy, or em
    """
    defaults = get_current_defaults()
    if bond_type not in defaults["bonds"]:
        return {"error": f"Unknown bond type: {bond_type}. Valid: global, hy, em"}
    return defaults["bonds"][bond_type]


@router.get("/equity/{region}")
async def get_equity_defaults(region: str):
    """
    Get equity defaults for a specific region.

    Parameters:
        region: us, europe, japan, or em
    """
    defaults = get_current_defaults()
    if region not in defaults["equity"]:
        return {"error": f"Unknown region: {region}. Valid: us, europe, japan, em"}
    return defaults["equity"][region]
