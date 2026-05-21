"""
Configuration and default parameters for the RA stress testing tool.

All parameters are based on the Research Affiliates Capital Market
Expectations methodology documentation.
"""

from dataclasses import dataclass, field
from typing import Dict, Any
from enum import Enum


class Region(Enum):
    """Geographic regions for asset classes."""
    US = "us"
    EUROPE = "europe"
    JAPAN = "japan"
    EM = "em"
    GLOBAL_DM = "global_dm"
    GLOBAL = "global"


class BaseCurrency(Enum):
    """Supported base currencies for return calculations."""
    USD = "usd"
    EUR = "eur"


class AssetClass(Enum):
    """Supported asset classes."""
    LIQUIDITY = "liquidity"
    BONDS_GLOBAL = "bonds_global"
    BONDS_HY = "bonds_hy"
    BONDS_EM = "bonds_em"
    INFLATION_LINKED = "inflation_linked"
    EQUITY_US = "equity_us"
    EQUITY_EUROPE = "equity_europe"
    EQUITY_JAPAN = "equity_japan"
    EQUITY_EM = "equity_em"
    ABSOLUTE_RETURN = "absolute_return"


# =============================================================================
# EWMA Parameters
# =============================================================================

@dataclass
class EWMAParams:
    """EWMA calculation parameters."""
    window_years: int
    half_life_years: float


EWMA_PARAMS = {
    'productivity_growth': EWMAParams(window_years=10, half_life_years=5),
    'inflation_dm': EWMAParams(window_years=10, half_life_years=5),
    'inflation_em': EWMAParams(window_years=10, half_life_years=2),
    'tbill_country_factor': EWMAParams(window_years=10, half_life_years=5),
    'bond_term_premium': EWMAParams(window_years=50, half_life_years=20),
    'credit_spread': EWMAParams(window_years=50, half_life_years=20),
    'caey_fair_value': EWMAParams(window_years=50, half_life_years=20),
}


# =============================================================================
# Credit Parameters
# =============================================================================

CREDIT_PARAMS = {
    'investment_grade': {
        'default_rate': 0.001,      # 0.1%
        'recovery_rate': 0.70,      # 70%
        'transition_rate': 0.06,    # 6%
    },
    'high_yield': {
        'default_rate': 0.055,      # 5.5%
        'recovery_rate': 0.40,      # 40%
        'transition_rate': 0.01,    # 1%
    },
    'em_hard_currency': {
        'default_rate': 0.028,      # 2.8%
        'recovery_rate': 0.55,      # 55%
        'transition_rate': 0.00,    # 0%
    },
    'em_local_currency': {
        'default_rate': 0.0018,     # 0.18%
        'recovery_rate': 0.40,      # 40%
        'transition_rate': 0.00,    # 0%
    },
}


# =============================================================================
# Mean Reversion Parameters
# =============================================================================

MEAN_REVERSION_PARAMS = {
    'macro_convergence_speed': 0.03,           # 3% per month
    'equity_caey_full_reversion_years': 20,    # 20 years
    'bond_term_premium_bounds': (-1.0, -0.015),  # Mean reversion speed bounds
    'tbill_rate_floor': -0.0075,               # -0.75%
}


# =============================================================================
# Inflation Model Parameters
# =============================================================================

INFLATION_PARAMS = {
    'current_weight': 0.30,         # Weight on current headline inflation
    'long_term_weight': 0.70,       # Weight on long-term inflation
}


# =============================================================================
# T-Bill Model Parameters
# =============================================================================

TBILL_PARAMS = {
    'current_weight': 0.30,         # Weight on current T-Bill rate
    'long_term_weight': 0.70,       # Weight on long-term rate
    'rate_floor': -0.0075,          # -0.75% floor
    'country_factor_bounds': (-0.001, 0.001),  # -0.1% to +0.1%
}


# =============================================================================
# Bond Model Parameters
# =============================================================================

BOND_PARAMS = {
    'term_premium_reversion_speed': -0.05,  # Default mean reversion speed
    'yield_floor': 0.0,                      # Minimum yield
}


# =============================================================================
# Equity Model Parameters
# =============================================================================

EQUITY_PARAMS = {
    'valuation_reversion_years': 20,     # Years to full CAEY mean reversion
    'forecast_horizon': 10,               # 10-year forecast
    'country_weight': 0.50,               # Weight on country-specific EPS growth
    'regional_weight': 0.50,              # Weight on regional EPS growth
    'eps_growth_window_years': 50,        # Years for EPS trend calculation
}


