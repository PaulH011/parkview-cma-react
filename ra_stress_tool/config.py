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
        'current_tbill': 0.0360,               # 3.60% (E[T-Bill] = 4.02%)
        'population_growth': 0.004,            # 0.4%
        'productivity_growth': 0.012,          # 1.2%
        'my_ratio': 2.1,                       # Middle/Young ratio
    },
    # Eurozone Macro
    'eurozone': {
        'current_headline_inflation': 0.020,   # 2.0%
        'current_tbill': 0.0210,               # 2.10% (E[T-Bill] = 2.59%)
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

    # Q2 2026 bond defaults — term premium back-solved so avg_yield = current_yield
    AssetClass.BONDS_GLOBAL: {
        # Regime selected by base currency at runtime
        # USD = US Treasury / Global Aggregate USD-centric assumptions
        # EUR = Bund / EUR sovereign aggregate assumptions
        'usd': {
            'current_yield': 0.046,                # 4.6% (US 10y UST proxy)
            'duration': 8.0,                       # 8 years
            # TP normalizes upward (0.81 -> 1.00) over horizon
            'current_term_premium': 0.0081,        # 0.81%
            'fair_term_premium': 0.010,            # 1.00%
        },
        'eur': {
            'current_yield': 0.030,                # 3.0% (10y Bund)
            'duration': 7.5,                       # 7.5 years
            # TP normalizes upward 0.40 -> 0.50 over horizon
            'current_term_premium': 0.004,         # 0.40%
            'fair_term_premium': 0.005,            # 0.50%
        },
    },

    AssetClass.BONDS_HY: {
        'current_yield': 0.071,                # 7.1%
        'duration': 3.0,                       # 3 years
        # TP now represents duration risk only (credit risk captured by
        # credit_spread + credit_loss). Yield component will be ~5%.
        'current_term_premium': 0.010,         # 1.0%
        'fair_term_premium': 0.010,            # 1.0%
        'credit_spread': 0.026,                # 2.6%
        'fair_credit_spread': 0.04,            # 4.0%
        'default_rate': 0.034,                 # 3.4%
        'recovery_rate': 0.40,                 # 40%
    },

    AssetClass.BONDS_EM: {
        'current_yield': 0.060,                # 6.0% (EM USD sovereign aggregate)
        'duration': 5.8,                       # 5.8 years
        # EM model adds em_spread=2% on top of US T-Bill; base rate = 6%.
        # TP rises 0.81 -> 1.00 over horizon.
        'current_term_premium': 0.0081,        # 0.81%
        'fair_term_premium': 0.010,            # 1.00%
        'default_rate': 0.034,                 # 3.4%
        'recovery_rate': 0.55,                 # 55%
    },

    AssetClass.INFLATION_LINKED: {
        # Regime selected by base currency at runtime
        # USD = US TIPS assumptions, EUR = Euro inflation-linked sovereign assumptions
        'usd': {
            'current_real_yield': 0.0210,          # 2.10% (10y TIPS)
            'duration': 4.3,                       # Years
            'current_real_term_premium': 0.0080,   # 0.80%
            'fair_real_term_premium': 0.0080,      # 0.80%
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
        # Q2 2026 RA model defaults
        'dividend_yield': 0.011,               # 1.1% (S&P 500 TTM)
        'current_caey': 0.025,                 # 2.5% (CAPE ~40)
        'fair_caey': 0.043,                    # 4.3% (CAPE ~23)
        'real_eps_growth': 0.018,              # 1.8%
        'regional_eps_growth': 0.016,          # DM average
        'reversion_speed': 1.0,                # 100% = full CAEY mean reversion
        # Q2 2026 GK model defaults (coexist; each model reads only its own keys)
        'net_buyback_yield': 0.013,            # 1.3%
        'revenue_gdp_wedge': 0.020,            # 2.0%
        'revenue_growth': 0.062,               # 6.2% display (auto = inflation 3.0 + GDP 1.2 + wedge 2.0)
        'margin_change': -0.005,               # -0.5%
        'current_pe': 21.3,                    # Forward P/E
        'target_pe': 22.7,                     # Equilibrium P/E
    },

    AssetClass.EQUITY_EUROPE: {
        # Q2 2026 RA model defaults
        'dividend_yield': 0.028,               # 2.8%
        'current_caey': 0.044,                 # 4.4%
        'fair_caey': 0.043,                    # 4.3% (basically at fair value)
        'real_eps_growth': 0.012,              # 1.2%
        'regional_eps_growth': 0.016,          # DM average
        'reversion_speed': 1.0,                # 100% = full CAEY mean reversion
        # Q2 2026 GK model defaults
        'net_buyback_yield': 0.007,            # 0.7%
        'revenue_gdp_wedge': 0.005,            # 0.5%
        'revenue_growth': 0.035,               # 3.5% display (auto = 2.0 + 1.0 + 0.5)
        'margin_change': 0.000,                # 0.0%
        'current_pe': 14.9,
        'target_pe': 16.4,
    },

    AssetClass.EQUITY_JAPAN: {
        # Q2 2026 RA model defaults
        'dividend_yield': 0.019,               # 1.9%
        'current_caey': 0.037,                 # 3.7%
        'fair_caey': 0.037,                    # 3.7% (at fair value, no valuation drift)
        'real_eps_growth': 0.008,              # 0.8%
        'regional_eps_growth': 0.016,          # DM average
        'reversion_speed': 1.0,                # 100% = full CAEY mean reversion
        # Q2 2026 GK model defaults
        'net_buyback_yield': 0.014,            # 1.4%
        'revenue_gdp_wedge': 0.005,            # 0.5%
        'revenue_growth': 0.028,               # 2.8% display (auto = 1.5 + 0.8 + 0.5)
        'margin_change': 0.003,                # 0.3%
        'current_pe': 21.9,
        'target_pe': 22.1,
    },

    AssetClass.EQUITY_EM: {
        # Q2 2026 RA model defaults
        'dividend_yield': 0.022,               # 2.2%
        'current_caey': 0.038,                 # 3.8% (CAPE ~26 — currently rich vs fair)
        'fair_caey': 0.058,                    # 5.8% (CAPE ~17)
        'real_eps_growth': 0.030,              # 3.0%
        'regional_eps_growth': 0.028,          # EM average
        'reversion_speed': 1.0,                # 100% = full CAEY mean reversion
        # Q2 2026 GK model defaults
        'net_buyback_yield': -0.006,           # -0.6%
        'revenue_gdp_wedge': 0.005,            # 0.5%
        'revenue_growth': 0.079,               # 7.9% display (auto = 4.0 + 3.4 + 0.5)
        'margin_change': 0.000,                # 0.0%
        'current_pe': 11.7,
        'target_pe': 15.0,
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
    # Q2 2026 GK defaults
    AssetClass.EQUITY_US: {
        'dividend_yield': 0.011,               # 1.1% (S&P 500)
        'net_buyback_yield': 0.013,            # 1.3%
        'revenue_gdp_wedge': 0.020,            # 2.0% (S&P global revenue exposure)
        'margin_change': -0.005,               # -0.5% (mild compression from peak)
        'current_pe': 21.3,                    # Forward P/E
        'target_pe': 22.7,                     # Equilibrium P/E
    },

    AssetClass.EQUITY_EUROPE: {
        'dividend_yield': 0.028,               # 2.8% (MSCI Europe)
        'net_buyback_yield': 0.007,            # 0.7%
        'revenue_gdp_wedge': 0.005,            # 0.5%
        'margin_change': 0.000,                # 0.0%
        'current_pe': 14.9,                    # Forward P/E
        'target_pe': 16.4,                     # Slight expansion
    },

    AssetClass.EQUITY_JAPAN: {
        'dividend_yield': 0.019,               # 1.9% (MSCI Japan)
        'net_buyback_yield': 0.014,            # 1.4%
        'revenue_gdp_wedge': 0.005,            # 0.5%
        'margin_change': 0.003,                # 0.3% (corporate governance reform)
        'current_pe': 21.9,                    # Forward P/E
        'target_pe': 22.1,                     # Near fair value
    },

    AssetClass.EQUITY_EM: {
        'dividend_yield': 0.022,               # 2.2% (MSCI EM)
        'net_buyback_yield': -0.006,           # -0.6% (net dilution from issuance)
        'revenue_gdp_wedge': 0.005,            # 0.5%
        'margin_change': 0.000,                # 0.0%
        'current_pe': 11.7,                    # Forward P/E
        'target_pe': 15.0,                     # Expected re-rating higher
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
    AssetClass.BONDS_GLOBAL: 'base',    # Regime-based (USD/EUR sovereign); no FX adjustment
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
