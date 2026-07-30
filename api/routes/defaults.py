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
        # Q2 2026 defaults — direct forecasts back-solved through building blocks
        "us": {
            "inflation_forecast": 3.00,
            "rgdp_growth": 1.20,
            "tbill_forecast": 4.02,           # 0.3*3.60 + 0.7*4.20
            "population_growth": 0.40,
            "productivity_growth": 1.20,
            "my_ratio": 2.1,
            "current_headline_inflation": 3.00,
            "long_term_inflation": 3.00,
            "current_tbill": 3.60,
            "country_factor": 0.00,
        },
        "eurozone": {
            "inflation_forecast": 2.00,
            "rgdp_growth": 1.00,
            "tbill_forecast": 2.59,           # 0.3*2.10 + 0.7*2.80
            "population_growth": 0.10,
            "productivity_growth": 1.49,
            "my_ratio": 2.3,
            "current_headline_inflation": 2.00,
            "long_term_inflation": 2.00,
            "current_tbill": 2.10,
            "country_factor": -0.20,
        },
        "japan": {
            "inflation_forecast": 1.50,
            "rgdp_growth": 0.80,
            "tbill_forecast": 1.75,
            "population_growth": -0.20,
            "productivity_growth": 1.59,
            "my_ratio": 2.3,
            "current_headline_inflation": 1.50,
            "long_term_inflation": 1.50,
            "current_tbill": 1.62,
            "country_factor": -0.50,
        },
        "em": {
            "inflation_forecast": 4.00,
            "rgdp_growth": 3.40,
            "tbill_forecast": 4.00,
            "population_growth": 1.00,
            "productivity_growth": 2.44,
            "my_ratio": 1.5,
            "current_headline_inflation": 4.00,
            "long_term_inflation": 4.00,
            "current_tbill": 4.00,
            # Negative country factor reflects structurally suppressed EM short
            # rates (financial repression / capital controls) — needed so the
            # 10y avg lands on 4% rather than the ~7% implied by RGDP + Inflation.
            "country_factor": -3.40,
        },
        "switzerland": {
            # CHF base currency only; not part of Global RGDP weights.
            # Calibrated mid-2026: CPI 0.5% (FSO), SNB policy 0%, 10y Eidgenosse 0.4%.
            "inflation_forecast": 0.85,       # 0.3*0.50 + 0.7*1.00
            "rgdp_growth": 1.20,
            "tbill_forecast": 0.60,           # 0.3*0.00 + 0.7*0.85
            "population_growth": 0.70,
            "productivity_growth": 1.00,
            "my_ratio": 2.2,
            "current_headline_inflation": 0.50,
            "long_term_inflation": 1.00,      # SNB price stability (0-2%); LT expectations ~1%
            "current_tbill": 0.00,            # SNB policy rate (SARON ~-0.04%)
            # Strongly negative: safe-haven franc keeps Swiss short rates
            # structurally below the RGDP + Inflation equilibrium.
            "country_factor": -1.20,
        },
    },
    "bonds": {
        # Q2 2026 defaults. Term-premium fields set so avg_yield = stated current_yield.
        "global": {
            # Regime-based: USD = US Treasury / Global Agg, EUR = Bund / EUR sovereign agg
            "usd": {
                "current_yield": 4.60,        # US 10y UST proxy
                "duration": 8.0,
                # TP normalizes upward (0.81 -> 1.00) over horizon
                "current_term_premium": 0.81,
                "fair_term_premium": 1.00,
            },
            "eur": {
                "current_yield": 3.00,        # 10y Bund
                "duration": 7.5,
                # TP normalizes upward 0.40 -> 0.50 over horizon
                "current_term_premium": 0.40,
                "fair_term_premium": 0.50,
            },
            "chf": {
                "current_yield": 0.40,        # 10y Swiss Confederation (Eidgenosse, Jul 2026)
                "duration": 9.0,              # SBI domestic government is long-duration (~9-10y)
                # Flat Swiss curve: TP normalizes -0.20 -> 0.20 over horizon
                "current_term_premium": -0.20,
                "fair_term_premium": 0.20,
            },
        },
        "hy": {
            "current_yield": 7.10,
            "duration": 3.0,
            # TP now represents duration risk only (credit risk captured by
            # credit_spread + credit_loss). Yield component will be ~5%.
            "current_term_premium": 1.00,
            "fair_term_premium": 1.00,
            "credit_spread": 2.60,
            "fair_credit_spread": 4.00,
            "default_rate": 3.40,
            "recovery_rate": 40.0,
        },
        "em": {
            "current_yield": 6.00,            # EM USD sovereign aggregate
            "duration": 5.8,
            # EM model adds em_spread=2% on top of US T-Bill internally;
            # base rate = 4+2 = 6%. TP rises 0.81 -> 1.00 over horizon.
            "current_term_premium": 0.81,
            "fair_term_premium": 1.00,
            "default_rate": 3.40,
            "recovery_rate": 55.0,
        },
        "inflation_linked": {
            "usd": {
                "current_real_yield": 2.10,   # 10y TIPS
                "duration": 4.3,
                "current_real_term_premium": 0.80,
                "fair_real_term_premium": 0.80,
                "inflation_beta": 1.00,
                "index_lag_drag": 0.10,
                "liquidity_technical": 0.05,
            },
            "eur": {
                "current_real_yield": 0.75,
                "duration": 7.5,
                "current_real_term_premium": 0.15,
                "fair_real_term_premium": 0.10,
                "inflation_beta": 1.00,
                "index_lag_drag": 0.15,
                "liquidity_technical": 0.10,
            },
        },
    },
    "equity": {
        # Q2 2026 RA equity defaults
        "us": {
            "dividend_yield": 1.10,
            "current_caey": 2.50,           # CAPE ~40
            "fair_caey": 4.30,              # CAPE ~23
            "real_eps_growth": 1.80,
            "regional_eps_growth": 1.60,
            "reversion_speed": 100,
        },
        "europe": {
            "dividend_yield": 2.80,
            "current_caey": 4.40,
            "fair_caey": 4.30,              # basically at fair value
            "real_eps_growth": 1.20,
            "regional_eps_growth": 1.60,
            "reversion_speed": 100,
        },
        "japan": {
            "dividend_yield": 1.90,
            "current_caey": 3.70,
            "fair_caey": 3.70,              # at fair value
            "real_eps_growth": 0.80,
            "regional_eps_growth": 1.60,
            "reversion_speed": 100,
        },
        "em": {
            "dividend_yield": 2.20,
            "current_caey": 3.80,           # CAPE ~26 — currently rich vs fair
            "fair_caey": 5.80,              # CAPE ~17
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

# ---- Grinold-Kroner equity defaults (values in percentage points / ratios) ----
INPUT_DEFAULTS_GK_EQUITY = {
    # Q2 2026 GK equity defaults
    "us": {
        "dividend_yield": 1.10,
        "net_buyback_yield": 1.30,
        "revenue_growth": 6.20,        # auto-computed: inflation 3.0 + GDP 1.2 + wedge 2.0
        "revenue_gdp_wedge": 2.00,
        "margin_change": -0.50,
        "current_pe": 21.3,
        "target_pe": 22.7,
    },
    "europe": {
        "dividend_yield": 2.80,
        "net_buyback_yield": 0.70,
        "revenue_growth": 3.50,        # inflation 2.0 + GDP 1.0 + wedge 0.5
        "revenue_gdp_wedge": 0.50,
        "margin_change": 0.00,
        "current_pe": 14.9,
        "target_pe": 16.4,
    },
    "japan": {
        "dividend_yield": 1.90,
        "net_buyback_yield": 1.40,
        "revenue_growth": 2.80,        # inflation 1.5 + GDP 0.8 + wedge 0.5
        "revenue_gdp_wedge": 0.50,
        "margin_change": 0.30,
        "current_pe": 21.9,
        "target_pe": 22.1,
    },
    "em": {
        "dividend_yield": 2.20,
        "net_buyback_yield": -0.60,
        "revenue_growth": 7.90,        # inflation 4.0 + GDP 3.4 + wedge 0.5
        "revenue_gdp_wedge": 0.50,
        "margin_change": 0.00,
        "current_pe": 11.7,
        "target_pe": 15.0,
    },
}

# ---- In-memory cache for Supabase defaults ----
_cached_defaults: Optional[Dict[str, Any]] = None
_cache_timestamp: float = 0.0
_CACHE_TTL_SECONDS = 300  # 5 minutes


def _deep_merge(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge updates into base (updates take precedence)."""
    merged = dict(base)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


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
                # Merge DB defaults onto hardcoded defaults so newly added keys
                # are always available even before DB schema/default refresh.
                _cached_defaults = _deep_merge(INPUT_DEFAULTS, db_defaults)
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
async def get_all_defaults(equity_model: str = "ra"):
    """
    Get all default input values.

    Returns the complete set of default assumptions used when no override is specified.
    Values are in percentage points (e.g., 2.29 means 2.29%).

    Query params:
        equity_model: 'ra' (default) or 'gk' (Grinold-Kroner equity defaults)
    """
    import copy
    defaults = get_current_defaults()

    if equity_model == "gk":
        # Swap equity section with GK defaults
        defaults = copy.deepcopy(defaults)
        defaults["equity"] = INPUT_DEFAULTS_GK_EQUITY

    return defaults


@router.get("/macro/{region}")
async def get_macro_defaults(region: str):
    """
    Get macro defaults for a specific region.

    Parameters:
        region: us, eurozone, japan, em, or switzerland
    """
    defaults = get_current_defaults()
    region_lower = region.lower()
    if region_lower not in defaults["macro"]:
        return {"error": f"Unknown region: {region}. Valid: {', '.join(defaults['macro'].keys())}"}
    return defaults["macro"][region_lower]


@router.get("/bonds/{bond_type}")
async def get_bond_defaults(bond_type: str):
    """
    Get bond defaults for a specific type.

    Parameters:
        bond_type: global, hy, em, or inflation_linked
    """
    defaults = get_current_defaults()
    if bond_type not in defaults["bonds"]:
        return {"error": f"Unknown bond type: {bond_type}. Valid: global, hy, em, inflation_linked"}
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