# =============================================================================
# Grinold-Kroner Equity Model Parameters
# =============================================================================

EQUITY_PARAMS_GK = {
    'pe_reversion_years': 10,             # Forecast horizon for P/E convergence
}


# =============================================================================
# Hedge Fund Factor Parameters
# =============================================================================

HEDGE_FUND_PARAMS = {
    'historical_discount': 0.50,          # Use 50% of historical for some factors
    'factor_exposures': {
        # Default factor betas (from typical diversified HF)
        'market': 0.30,
        'size': 0.10,
        'value': 0.05,
        'profitability': 0.05,
        'investment': 0.05,
        'momentum': 0.10,
    },
    'historical_factor_premia': {
        # Long-term historical factor premia (annualized)
        'market': 0.05,          # 5% equity risk premium
        'size': 0.02,            # 2% SMB
        'value': 0.03,           # 3% HML
        'profitability': 0.025,  # 2.5% RMW
        'investment': 0.025,     # 2.5% CMA
        'momentum': 0.06,        # 6% UMD
    },
}


# =============================================================================
# Default Market Data (Placeholder values - user should override)
# =============================================================================

DEFAULT_MARKET_DATA = {
    # Q2 2026 defaults — back-solved so direct forecasts land on
    # US 3/1.2/4, EZ 2/1/2.5, JP 1.5/0.8/1.75, EM 4/3.4/4
    # US Macro
    'us': {
        'current_headline_inflation': 0.030,   # 3.0%
        'current_tbill': 0.0353,               # 3.53% (back-solves E[T-Bill] to 4.0%)
        'population_growth': 0.004,            # 0.4%
        'productivity_growth': 0.012,          # 1.2%
        'my_ratio': 2.1,                       # Middle/Young ratio
    },
    # Eurozone Macro
    'eurozone': {
        'current_headline_inflation': 0.020,   # 2.0%
        'current_tbill': 0.0180,               # 1.80%
        'population_growth': 0.001,            # 0.1%
        'productivity_growth': 0.0149,         # 1.49% (back-solves E[RGDP] to 1.0%)
        'my_ratio': 2.3,
    },
    # Japan Macro
    'japan': {
        'current_headline_inflation': 0.015,   # 1.5%
        'current_tbill': 0.0162,               # 1.62%
        'population_growth': -0.002,           # -0.2%
        'productivity_growth': 0.0159,         # 1.59%
        'my_ratio': 2.3,
    },
    # Emerging Markets Macro (aggregate)
    'em': {
        'current_headline_inflation': 0.040,   # 4.0%
        'current_tbill': 0.040,                # 4.0%
        'population_growth': 0.010,            # 1.0%
        'productivity_growth': 0.0244,         # 2.44%
        'my_ratio': 1.5,
    },
}


# =============================================================================
# Default Asset Class Data (Placeholder values - user should override)
# =============================================================================

DEFAULT_ASSET_DATA = {
    AssetClass.LIQUIDITY: {
        'region': Region.US,
    },

    AssetClass.BONDS_GLOBAL: {
        'current_yield': 0.035,                # 3.5%
        'duration': 7.0,                       # 7 years
        'current_term_premium': 0.01,          # 1.0%
        'fair_term_premium': 0.015,            # 1.5%
    },

    AssetClass.BONDS_HY: {
        'current_yield': 0.075,                # 7.5%
        'duration': 4.0,                       # 4 years
        'credit_spread': 0.0271,               # 2.71% (ICE BofA HY OAS)
        'fair_credit_spread': 0.04,            # 4.0%
        'default_rate': 0.055,                 # 5.5%
        'recovery_rate': 0.40,                 # 40%
    },

    AssetClass.BONDS_EM: {
        'current_yield': 0.0577,               # 5.77% (BBG EM USD Aggregate Index YTM)
        'duration': 5.5,                       # 5.5 years
        'current_term_premium': 0.015,         # 1.5%
        'fair_term_premium': 0.02,             # 2.0%
        'default_rate': 0.028,                 # 2.8% (EM hard currency)
        'recovery_rate': 0.55,                 # 55%
    },

    AssetClass.INFLATION_LINKED: {
        # Regime selected by base currency at runtime
        # USD = US TIPS assumptions, EUR = Euro inflation-linked sovereign assumptions
        'usd': {
            'current_real_yield': 0.0180,          # 1.80%
            'duration': 6.4,                       # Years
            'current_real_term_premium': 0.0030,   # 0.30%
            'fair_real_term_premium': 0.0020,      # 0.20%
            'inflation_beta': 1.0,                 # Unitless
            'index_lag_drag': 0.0010,              # 0.10%
            'liquidity_technical': 0.0005,         # 0.05%
        },
        'eur': {
            'current_real_yield': 0.0075,          # 0.75%
            'duration': 7.5,                       # Years
            'current_real_term_premium': 0.0015,   # 0.15%
            'fair_real_term_premium': 0.0010,      # 0.10%
            'inflation_beta': 1.0,                 # Unitless
            'index_lag_drag': 0.0015,              # 0.15%
            'liquidity_technical': 0.0010,         # 0.10%
        },
    },

    AssetClass.EQUITY_US: {
        # RA model defaults
        'dividend_yield': 0.0113,              # 1.13% (S&P 500 TTM)
        'current_caey': 0.0248,                # 2.48% (CAPE ~40)
        'fair_caey': 0.05,                     # 5.0% (CAPE ~20)
        'real_eps_growth': 0.018,              # 1.8%
        'regional_eps_growth': 0.016,          # DM average
        'reversion_speed': 1.0,                # 100% = full CAEY mean reversion
        # GK model defaults (coexist; each model reads only its own keys)
        'net_buyback_yield': 0.015,            # 1.5%
        'revenue_gdp_wedge': 0.020,            # 2.0%
        'revenue_growth': 0.055,               # 5.5% (computed from macro)
        'margin_change': -0.005,               # -0.5%
        'current_pe': 22.0,                    # Forward P/E
        'target_pe': 20.0,                     # Equilibrium P/E
    },

    AssetClass.EQUITY_EUROPE: {
        # RA model defaults
        'dividend_yield': 0.030,               # 3.0%
        'current_caey': 0.055,                 # 5.5%
        'fair_caey': 0.055,                    # 5.5%
        'real_eps_growth': 0.012,              # 1.2%
        'regional_eps_growth': 0.016,          # DM average
        'reversion_speed': 1.0,                # 100% = full CAEY mean reversion
        # GK model defaults
        'net_buyback_yield': 0.005,            # 0.5%
        'revenue_gdp_wedge': 0.005,            # 0.5%
        'revenue_growth': 0.034,               # 3.4%
        'margin_change': 0.000,                # 0.0%
        'current_pe': 14.0,
        'target_pe': 14.0,
    },

    AssetClass.EQUITY_JAPAN: {
        # RA model defaults
        'dividend_yield': 0.022,               # 2.2%
        'current_caey': 0.055,                 # 5.5%
        'fair_caey': 0.05,                     # 5.0%
        'real_eps_growth': 0.008,              # 0.8%
        'regional_eps_growth': 0.016,          # DM average
        'reversion_speed': 1.0,                # 100% = full CAEY mean reversion
        # GK model defaults
        'net_buyback_yield': 0.008,            # 0.8%
        'revenue_gdp_wedge': 0.005,            # 0.5%
        'revenue_growth': 0.025,               # 2.5%
        'margin_change': 0.003,                # 0.3%
        'current_pe': 15.0,
        'target_pe': 14.5,
    },

    AssetClass.EQUITY_EM: {
        # RA model defaults
        'dividend_yield': 0.030,               # 3.0%
        'current_caey': 0.065,                 # 6.5%
        'fair_caey': 0.06,                     # 6.0%
        'real_eps_growth': 0.030,              # 3.0%
        'regional_eps_growth': 0.028,          # EM average
        'reversion_speed': 1.0,                # 100% = full CAEY mean reversion
        # GK model defaults
        'net_buyback_yield': -0.015,           # -1.5%
        'revenue_gdp_wedge': 0.005,            # 0.5%
        'revenue_growth': 0.073,               # 7.3%
        'margin_change': 0.000,                # 0.0%
        'current_pe': 12.0,
        'target_pe': 12.0,
    },

    AssetClass.ABSOLUTE_RETURN: {
        'beta_market': 0.30,
        'beta_size': 0.10,
        'beta_value': 0.05,
        'beta_profitability': 0.05,
        'beta_investment': 0.05,
        'beta_momentum': 0.10,
        'trading_alpha': 0.01,                 # 1% (50% of historical ~2%)
    },
}


# =============================================================================
# Grinold-Kroner Default Asset Data
# Overlaid onto DEFAULT_ASSET_DATA when equity_model_type == "gk"
# =============================================================================

DEFAULT_ASSET_DATA_GK = {
    AssetClass.EQUITY_US: {
        'dividend_yield': 0.013,               # 1.3% (S&P 500 trailing)
        'net_buyback_yield': 0.015,            # 1.5% (gross ~3% minus ~1.5% dilution)
        'revenue_gdp_wedge': 0.020,            # 2.0% (S&P global revenue exposure)
        'margin_change': -0.005,               # -0.5% (mild compression from peak)
        'current_pe': 22.0,                    # Forward P/E
        'target_pe': 20.0,                     # Long-run equilibrium P/E
    },

    AssetClass.EQUITY_EUROPE: {
        'dividend_yield': 0.030,               # 3.0% (MSCI Europe)
        'net_buyback_yield': 0.005,            # 0.5% (lower buyback culture)
        'revenue_gdp_wedge': 0.005,            # 0.5%
        'margin_change': 0.000,                # 0.0% (flat)
        'current_pe': 14.0,                    # Forward P/E
        'target_pe': 14.0,                     # Near fair value
    },

    AssetClass.EQUITY_JAPAN: {
        'dividend_yield': 0.022,               # 2.2% (MSCI Japan)
        'net_buyback_yield': 0.008,            # 0.8% (growing buyback trend)
        'revenue_gdp_wedge': 0.005,            # 0.5%
        'margin_change': 0.003,                # 0.3% (corporate governance reform)
        'current_pe': 15.0,                    # Forward P/E
        'target_pe': 14.5,                     # Slight contraction
    },

    AssetClass.EQUITY_EM: {
        'dividend_yield': 0.030,               # 3.0% (MSCI EM)
        'net_buyback_yield': -0.015,           # -1.5% (net dilution from issuance)
        'revenue_gdp_wedge': 0.005,            # 0.5%
        'margin_change': 0.000,                # 0.0% (flat)
        'current_pe': 12.0,                    # Forward P/E
        'target_pe': 12.0,                     # Near fair value
    },
}


# =============================================================================
# Helper function to get nested config values
# =============================================================================

# =============================================================================
# Currency Configuration for FX Adjustments
# =============================================================================

# Asset to local currency mapping
# Defines what currency each asset class is denominated in
ASSET_LOCAL_CURRENCY = {
    AssetClass.LIQUIDITY: 'base',       # Uses base currency T-Bill
    AssetClass.BONDS_GLOBAL: 'usd',     # USD-hedged developed bonds
    AssetClass.BONDS_HY: 'usd',         # US High Yield
    AssetClass.BONDS_EM: 'usd',         # USD hard currency (EM sovereign bonds issued in USD)
    AssetClass.INFLATION_LINKED: 'base',# Uses base currency regime directly (USD TIPS or EUR ILBs)
    AssetClass.EQUITY_US: 'usd',
    AssetClass.EQUITY_EUROPE: 'eur',
    AssetClass.EQUITY_JAPAN: 'jpy',
    AssetClass.EQUITY_EM: 'em',
    AssetClass.ABSOLUTE_RETURN: 'base', # Uses base currency T-Bill
}

# Macro region mapping for FX calculations
CURRENCY_TO_MACRO_REGION = {
    'usd': 'us',
    'eur': 'eurozone',
    'jpy': 'japan',
    'em': 'em',
}


# =============================================================================
# Expected Volatility (Long-term historical estimates)
# =============================================================================

EXPECTED_VOLATILITY = {
    AssetClass.LIQUIDITY: 0.01,          # 1% - Cash/T-Bills
    AssetClass.BONDS_GLOBAL: 0.06,       # 6% - Global Gov Bonds
    AssetClass.BONDS_HY: 0.10,           # 10% - High Yield
    AssetClass.BONDS_EM: 0.12,           # 12% - EM Hard Currency
    AssetClass.INFLATION_LINKED: 0.07,   # 7% - DM inflation-linked sovereign bonds
    AssetClass.EQUITY_US: 0.16,          # 16% - US Equities
    AssetClass.EQUITY_EUROPE: 0.18,      # 18% - Europe Equities
    AssetClass.EQUITY_JAPAN: 0.18,       # 18% - Japan Equities
    AssetClass.EQUITY_EM: 0.24,          # 24% - EM Equities
    AssetClass.ABSOLUTE_RETURN: 0.08,    # 8% - Hedge Funds
}


def get_config_value(config_dict: Dict[str, Any], *keys, default=None):
    """
    Safely get a nested configuration value.

    Parameters
    ----------
    config_dict : dict
        Configuration dictionary.
    *keys : str
        Sequence of keys to traverse.
    default : Any
        Default value if key path not found.

    Returns
    -------
    Any
        The configuration value or default.
    """
    result = config_dict
    for key in keys:
        if isinstance(result, dict) and key in result:
            result = result[key]
        else:
            return default
    return result
