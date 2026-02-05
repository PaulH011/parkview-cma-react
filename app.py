"""
Streamlit Frontend for Parkview CMA Tool

Run with: streamlit run app.py
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import json
import os
import io
from datetime import datetime
from ra_stress_tool.main import CMEEngine
from ra_stress_tool.config import AssetClass, EXPECTED_VOLATILITY

# =============================================================================
# Authentication
# =============================================================================

from auth.middleware import require_auth, logout, load_scenarios, save_scenario, delete_scenario
from auth.database import init_db
from chatbot.assistant import render_chatbot

# Initialize database and require authentication
init_db()
user = require_auth()
user_id = user['id']

# =============================================================================
# Scenario Management Functions (Now handled by auth.middleware)
# =============================================================================

# Note: load_scenarios, save_scenario, delete_scenario are now imported from auth.middleware
# and take user_id as first parameter

# Default values for all inputs (used for comparison to detect overrides)
def get_reset_version():
    """Get the current reset version counter."""
    return st.session_state.get('_reset_version', 0)

def widget_key(base_key):
    """Generate a versioned widget key that changes on reset."""
    return f"{base_key}_v{get_reset_version()}"

def get_input_value(key):
    """Get value from session_state or return default if not set."""
    # Look up using the versioned widget key
    wkey = widget_key(key)
    if wkey in st.session_state and st.session_state[wkey] is not None:
        return st.session_state[wkey]
    return INPUT_DEFAULTS.get(key)

INPUT_DEFAULTS = {
    # US Macro
    'macro_us_inflation_forecast': 2.29,
    'macro_us_rgdp_growth': 1.20,
    'macro_us_tbill_forecast': 3.79,
    'macro_us_population_growth': 0.40,
    'macro_us_productivity_growth': 1.20,
    'macro_us_my_ratio': 2.1,
    'macro_us_current_headline_inflation': 2.50,
    'macro_us_long_term_inflation': 2.20,
    'macro_us_current_tbill': 3.67,
    'macro_us_country_factor': 0.00,
    # Eurozone Macro
    'macro_eurozone_inflation_forecast': 2.06,
    'macro_eurozone_rgdp_growth': 0.80,
    'macro_eurozone_tbill_forecast': 2.70,
    'macro_eurozone_population_growth': 0.10,
    'macro_eurozone_productivity_growth': 1.00,
    'macro_eurozone_my_ratio': 2.3,
    'macro_eurozone_current_headline_inflation': 2.20,
    'macro_eurozone_long_term_inflation': 2.00,
    'macro_eurozone_current_tbill': 2.04,
    'macro_eurozone_country_factor': 0.00,
    # Japan Macro
    'macro_japan_inflation_forecast': 1.65,
    'macro_japan_rgdp_growth': 0.30,
    'macro_japan_tbill_forecast': 1.00,
    'macro_japan_population_growth': -0.50,
    'macro_japan_productivity_growth': 0.80,
    'macro_japan_my_ratio': 2.5,
    'macro_japan_current_headline_inflation': 2.00,
    'macro_japan_long_term_inflation': 1.50,
    'macro_japan_current_tbill': 0.75,
    'macro_japan_country_factor': 0.00,
    # EM Macro
    'macro_em_inflation_forecast': 3.80,
    'macro_em_rgdp_growth': 3.00,
    'macro_em_tbill_forecast': 5.50,
    'macro_em_population_growth': 1.00,
    'macro_em_productivity_growth': 2.50,
    'macro_em_my_ratio': 1.5,
    'macro_em_current_headline_inflation': 4.50,
    'macro_em_long_term_inflation': 3.50,
    'macro_em_current_tbill': 6.00,
    'macro_em_country_factor': 0.00,
    # Bonds Global
    'bonds_global_current_yield': 3.50,
    'bonds_global_duration': 7.0,
    'bonds_global_fair_term_premium': 1.50,
    'bonds_global_current_term_premium': 1.00,
    # Bonds HY
    'bonds_hy_current_yield': 7.50,
    'bonds_hy_duration': 4.0,
    'bonds_hy_credit_spread': 2.71,
    'bonds_hy_fair_credit_spread': 4.00,
    'bonds_hy_default_rate': 5.50,
    'bonds_hy_recovery_rate': 40.0,
    # Bonds EM
    'bonds_em_current_yield': 5.77,
    'bonds_em_duration': 5.5,
    'bonds_em_fair_term_premium': 2.00,
    'bonds_em_current_term_premium': 1.50,
    'bonds_em_default_rate': 2.80,
    'bonds_em_recovery_rate': 55.0,
    # Equity US
    'equity_us_dividend_yield': 1.13,
    'equity_us_current_caey': 2.48,
    'equity_us_fair_caey': 5.00,
    'equity_us_real_eps_growth': 1.80,
    'equity_us_regional_eps_growth': 1.60,
    # Equity Europe
    'equity_europe_dividend_yield': 3.00,
    'equity_europe_current_caey': 5.50,
    'equity_europe_fair_caey': 5.50,
    'equity_europe_real_eps_growth': 1.20,
    'equity_europe_regional_eps_growth': 1.60,
    # Equity Japan
    'equity_japan_dividend_yield': 2.20,
    'equity_japan_current_caey': 5.50,
    'equity_japan_fair_caey': 5.00,
    'equity_japan_real_eps_growth': 0.80,
    'equity_japan_regional_eps_growth': 1.60,
    # Equity EM
    'equity_em_dividend_yield': 3.00,
    'equity_em_current_caey': 6.50,
    'equity_em_fair_caey': 6.00,
    'equity_em_real_eps_growth': 3.00,
    'equity_em_regional_eps_growth': 2.80,
    # Absolute Return
    'absolute_return_trading_alpha': 1.00,
    'absolute_return_beta_market': 0.30,
    'absolute_return_beta_size': 0.10,
    'absolute_return_beta_value': 0.05,
    'absolute_return_beta_profitability': 0.05,
    'absolute_return_beta_investment': 0.05,
    'absolute_return_beta_momentum': 0.10,
}

def apply_scenario_to_session(scenario_data):
    """Apply a saved scenario's overrides to session state."""
    overrides = scenario_data.get('overrides', {})

    # Increment reset version to create fresh widget keys (clears all browser widget state)
    st.session_state['_reset_version'] = st.session_state.get('_reset_version', 0) + 1

    # Note: base_currency cannot be changed after widget renders
    # User should manually switch if needed

    # Apply macro overrides (using new versioned keys)
    if 'macro' in overrides:
        for region, region_overrides in overrides['macro'].items():
            for key, value in region_overrides.items():
                base_key = f"macro_{region}_{key}"
                session_key = widget_key(base_key)
                if key == 'my_ratio':
                    st.session_state[session_key] = value
                else:
                    st.session_state[session_key] = value * 100  # Convert back to percentage

    # Apply bond overrides
    for bond_type in ['bonds_global', 'bonds_hy', 'bonds_em']:
        if bond_type in overrides:
            for key, value in overrides[bond_type].items():
                base_key = f"{bond_type}_{key}"
                session_key = widget_key(base_key)
                if key == 'duration':
                    st.session_state[session_key] = value
                else:
                    st.session_state[session_key] = value * 100

    # Apply equity overrides
    for region in ['us', 'europe', 'japan', 'em']:
        equity_key = f"equity_{region}"
        if equity_key in overrides:
            for key, value in overrides[equity_key].items():
                base_key = f"{equity_key}_{key}"
                session_key = widget_key(base_key)
                st.session_state[session_key] = value * 100

    # Apply hedge fund overrides
    if 'absolute_return' in overrides:
        for key, value in overrides['absolute_return'].items():
            base_key = f"absolute_return_{key}"
            session_key = widget_key(base_key)
            if key == 'trading_alpha':
                st.session_state[session_key] = value * 100
            else:
                st.session_state[session_key] = value

def format_overrides_preview(overrides, base_currency=None):
    """Format overrides for display in preview panel."""
    if not overrides:
        return "No changes from defaults"
    
    lines = []
    
    # Macro overrides
    if 'macro' in overrides:
        region_names = {'us': 'US', 'eurozone': 'Europe', 'japan': 'Japan', 'em': 'EM'}
        for region, region_overrides in overrides['macro'].items():
            region_name = region_names.get(region, region)
            for key, value in region_overrides.items():
                display_key = key.replace('_', ' ').title()
                if key == 'my_ratio':
                    lines.append(f"- {region_name} {display_key}: {value:.2f}")
                else:
                    lines.append(f"- {region_name} {display_key}: {value*100:.2f}%")
    
    # Bond overrides
    bond_names = {'bonds_global': 'Bonds Global', 'bonds_hy': 'Bonds HY', 'bonds_em': 'Bonds EM'}
    for bond_type, display_name in bond_names.items():
        if bond_type in overrides:
            for key, value in overrides[bond_type].items():
                display_key = key.replace('_', ' ').title()
                if key == 'duration':
                    lines.append(f"- {display_name} {display_key}: {value:.1f} yrs")
                else:
                    lines.append(f"- {display_name} {display_key}: {value*100:.2f}%")
    
    # Equity overrides
    equity_names = {'equity_us': 'Equity US', 'equity_europe': 'Equity Europe', 
                    'equity_japan': 'Equity Japan', 'equity_em': 'Equity EM'}
    for equity_key, display_name in equity_names.items():
        if equity_key in overrides:
            for key, value in overrides[equity_key].items():
                display_key = key.replace('_', ' ').title()
                lines.append(f"- {display_name} {display_key}: {value*100:.2f}%")
    
    # Hedge fund overrides
    if 'absolute_return' in overrides:
        for key, value in overrides['absolute_return'].items():
            display_key = key.replace('_', ' ').title()
            if key == 'trading_alpha':
                lines.append(f"- Absolute Return {display_key}: {value*100:.2f}%")
            else:
                lines.append(f"- Absolute Return {display_key}: {value:.2f}")
    
    return "\n".join(lines) if lines else "No changes from defaults"

# Page configuration
st.set_page_config(
    page_title="Parkview CMA Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A5F;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1E3A5F;
    }
    .positive { color: #28a745; }
    .negative { color: #dc3545; }
    .section-header {
        font-size: 1.2rem;
        font-weight: bold;
        color: #1E3A5F;
        border-bottom: 2px solid #1E3A5F;
        padding-bottom: 0.5rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .formula-box {
        background-color: #e8f4f8;
        border: 1px solid #b8d4e3;
        border-radius: 0.5rem;
        padding: 1rem;
        font-family: 'Courier New', monospace;
        margin: 0.5rem 0;
    }
    .input-table {
        width: 100%;
        border-collapse: collapse;
    }
    .input-table td, .input-table th {
        padding: 0.5rem;
        text-align: left;
        border-bottom: 1px solid #ddd;
    }
    .override-badge {
        background-color: #ffc107;
        color: #000;
        padding: 0.1rem 0.4rem;
        border-radius: 0.25rem;
        font-size: 0.7rem;
        font-weight: bold;
    }
    .default-badge {
        background-color: #6c757d;
        color: #fff;
        padding: 0.1rem 0.4rem;
        border-radius: 0.25rem;
        font-size: 0.7rem;
    }
    .computed-badge {
        background-color: #17a2b8;
        color: #fff;
        padding: 0.1rem 0.4rem;
        border-radius: 0.25rem;
        font-size: 0.7rem;
    }
    .advanced-section {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 0.5rem;
        padding: 0.5rem;
        margin-top: 0.5rem;
    }
    .building-block {
        font-size: 0.85rem;
        color: #856404;
    }
</style>
""", unsafe_allow_html=True)

# FX formula documentation (shared across asset classes)
FX_FORMULA = {
    'formula': 'FX Return = 30% × (Home T-Bill - Foreign T-Bill) + 70% × (Home Inflation - Foreign Inflation)',
    'sub_formula': 'PPP-based FX forecast; positive means home currency depreciates, adding to foreign asset returns',
    'inputs': ['home_tbill', 'foreign_tbill', 'home_inflation', 'foreign_inflation']
}

# Model formulas and descriptions
MODEL_FORMULAS = {
    'liquidity': {
        'name': 'Liquidity (Cash/T-Bills)',
        'main_formula': 'E[Return] = E[T-Bill Rate]',
        'description': 'Cash return equals the expected T-Bill rate over the forecast horizon. Uses base currency T-Bill.',
        'components': {
            'tbill_rate': {
                'formula': 'E[T-Bill] = 30% × Current T-Bill + 70% × Long-Term T-Bill',
                'sub_formula': 'Long-Term T-Bill = max(-0.75%, Country Factor + RGDP Growth + Inflation)',
                'inputs': ['current_tbill', 'country_factor', 'rgdp_forecast', 'inflation_forecast']
            }
        }
    },
    'bonds_global': {
        'name': 'Bonds Global (Developed Government)',
        'main_formula': 'E[Return] = Yield + Roll Return + Valuation Return - Credit Losses + FX Return',
        'description': 'Government bond returns based on yield, roll-down, and term premium mean reversion. USD-hedged; FX adjustment applied when EUR base.',
        'components': {
            'yield': {
                'formula': 'Avg Yield = E[T-Bill] + Avg Term Premium',
                'sub_formula': 'Term Premium mean-reverts from current to fair value over time',
                'inputs': ['current_yield', 'duration', 'current_term_premium', 'fair_term_premium', 'tbill_forecast']
            },
            'roll_return': {
                'formula': 'Roll Return = (Term Premium / Maturity) × Duration',
                'sub_formula': 'Captures yield curve roll-down as bonds approach maturity',
                'inputs': ['duration', 'term_premium', 'maturity_years']
            },
            'valuation': {
                'formula': 'Valuation = -Duration × (ΔTerm Premium / Horizon)',
                'sub_formula': 'Term premium reverts toward fair value; rising yields = negative valuation',
                'inputs': ['duration', 'current_term_premium', 'fair_term_premium', 'mean_reversion_speed']
            },
            'credit_loss': {
                'formula': 'Credit Loss = 0% (Sovereign default-free)',
                'sub_formula': 'Developed market government bonds assumed risk-free',
                'inputs': []
            },
            'fx_return': FX_FORMULA
        }
    },
    'bonds_hy': {
        'name': 'Bonds High Yield',
        'main_formula': 'E[Return] = Yield + Roll Return + Valuation Return - Credit Losses + FX Return',
        'description': 'High yield bonds with credit spread and default loss components. USD-denominated; FX adjustment applied when EUR base.',
        'components': {
            'yield': {
                'formula': 'Avg Yield = E[T-Bill] + Avg Term Premium + Credit Spread',
                'sub_formula': 'Includes credit spread which also mean-reverts to fair value',
                'inputs': ['current_yield', 'duration', 'credit_spread', 'fair_credit_spread', 'tbill_forecast']
            },
            'roll_return': {
                'formula': 'Roll Return = (Term Premium / Maturity) × Duration',
                'sub_formula': 'Shorter duration than government bonds reduces roll return',
                'inputs': ['duration', 'term_premium']
            },
            'valuation': {
                'formula': 'Valuation = -Duration × (ΔTerm Premium + ΔCredit Spread) / Horizon',
                'sub_formula': 'Both term premium and credit spread mean reversion affect valuations',
                'inputs': ['duration', 'current_term_premium', 'fair_term_premium', 'credit_spread', 'fair_credit_spread']
            },
            'credit_loss': {
                'formula': 'Credit Loss = Default Rate × (1 - Recovery Rate)',
                'sub_formula': 'Annual expected loss from defaults, using historical default and recovery rates',
                'inputs': ['default_rate', 'recovery_rate']
            },
            'fx_return': FX_FORMULA
        }
    },
    'bonds_em': {
        'name': 'Bonds EM (Hard Currency)',
        'main_formula': 'E[Return] = Yield + Roll Return + Valuation Return - Credit Losses + FX Return',
        'description': 'Emerging market USD-denominated sovereign bonds. Uses US T-Bill and US inflation (not EM macro) since bonds are priced off the US Treasury curve. No FX adjustment for USD base; EUR/USD adjustment applied when EUR base.',
        'components': {
            'yield': {
                'formula': 'Avg Yield = E[US T-Bill] + Avg Term Premium + EM Credit Spread (~2%)',
                'sub_formula': 'USD-denominated; yield based on US T-Bill plus EM sovereign credit spread',
                'inputs': ['current_yield', 'duration', 'us_tbill_forecast', 'current_term_premium', 'fair_term_premium']
            },
            'roll_return': {
                'formula': 'Roll Return = (Term Premium / Maturity) × Duration',
                'sub_formula': 'Similar roll mechanics to other bond classes',
                'inputs': ['duration', 'term_premium']
            },
            'valuation': {
                'formula': 'Valuation = -Duration × (ΔTerm Premium / Horizon)',
                'sub_formula': 'Term premium mean reversion in EM markets',
                'inputs': ['duration', 'current_term_premium', 'fair_term_premium']
            },
            'credit_loss': {
                'formula': 'Credit Loss = Default Rate × (1 - Recovery Rate)',
                'sub_formula': 'EM hard currency sovereign default rate (2.8% historical)',
                'inputs': ['default_rate', 'recovery_rate']
            },
            'fx_return': FX_FORMULA
        }
    },
    'equity_us': {
        'name': 'Equity US',
        'main_formula': 'E[Real Return] = Dividend Yield + Real EPS Growth + Valuation Change + FX Return',
        'description': 'US equity returns based on dividends, earnings growth, and CAEY mean reversion. FX adjustment applied when EUR base.',
        'components': {
            'dividend_yield': {
                'formula': 'Dividend Yield = Current Trailing 12-Month Dividend Yield',
                'sub_formula': 'Taken as current market value, no mean reversion assumed',
                'inputs': ['dividend_yield']
            },
            'real_eps_growth': {
                'formula': 'EPS Growth = 50% × Country EPS + 50% × Regional (DM) EPS',
                'sub_formula': 'Blended growth capped at Global GDP growth; based on 50-year log-linear trend',
                'inputs': ['country_eps_growth', 'regional_eps_growth', 'global_gdp_cap']
            },
            'valuation_change': {
                'formula': 'Valuation = Avg[(Fair CAEY / Current CAEY)^(1/20) - 1] over 10 years',
                'sub_formula': 'CAEY (1/CAPE) reverts to fair value over 20 years; averaged over forecast horizon',
                'inputs': ['current_caey', 'fair_caey', 'reversion_years']
            },
            'fx_return': FX_FORMULA
        }
    },
    'equity_europe': {
        'name': 'Equity Europe',
        'main_formula': 'E[Real Return] = Dividend Yield + Real EPS Growth + Valuation Change + FX Return',
        'description': 'European equity returns using same methodology as US. No FX adjustment when EUR base (home market); FX adjustment applied when USD base.',
        'components': {
            'dividend_yield': {
                'formula': 'Dividend Yield = Current Trailing 12-Month Dividend Yield',
                'sub_formula': 'European markets typically have higher dividend yields than US',
                'inputs': ['dividend_yield']
            },
            'real_eps_growth': {
                'formula': 'EPS Growth = 50% × Country EPS + 50% × Regional (DM) EPS',
                'sub_formula': 'Blended with Developed Markets regional average',
                'inputs': ['country_eps_growth', 'regional_eps_growth', 'global_gdp_cap']
            },
            'valuation_change': {
                'formula': 'Valuation = Avg[(Fair CAEY / Current CAEY)^(1/20) - 1] over 10 years',
                'sub_formula': 'CAEY mean reversion; Europe often closer to fair value than US',
                'inputs': ['current_caey', 'fair_caey', 'reversion_years']
            },
            'fx_return': FX_FORMULA
        }
    },
    'equity_japan': {
        'name': 'Equity Japan',
        'main_formula': 'E[Real Return] = Dividend Yield + Real EPS Growth + Valuation Change + FX Return',
        'description': 'Japanese equity returns with Japan-specific growth assumptions. FX adjustment applies for both USD and EUR base.',
        'components': {
            'dividend_yield': {
                'formula': 'Dividend Yield = Current Trailing 12-Month Dividend Yield',
                'sub_formula': 'Japan dividends have been increasing as payout ratios rise',
                'inputs': ['dividend_yield']
            },
            'real_eps_growth': {
                'formula': 'EPS Growth = 50% × Country EPS + 50% × Regional (DM) EPS',
                'sub_formula': 'Japan country growth lower due to demographics; blended with DM average',
                'inputs': ['country_eps_growth', 'regional_eps_growth', 'global_gdp_cap']
            },
            'valuation_change': {
                'formula': 'Valuation = Avg[(Fair CAEY / Current CAEY)^(1/20) - 1] over 10 years',
                'sub_formula': 'CAEY mean reversion over 20 years',
                'inputs': ['current_caey', 'fair_caey', 'reversion_years']
            },
            'fx_return': FX_FORMULA
        }
    },
    'equity_em': {
        'name': 'Equity EM',
        'main_formula': 'E[Real Return] = Dividend Yield + Real EPS Growth + Valuation Change + FX Return',
        'description': 'Emerging market equity returns with EM-specific assumptions. FX adjustment applies for both USD and EUR base.',
        'components': {
            'dividend_yield': {
                'formula': 'Dividend Yield = Current Trailing 12-Month Dividend Yield',
                'sub_formula': 'EM dividend yields vary widely across countries',
                'inputs': ['dividend_yield']
            },
            'real_eps_growth': {
                'formula': 'EPS Growth = 50% × Country EPS + 50% × Regional (EM) EPS',
                'sub_formula': 'Higher growth potential but capped at Global GDP; uses 5-year minimum data window',
                'inputs': ['country_eps_growth', 'regional_eps_growth', 'global_gdp_cap']
            },
            'valuation_change': {
                'formula': 'Valuation = Avg[(Fair CAEY / Current CAEY)^(1/20) - 1] over 10 years',
                'sub_formula': 'EM CAEY averaged with EM regional group for stability',
                'inputs': ['current_caey', 'fair_caey', 'reversion_years']
            },
            'fx_return': FX_FORMULA
        }
    },
    'absolute_return': {
        'name': 'Absolute Return (Hedge Funds)',
        'main_formula': 'E[Return] = E[T-Bill] + Σ(βᵢ × Factor Premiumᵢ) + Trading Alpha',
        'description': 'Factor-based model using Fama-French factors plus manager alpha.',
        'components': {
            'tbill': {
                'formula': 'T-Bill Component = E[T-Bill Rate]',
                'sub_formula': 'Risk-free rate foundation for all returns',
                'inputs': ['tbill_forecast']
            },
            'factor_return': {
                'formula': 'Factor Return = Σ(βᵢ × E[Factor Premiumᵢ])',
                'sub_formula': 'Factors: Market, Size (SMB), Value (HML), Profitability (RMW), Investment (CMA), Momentum (UMD)',
                'inputs': ['beta_market', 'beta_size', 'beta_value', 'beta_profitability', 'beta_investment', 'beta_momentum',
                          'premium_market', 'premium_size', 'premium_value', 'premium_profitability', 'premium_investment', 'premium_momentum']
            },
            'trading_alpha': {
                'formula': 'Trading Alpha = 50% × Historical Alpha',
                'sub_formula': 'Manager skill beyond factor exposures; discounted from historical due to alpha decay',
                'inputs': ['trading_alpha']
            }
        }
    }
}

# Header
st.markdown('<p class="main-header">Parkview CMA Tool</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Adjust assumptions to see how expected returns change across asset classes. See the <strong>Methodology</strong> page in the sidebar for calculation details.</p>', unsafe_allow_html=True)

# Initialize session state for overrides
if 'overrides' not in st.session_state:
    st.session_state.overrides = {}

def format_pct(value, decimals=2):
    """Format as percentage"""
    return f"{value * 100:.{decimals}f}%"

def get_source_badge(source):
    """Return HTML badge for source type"""
    if source == 'override':
        return '<span class="override-badge">OVERRIDE</span>'
    elif source == 'computed':
        return '<span class="computed-badge">COMPUTED</span>'
    else:
        return '<span class="default-badge">DEFAULT</span>'

def build_overrides():
    """Build override dictionary from session state by comparing to defaults."""
    overrides = {}

    def is_override(base_key):
        """Check if value differs from default (with tolerance for float comparison)."""
        # Use versioned widget key for session state lookup
        wkey = widget_key(base_key)
        if wkey not in st.session_state:
            return False, None
        val = st.session_state[wkey]
        default = INPUT_DEFAULTS.get(base_key)
        
        # Handle None or NaN
        if val is None or (isinstance(val, float) and val != val):
            return False, None
        if default is None:
            return True, val  # No default means any value is an override
        
        # Compare with tolerance for floating point
        if abs(val - default) > 0.001:
            return True, val
        return False, None

    # Macro overrides (both basic and advanced)
    for region in ['us', 'eurozone', 'japan', 'em']:
        region_overrides = {}

        # Basic macro inputs
        for key in ['inflation_forecast', 'rgdp_growth', 'tbill_forecast']:
            session_key = f"macro_{region}_{key}"
            is_changed, val = is_override(session_key)
            if is_changed:
                region_overrides[key] = val / 100

        # Advanced macro inputs (building blocks)
        advanced_keys = [
            'population_growth', 'productivity_growth', 'my_ratio',
            'current_headline_inflation', 'long_term_inflation',
            'current_tbill', 'country_factor'
        ]
        for key in advanced_keys:
            session_key = f"macro_{region}_{key}"
            is_changed, val = is_override(session_key)
            if is_changed:
                if key == 'my_ratio':
                    region_overrides[key] = val  # Not a percentage
                else:
                    region_overrides[key] = val / 100

        if region_overrides:
            if 'macro' not in overrides:
                overrides['macro'] = {}
            overrides['macro'][region] = region_overrides

    # Bond overrides
    for bond_type, bond_key in [('bonds_global', 'bonds_global'), ('bonds_hy', 'bonds_hy'), ('bonds_em', 'bonds_em')]:
        bond_overrides = {}
        for key in ['current_yield', 'duration', 'default_rate', 'recovery_rate', 'credit_spread',
                    'fair_term_premium', 'fair_credit_spread', 'current_term_premium']:
            session_key = f"{bond_key}_{key}"
            is_changed, val = is_override(session_key)
            if is_changed:
                if key in ['duration']:
                    bond_overrides[key] = val
                elif key in ['recovery_rate']:
                    bond_overrides[key] = val / 100  # recovery_rate is stored as % in defaults
                else:
                    bond_overrides[key] = val / 100
        if bond_overrides:
            overrides[bond_key] = bond_overrides

    # Equity overrides
    for region in ['us', 'europe', 'japan', 'em']:
        equity_key = f"equity_{region}"
        equity_overrides = {}
        for key in ['dividend_yield', 'real_eps_growth', 'current_caey', 'fair_caey', 'regional_eps_growth']:
            session_key = f"{equity_key}_{key}"
            is_changed, val = is_override(session_key)
            if is_changed:
                equity_overrides[key] = val / 100
        if equity_overrides:
            overrides[equity_key] = equity_overrides

    # Hedge fund overrides
    hf_overrides = {}
    for key in ['trading_alpha', 'beta_market', 'beta_value', 'beta_momentum', 'beta_size', 'beta_profitability', 'beta_investment']:
        session_key = f"absolute_return_{key}"
        is_changed, val = is_override(session_key)
        if is_changed:
            if key == 'trading_alpha':
                hf_overrides[key] = val / 100
            else:
                hf_overrides[key] = val
    if hf_overrides:
        overrides['absolute_return'] = hf_overrides

    return overrides

# Sidebar for inputs
with st.sidebar:
    # Show any pending toast messages (deferred from previous run)
    if '_pending_toast' in st.session_state:
        msg, icon = st.session_state.pop('_pending_toast')
        st.toast(msg, icon=icon)

    # User info and logout
    st.markdown(f"""
    <div style="background-color: #e8f4f8; padding: 0.5rem 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
        <span style="color: #1E3A5F; font-size: 0.9rem;">Logged in as:</span><br/>
        <strong style="color: #1E3A5F;">{user['email']}</strong>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚪 Logout", use_container_width=True):
        logout()
        st.rerun()

    st.divider()

    st.header("Settings")

    # Base currency toggle
    base_currency = st.radio(
        "Base Currency",
        options=["USD", "EUR"],
        horizontal=True,
        help="Select the currency perspective for all returns. EUR base applies FX adjustments using PPP methodology.",
        key="base_currency_toggle"
    )

    st.divider()

    # ==========================================================================
    # Scenario Management Section
    # ==========================================================================
    st.header("📁 Scenarios")

    # Load available scenarios for current user
    saved_scenarios = load_scenarios(user_id)
    scenario_names = list(saved_scenarios.keys())
    
    # Track which scenario was last loaded to hide its preview
    last_loaded = st.session_state.get('_last_loaded_scenario')

    # Scenario selector
    scenario_options = ["-- New Scenario --"] + scenario_names
    selected_scenario = st.selectbox(
        "Select Scenario",
        options=scenario_options,
        key="selected_scenario_dropdown",
        help="Choose a saved scenario to preview or load"
    )

    # Clear the "last loaded" marker if user selects a different scenario
    if selected_scenario != last_loaded and last_loaded is not None:
        del st.session_state['_last_loaded_scenario']
        last_loaded = None
    
    # Show preview if a saved scenario is selected
    # Show preview only if a scenario is selected AND it wasn't just loaded
    show_preview = (selected_scenario != "-- New Scenario --"
                    and selected_scenario in saved_scenarios
                    and selected_scenario != last_loaded)

    if show_preview:
        scenario_data = saved_scenarios[selected_scenario]

        with st.expander("📋 Scenario Preview", expanded=True):
            # Metadata
            timestamp = scenario_data.get('timestamp', 'Unknown')
            if timestamp != 'Unknown':
                try:
                    dt = datetime.fromisoformat(timestamp)
                    timestamp = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            st.markdown(f"**Saved:** {timestamp}")
            st.markdown(f"**Base Currency:** {scenario_data.get('base_currency', 'USD')}")
            
            st.markdown("---")
            st.markdown("**Changes from defaults:**")
            preview_text = format_overrides_preview(scenario_data.get('overrides', {}))
            st.markdown(preview_text)
        
        # Load and Delete buttons
        col_load, col_delete = st.columns(2)
        with col_load:
            if st.button("✅ Load Scenario", use_container_width=True):
                apply_scenario_to_session(scenario_data)
                # Deferred toast (shown after rerun)
                st.session_state['_pending_toast'] = (f"✅ Loaded '{selected_scenario}'", "✅")
                # Mark this scenario as loaded (hides its preview until user selects different)
                st.session_state['_last_loaded_scenario'] = selected_scenario
                st.rerun()
        with col_delete:
            if st.button("🗑️ Delete", use_container_width=True):
                if delete_scenario(user_id, selected_scenario):
                    st.session_state['_pending_toast'] = (f"🗑️ Deleted '{selected_scenario}'", "🗑️")
                    st.rerun()
                else:
                    st.toast("❌ Failed to delete scenario", icon="❌")
    
    st.markdown("---")

    # Quick Scenario Templates
    st.markdown("**📋 Quick Templates:**")
    st.caption("Load a preset scenario as a starting point")

    # Define templates
    SCENARIO_TEMPLATES = {
        "-- Select Template --": None,
        "🟢 Bull Market": {
            'description': 'Higher growth (+0.5%), lower inflation (-0.3%)',
            'overrides': {
                'macro': {
                    'us': {'rgdp_growth': 0.017, 'inflation_forecast': 0.0199},
                    'eurozone': {'rgdp_growth': 0.013, 'inflation_forecast': 0.0176},
                    'japan': {'rgdp_growth': 0.008, 'inflation_forecast': 0.0135},
                    'em': {'rgdp_growth': 0.035, 'inflation_forecast': 0.035}
                }
            }
        },
        "🔴 Bear Market": {
            'description': 'Lower growth (-1%), higher credit spreads',
            'overrides': {
                'macro': {
                    'us': {'rgdp_growth': 0.002},
                    'eurozone': {'rgdp_growth': -0.002},
                    'japan': {'rgdp_growth': -0.007},
                    'em': {'rgdp_growth': 0.02}
                },
                'bonds_hy': {'credit_spread': 0.05, 'default_rate': 0.07},
                'bonds_em': {'default_rate': 0.04}
            }
        },
        "🟠 Stagflation": {
            'description': 'High inflation (+2%), low growth (-0.5%)',
            'overrides': {
                'macro': {
                    'us': {'inflation_forecast': 0.0429, 'rgdp_growth': 0.007},
                    'eurozone': {'inflation_forecast': 0.0406, 'rgdp_growth': 0.003},
                    'japan': {'inflation_forecast': 0.0365, 'rgdp_growth': -0.002},
                    'em': {'inflation_forecast': 0.058, 'rgdp_growth': 0.025}
                }
            }
        },
        "📈 Rising Rates": {
            'description': 'Higher T-Bill (+1.5%), duration impact',
            'overrides': {
                'macro': {
                    'us': {'tbill_forecast': 0.0529},
                    'eurozone': {'tbill_forecast': 0.042},
                    'japan': {'tbill_forecast': 0.025},
                    'em': {'tbill_forecast': 0.07}
                }
            }
        },
        "⚖️ RA Base Case": {
            'description': 'All default values',
            'overrides': {}
        }
    }

    selected_template = st.selectbox(
        "Load Template",
        options=list(SCENARIO_TEMPLATES.keys()),
        key="template_selector",
        label_visibility="collapsed"
    )

    if selected_template != "-- Select Template --" and SCENARIO_TEMPLATES[selected_template]:
        template_data = SCENARIO_TEMPLATES[selected_template]
        st.caption(f"_{template_data['description']}_")

        if st.button("📥 Load Template", use_container_width=True):
            # Apply template overrides
            template_overrides = template_data.get('overrides', {})
            apply_scenario_to_session({'overrides': template_overrides})
            st.session_state['_pending_toast'] = (f"✅ Loaded template: {selected_template}", "📋")
            # Reset template selector
            st.rerun()

    st.markdown("---")

    # Save current scenario
    st.markdown("**Save Current Settings:**")
    new_scenario_name = st.text_input(
        "Scenario Name",
        placeholder="e.g., Bull Case, Bear Case, Base Case",
        key="new_scenario_name",
        label_visibility="collapsed"
    )
    
    col_save, col_reset = st.columns(2)
    with col_save:
        if st.button("💾 Save Scenario", use_container_width=True):
            if new_scenario_name and new_scenario_name.strip():
                # Build overrides directly from current session state
                current_overrides = build_overrides()
                if save_scenario(user_id, new_scenario_name.strip(), current_overrides, base_currency):
                    # Deferred toast (shown after rerun)
                    if current_overrides:
                        st.session_state['_pending_toast'] = (f"✅ Saved '{new_scenario_name}' with {len(current_overrides)} override group(s)", "✅")
                    else:
                        st.session_state['_pending_toast'] = (f"⚠️ Saved '{new_scenario_name}' (no changes from defaults)", "⚠️")
                    st.rerun()  # Refresh to show new scenario in dropdown
                else:
                    st.toast(f"❌ Failed to save", icon="❌")
            else:
                st.error("Please enter a scenario name")
    
    with col_reset:
        if st.button("🔄 Reset All", use_container_width=True):
            # Increment reset version to create fresh widget keys (clears all browser widget state)
            st.session_state['_reset_version'] = st.session_state.get('_reset_version', 0) + 1
            # Also clear scenario-related keys
            if '_last_loaded_scenario' in st.session_state:
                del st.session_state['_last_loaded_scenario']
            st.session_state['_pending_toast'] = ("✅ All inputs reset to defaults", "🔄")
            st.rerun()

    st.divider()

    st.header("Input Assumptions")

    # Mode toggle
    advanced_mode = st.toggle("Advanced Mode", value=False,
                              help="Show all building block inputs (population growth, productivity, etc.)")

    st.divider()

    # Macro Assumptions
    with st.expander("🌍 Macro Assumptions", expanded=True):
        tab_us, tab_eu, tab_jp, tab_em = st.tabs(["US", "Europe", "Japan", "EM"])

        with tab_us:
            st.markdown("**📊 Direct Forecast Overrides:**")
            st.caption("Override the 10-year forecast directly (bypasses building block calculations)")
            st.number_input("E[Inflation] — 10yr Avg (%)", min_value=-2.0, max_value=15.0, 
                           value=INPUT_DEFAULTS['macro_us_inflation_forecast'],
                           step=0.1, key=widget_key("macro_us_inflation_forecast"),
                           help="Default: 2.29% | Directly override the 10-year inflation forecast")
            st.number_input("E[Real GDP Growth] — 10yr Avg (%)", min_value=-5.0, max_value=10.0, 
                           value=INPUT_DEFAULTS['macro_us_rgdp_growth'],
                           step=0.1, key=widget_key("macro_us_rgdp_growth"),
                           help="Default: 1.20% | Directly override the 10-year GDP forecast")
            st.number_input("E[T-Bill Rate] — 10yr Avg (%)", min_value=-1.0, max_value=15.0, 
                           value=INPUT_DEFAULTS['macro_us_tbill_forecast'],
                           step=0.1, key=widget_key("macro_us_tbill_forecast"),
                           help="Default: 3.79% | Directly override the 10-year T-Bill forecast")

            if advanced_mode:
                st.markdown("---")
                st.markdown("**🔧 Building Blocks (GDP Model):**")
                st.caption("GDP = Output-per-Capita Growth + Population Growth")
                st.number_input("Population Growth (%)", min_value=-3.0, max_value=5.0, 
                               value=INPUT_DEFAULTS['macro_us_population_growth'],
                               step=0.1, key=widget_key("macro_us_population_growth"),
                               help="Default: 0.40% | UN Population Database forecast")
                st.number_input("Productivity Growth (%)", min_value=-2.0, max_value=5.0, 
                               value=INPUT_DEFAULTS['macro_us_productivity_growth'],
                               step=0.1, key=widget_key("macro_us_productivity_growth"),
                               help="Default: 1.20% | EWMA of historical output-per-capita (5yr half-life)")
                st.number_input("MY Ratio", min_value=0.5, max_value=4.0, 
                               value=INPUT_DEFAULTS['macro_us_my_ratio'],
                               step=0.1, key=widget_key("macro_us_my_ratio"),
                               help="Default: 2.1 | Middle/Young population ratio (affects demographic drag)")

                st.markdown("**🔧 Building Blocks (Inflation Model):**")
                st.caption("E[Inflation] = 30% × Current Headline + 70% × Long-Term Target")
                st.number_input("Current Headline Inflation — Today (%)", min_value=-2.0, max_value=15.0, 
                               value=INPUT_DEFAULTS['macro_us_current_headline_inflation'],
                               step=0.1, key=widget_key("macro_us_current_headline_inflation"),
                               help="Default: 2.50% | Latest YoY CPI reading")
                st.number_input("Long-Term Inflation Target (%)", min_value=0.0, max_value=10.0, 
                               value=INPUT_DEFAULTS['macro_us_long_term_inflation'],
                               step=0.1, key=widget_key("macro_us_long_term_inflation"),
                               help="Default: 2.20% | EWMA of core inflation (5yr half-life)")

                st.markdown("**🔧 Building Blocks (T-Bill Model):**")
                st.caption("E[T-Bill] = 30% × Current T-Bill + 70% × Long-Term Equilibrium")
                st.number_input("Current T-Bill Rate — Today (%)", min_value=-1.0, max_value=15.0, 
                               value=INPUT_DEFAULTS['macro_us_current_tbill'],
                               step=0.1, key=widget_key("macro_us_current_tbill"),
                               help="Default: 3.67% | Today's 3-month UST yield")
                st.number_input("Country Factor (%)", min_value=-2.0, max_value=2.0, 
                               value=INPUT_DEFAULTS['macro_us_country_factor'],
                               step=0.1, key=widget_key("macro_us_country_factor"),
                               help="Default: 0.00% | Liquidity premium adjustment")

        with tab_eu:
            st.markdown("**📊 Direct Forecast Overrides:**")
            st.caption("Override the 10-year forecast directly")
            st.number_input("E[Inflation] — 10yr Avg (%)", min_value=-2.0, max_value=15.0, 
                           value=INPUT_DEFAULTS['macro_eurozone_inflation_forecast'],
                           step=0.1, key=widget_key("macro_eurozone_inflation_forecast"),
                           help="Default: 2.06%")
            st.number_input("E[Real GDP Growth] — 10yr Avg (%)", min_value=-5.0, max_value=10.0, 
                           value=INPUT_DEFAULTS['macro_eurozone_rgdp_growth'],
                           step=0.1, key=widget_key("macro_eurozone_rgdp_growth"),
                           help="Default: 0.80%")

            if advanced_mode:
                st.markdown("---")
                st.markdown("**🔧 Building Blocks (GDP):**")
                st.number_input("Population Growth (%)", min_value=-3.0, max_value=5.0, 
                               value=INPUT_DEFAULTS['macro_eurozone_population_growth'],
                               step=0.1, key=widget_key("macro_eurozone_population_growth"),
                               help="Default: 0.10%")
                st.number_input("Productivity Growth (%)", min_value=-2.0, max_value=5.0, 
                               value=INPUT_DEFAULTS['macro_eurozone_productivity_growth'],
                               step=0.1, key=widget_key("macro_eurozone_productivity_growth"),
                               help="Default: 1.00%")
                st.number_input("MY Ratio", min_value=0.5, max_value=4.0, 
                               value=INPUT_DEFAULTS['macro_eurozone_my_ratio'],
                               step=0.1, key=widget_key("macro_eurozone_my_ratio"),
                               help="Default: 2.3")

                st.markdown("**🔧 Building Blocks (Inflation):**")
                st.number_input("Current Headline Inflation (%)", min_value=-2.0, max_value=15.0, 
                               value=INPUT_DEFAULTS['macro_eurozone_current_headline_inflation'],
                               step=0.1, key=widget_key("macro_eurozone_current_headline_inflation"),
                               help="Default: 2.20%")
                st.number_input("Long-Term Inflation Target (%)", min_value=0.0, max_value=10.0, 
                               value=INPUT_DEFAULTS['macro_eurozone_long_term_inflation'],
                               step=0.1, key=widget_key("macro_eurozone_long_term_inflation"),
                               help="Default: 2.00% (ECB target)")

        with tab_jp:
            st.markdown("**📊 Direct Forecast Overrides:**")
            st.caption("Override the 10-year forecast directly")
            st.number_input("E[Inflation] — 10yr Avg (%)", min_value=-2.0, max_value=15.0, value=None,
                           step=0.1, key=widget_key("macro_japan_inflation_forecast"),
                           placeholder="1.65", help="Default: 1.65%")
            st.number_input("E[Real GDP Growth] — 10yr Avg (%)", min_value=-5.0, max_value=10.0, value=None,
                           step=0.1, key=widget_key("macro_japan_rgdp_growth"),
                           placeholder="-0.46", help="Default: -0.46%")

            if advanced_mode:
                st.markdown("---")
                st.markdown("**🔧 Building Blocks (GDP):**")
                st.number_input("Population Growth (%)", min_value=-3.0, max_value=5.0, value=None,
                               step=0.1, key=widget_key("macro_japan_population_growth"),
                               placeholder="-0.50", help="Default: -0.50% (declining population)")
                st.number_input("Productivity Growth (%)", min_value=-2.0, max_value=5.0, value=None,
                               step=0.1, key=widget_key("macro_japan_productivity_growth"),
                               placeholder="0.80", help="Default: 0.80%")
                st.number_input("MY Ratio", min_value=0.5, max_value=4.0, value=None,
                               step=0.1, key=widget_key("macro_japan_my_ratio"),
                               placeholder="2.5", help="Default: 2.5 (aging population)")

                st.markdown("**🔧 Building Blocks (Inflation):**")
                st.number_input("Current Headline Inflation (%)", min_value=-2.0, max_value=15.0, value=None,
                               step=0.1, key=widget_key("macro_japan_current_headline_inflation"),
                               placeholder="2.00", help="Default: 2.00%")
                st.number_input("Long-Term Inflation Target (%)", min_value=0.0, max_value=10.0, value=None,
                               step=0.1, key=widget_key("macro_japan_long_term_inflation"),
                               placeholder="1.50", help="Default: 1.50%")

        with tab_em:
            st.markdown("**📊 Direct Forecast Overrides:**")
            st.caption("Override the 10-year forecast directly")
            st.number_input("E[Inflation] — 10yr Avg (%)", min_value=-2.0, max_value=15.0, value=None,
                           step=0.1, key=widget_key("macro_em_inflation_forecast"),
                           placeholder="3.80", help="Default: 3.80%")
            st.number_input("E[Real GDP Growth] — 10yr Avg (%)", min_value=-5.0, max_value=10.0, value=None,
                           step=0.1, key=widget_key("macro_em_rgdp_growth"),
                           placeholder="3.46", help="Default: 3.46%")

            if advanced_mode:
                st.markdown("---")
                st.markdown("**🔧 Building Blocks (GDP):**")
                st.number_input("Population Growth (%)", min_value=-3.0, max_value=5.0, value=None,
                               step=0.1, key=widget_key("macro_em_population_growth"),
                               placeholder="1.00", help="Default: 1.00%")
                st.number_input("Productivity Growth (%)", min_value=-2.0, max_value=5.0, value=None,
                               step=0.1, key=widget_key("macro_em_productivity_growth"),
                               placeholder="2.50", help="Default: 2.50%")
                st.number_input("MY Ratio", min_value=0.5, max_value=4.0, value=None,
                               step=0.1, key=widget_key("macro_em_my_ratio"),
                               placeholder="1.5", help="Default: 1.5 (younger population)")

                st.markdown("**🔧 Building Blocks (Inflation):**")
                st.caption("EM uses 2-year half-life for EWMA")
                st.number_input("Current Headline Inflation (%)", min_value=-2.0, max_value=15.0, value=None,
                               step=0.1, key=widget_key("macro_em_current_headline_inflation"),
                               placeholder="4.50", help="Default: 4.50%")
                st.number_input("Long-Term Inflation Target (%)", min_value=0.0, max_value=10.0, value=None,
                               step=0.1, key=widget_key("macro_em_long_term_inflation"),
                               placeholder="3.50", help="Default: 3.50%")

    # Bond Assumptions
    with st.expander("🏦 Bond Assumptions", expanded=False):
        tab_gov, tab_hy, tab_emb = st.tabs(["Global Gov", "High Yield", "EM Hard"])

        with tab_gov:
            st.markdown("**Primary Inputs:**")
            st.number_input("Current Yield (%)", min_value=0.0, max_value=15.0, value=None,
                           step=0.1, key=widget_key("bonds_global_current_yield"),
                           placeholder="3.50", help="Default: 3.50% | Yield to maturity of bond index")
            st.number_input("Duration (years)", min_value=0.0, max_value=30.0, value=None,
                           step=0.5, key=widget_key("bonds_global_duration"),
                           placeholder="7.0", help="Default: 7.0 years | Modified duration")

            if advanced_mode:
                st.markdown("---")
                st.markdown("**🔧 Building Blocks:**")
                st.number_input("Current Term Premium (%)", min_value=-2.0, max_value=5.0, value=None,
                               step=0.1, key=widget_key("bonds_global_current_term_premium"),
                               placeholder="1.00", help="Default: 1.00% | Current yield - T-Bill")
                st.number_input("Fair Term Premium (%)", min_value=-1.0, max_value=5.0, value=None,
                               step=0.1, key=widget_key("bonds_global_fair_term_premium"),
                               placeholder="1.50", help="Default: 1.50% | EWMA 20yr half-life, 50yr window")

        with tab_hy:
            st.markdown("**Primary Inputs:**")
            st.number_input("Current Yield (%)", min_value=0.0, max_value=20.0, value=None,
                           step=0.1, key=widget_key("bonds_hy_current_yield"),
                           placeholder="7.50", help="Default: 7.50%")
            st.number_input("Duration (years)", min_value=0.0, max_value=15.0, value=None,
                           step=0.5, key=widget_key("bonds_hy_duration"),
                           placeholder="4.0", help="Default: 4.0 years")
            st.number_input("Default Rate (%)", min_value=0.0, max_value=20.0, value=None,
                           step=0.1, key=widget_key("bonds_hy_default_rate"),
                           placeholder="5.50", help="Default: 5.50% | Annual default probability")
            st.number_input("Recovery Rate (%)", min_value=0.0, max_value=100.0, value=None,
                           step=1.0, key=widget_key("bonds_hy_recovery_rate"),
                           placeholder="40.0", help="Default: 40% | Recovery on default")

            if advanced_mode:
                st.markdown("---")
                st.markdown("**🔧 Building Blocks:**")
                st.number_input("Credit Spread (%)", min_value=0.0, max_value=20.0, value=None,
                               step=0.1, key=widget_key("bonds_hy_credit_spread"),
                               placeholder="2.71", help="Default: 2.71% (ICE BofA HY OAS) | Spread vs duration-matched Treasury")
                st.number_input("Fair Credit Spread (%)", min_value=0.0, max_value=20.0, value=None,
                               step=0.1, key=widget_key("bonds_hy_fair_credit_spread"),
                               placeholder="4.00", help="Default: 4.00% | EWMA 20yr half-life")
                st.number_input("Current Term Premium (%)", min_value=-2.0, max_value=5.0, value=None,
                               step=0.1, key=widget_key("bonds_hy_current_term_premium"),
                               placeholder="1.00", help="Default: 1.00%")
                st.number_input("Fair Term Premium (%)", min_value=-1.0, max_value=5.0, value=None,
                               step=0.1, key=widget_key("bonds_hy_fair_term_premium"),
                               placeholder="1.50", help="Default: 1.50%")

        with tab_emb:
            st.markdown("**Primary Inputs:**")
            st.number_input("Current Yield (%)", min_value=0.0, max_value=20.0, value=None,
                           step=0.1, key=widget_key("bonds_em_current_yield"),
                           placeholder="5.77", help="Default: 5.77% (BBG EM USD Aggregate Index)")
            st.number_input("Duration (years)", min_value=0.0, max_value=15.0, value=None,
                           step=0.5, key=widget_key("bonds_em_duration"),
                           placeholder="5.5", help="Default: 5.5 years")
            st.number_input("Default Rate (%)", min_value=0.0, max_value=10.0, value=None,
                           step=0.1, key=widget_key("bonds_em_default_rate"),
                           placeholder="2.80", help="Default: 2.80% | EM hard currency sovereign default rate")
            st.number_input("Recovery Rate (%)", min_value=0.0, max_value=100.0, value=None,
                           step=1.0, key=widget_key("bonds_em_recovery_rate"),
                           placeholder="55.0", help="Default: 55% | EM sovereign recovery rate")

            if advanced_mode:
                st.markdown("---")
                st.markdown("**🔧 Building Blocks:**")
                st.number_input("Current Term Premium (%)", min_value=-2.0, max_value=5.0, value=None,
                               step=0.1, key=widget_key("bonds_em_current_term_premium"),
                               placeholder="1.50", help="Default: 1.50%")
                st.number_input("Fair Term Premium (%)", min_value=-1.0, max_value=5.0, value=None,
                               step=0.1, key=widget_key("bonds_em_fair_term_premium"),
                               placeholder="2.00", help="Default: 2.00%")

    # Equity Assumptions
    with st.expander("📈 Equity Assumptions", expanded=False):
        tab_eq_us, tab_eq_eu, tab_eq_jp, tab_eq_em = st.tabs(["US", "Europe", "Japan", "EM"])

        with tab_eq_us:
            st.markdown("**Primary Inputs:**")
            st.number_input("Dividend Yield (%)", min_value=0.0, max_value=10.0, value=None,
                           step=0.1, key=widget_key("equity_us_dividend_yield"),
                           placeholder="1.13", help="Default: 1.13% (S&P 500 TTM) | Trailing 12-month dividend yield")
            st.number_input("Current CAEY (%)", min_value=1.0, max_value=15.0, value=None,
                           step=0.1, key=widget_key("equity_us_current_caey"),
                           placeholder="2.48", help="Default: 2.48% (CAPE ~40) | 1/CAPE")
            st.number_input("Fair CAEY (%)", min_value=1.0, max_value=15.0, value=None,
                           step=0.1, key=widget_key("equity_us_fair_caey"),
                           placeholder="5.00", help="Default: 5.00% (CAPE ~20) | EWMA 20yr half-life")

            if advanced_mode:
                st.markdown("---")
                st.markdown("**🔧 Building Blocks (EPS Growth):**")
                st.caption("Final EPS = 50% Country + 50% Regional, capped at Global GDP")
                st.number_input("Country EPS Growth (%)", min_value=-5.0, max_value=10.0, value=None,
                               step=0.1, key=widget_key("equity_us_real_eps_growth"),
                               placeholder="1.80", help="Default: 1.80% | 50-year log-linear trend")
                st.number_input("Regional (DM) EPS Growth (%)", min_value=-5.0, max_value=10.0, value=None,
                               step=0.1, key=widget_key("equity_us_regional_eps_growth"),
                               placeholder="1.60", help="Default: 1.60% | DM average")

        with tab_eq_eu:
            st.markdown("**Primary Inputs:**")
            st.number_input("Dividend Yield (%)", min_value=0.0, max_value=10.0, value=None,
                           step=0.1, key=widget_key("equity_europe_dividend_yield"),
                           placeholder="3.00", help="Default: 3.00%")
            st.number_input("Current CAEY (%)", min_value=1.0, max_value=15.0, value=None,
                           step=0.1, key=widget_key("equity_europe_current_caey"),
                           placeholder="5.50", help="Default: 5.50%")
            st.number_input("Fair CAEY (%)", min_value=1.0, max_value=15.0, value=None,
                           step=0.1, key=widget_key("equity_europe_fair_caey"),
                           placeholder="5.50", help="Default: 5.50%")

            if advanced_mode:
                st.markdown("---")
                st.markdown("**🔧 Building Blocks (EPS Growth):**")
                st.number_input("Country EPS Growth (%)", min_value=-5.0, max_value=10.0, value=None,
                               step=0.1, key=widget_key("equity_europe_real_eps_growth"),
                               placeholder="1.20", help="Default: 1.20%")
                st.number_input("Regional (DM) EPS Growth (%)", min_value=-5.0, max_value=10.0, value=None,
                               step=0.1, key=widget_key("equity_europe_regional_eps_growth"),
                               placeholder="1.60", help="Default: 1.60%")

        with tab_eq_jp:
            st.markdown("**Primary Inputs:**")
            st.number_input("Dividend Yield (%)", min_value=0.0, max_value=10.0, value=None,
                           step=0.1, key=widget_key("equity_japan_dividend_yield"),
                           placeholder="2.20", help="Default: 2.20%")
            st.number_input("Current CAEY (%)", min_value=1.0, max_value=15.0, value=None,
                           step=0.1, key=widget_key("equity_japan_current_caey"),
                           placeholder="5.50", help="Default: 5.50%")
            st.number_input("Fair CAEY (%)", min_value=1.0, max_value=15.0, value=None,
                           step=0.1, key=widget_key("equity_japan_fair_caey"),
                           placeholder="5.00", help="Default: 5.00%")

            if advanced_mode:
                st.markdown("---")
                st.markdown("**🔧 Building Blocks (EPS Growth):**")
                st.number_input("Country EPS Growth (%)", min_value=-5.0, max_value=10.0, value=None,
                               step=0.1, key=widget_key("equity_japan_real_eps_growth"),
                               placeholder="0.80", help="Default: 0.80%")
                st.number_input("Regional (DM) EPS Growth (%)", min_value=-5.0, max_value=10.0, value=None,
                               step=0.1, key=widget_key("equity_japan_regional_eps_growth"),
                               placeholder="1.60", help="Default: 1.60%")

        with tab_eq_em:
            st.markdown("**Primary Inputs:**")
            st.number_input("Dividend Yield (%)", min_value=0.0, max_value=10.0, value=None,
                           step=0.1, key=widget_key("equity_em_dividend_yield"),
                           placeholder="3.00", help="Default: 3.00%")
            st.number_input("Current CAEY (%)", min_value=1.0, max_value=15.0, value=None,
                           step=0.1, key=widget_key("equity_em_current_caey"),
                           placeholder="6.50", help="Default: 6.50%")
            st.number_input("Fair CAEY (%)", min_value=1.0, max_value=15.0, value=None,
                           step=0.1, key=widget_key("equity_em_fair_caey"),
                           placeholder="6.00", help="Default: 6.00%")

            if advanced_mode:
                st.markdown("---")
                st.markdown("**🔧 Building Blocks (EPS Growth):**")
                st.caption("EM uses 5-year minimum data window")
                st.number_input("Country EPS Growth (%)", min_value=-5.0, max_value=10.0, value=None,
                               step=0.1, key=widget_key("equity_em_real_eps_growth"),
                               placeholder="3.00", help="Default: 3.00%")
                st.number_input("Regional (EM) EPS Growth (%)", min_value=-5.0, max_value=10.0, value=None,
                               step=0.1, key=widget_key("equity_em_regional_eps_growth"),
                               placeholder="2.80", help="Default: 2.80%")

    # Hedge Fund Assumptions
    with st.expander("🎯 Absolute Return Assumptions", expanded=False):
        st.markdown("**Primary Inputs:**")
        st.number_input("Trading Alpha (%)", min_value=-5.0, max_value=10.0, value=None,
                       step=0.1, key=widget_key("absolute_return_trading_alpha"),
                       placeholder="1.00", help="Default: 1.00% | 50% of historical alpha (~2%)")

        st.markdown("**Factor Betas:**")
        col1, col2 = st.columns(2)
        with col1:
            st.number_input("Market β", min_value=-1.0, max_value=2.0, value=None,
                           step=0.05, key=widget_key("absolute_return_beta_market"),
                           placeholder="0.30", help="Default: 0.30 | Equity market exposure")
            st.number_input("Size β", min_value=-1.0, max_value=2.0, value=None,
                           step=0.05, key=widget_key("absolute_return_beta_size"),
                           placeholder="0.10", help="Default: 0.10 | Small-minus-Big (SMB)")
            st.number_input("Value β", min_value=-1.0, max_value=2.0, value=None,
                           step=0.05, key=widget_key("absolute_return_beta_value"),
                           placeholder="0.05", help="Default: 0.05 | High-minus-Low (HML)")
        with col2:
            st.number_input("Profitability β", min_value=-1.0, max_value=2.0, value=None,
                           step=0.05, key=widget_key("absolute_return_beta_profitability"),
                           placeholder="0.05", help="Default: 0.05 | Robust-minus-Weak (RMW)")
            st.number_input("Investment β", min_value=-1.0, max_value=2.0, value=None,
                           step=0.05, key=widget_key("absolute_return_beta_investment"),
                           placeholder="0.05", help="Default: 0.05 | Conservative-minus-Aggressive (CMA)")
            st.number_input("Momentum β", min_value=-1.0, max_value=2.0, value=None,
                           step=0.05, key=widget_key("absolute_return_beta_momentum"),
                           placeholder="0.10", help="Default: 0.10 | Up-minus-Down (UMD)")

    # AI Chatbot Assistant
    render_chatbot()

# Build overrides and compute results
overrides = build_overrides()

# Debug display (can be removed later)
if overrides:
    pass  # Overrides detected, all good
else:
    # Only show debug if there are macro keys but no overrides (helps debug issues)
    debug_keys = [k for k in st.session_state.keys() if 'macro_us' in k]
    if debug_keys:
        us_val = st.session_state.get('macro_us_inflation_forecast', 'N/A')
        us_default = INPUT_DEFAULTS.get('macro_us_inflation_forecast', 'N/A')
        if us_val != us_default:
            st.info(f"Debug: US Inflation = {us_val} (default: {us_default}), but no override detected")

base_ccy = base_currency.lower()  # 'usd' or 'eur'
engine = CMEEngine(overrides if overrides else None, base_currency=base_ccy)
results = engine.compute_all_returns("Current Scenario")

# Store results in session state for chatbot context
st.session_state['current_results'] = results

# Also compute base case for comparison (same base currency)
base_engine = CMEEngine(None, base_currency=base_ccy)
base_results = base_engine.compute_all_returns("RA Defaults")

# Input Validation Warnings
# Compute macro for validation checks
macro = engine.compute_macro_forecasts()

validation_warnings = []

# Check 1: Real T-Bill rate < -2% (deeply negative real rates for extended period)
for region, region_name in [('us', 'US'), ('eurozone', 'Eurozone'), ('japan', 'Japan'), ('em', 'EM')]:
    region_data = macro[region]
    real_tbill = region_data.get('tbill_rate', 0) - region_data.get('inflation', 0)
    if real_tbill < -0.02:
        validation_warnings.append(
            f"**{region_name} Real T-Bill Rate**: {real_tbill*100:.2f}% — Deeply negative real rates "
            f"(< -2%) are unusual for a 10-year average. Consider if this is realistic."
        )

# Check 2: EM inflation < US inflation (historically rare)
em_inflation = macro['em'].get('inflation', 0)
us_inflation = macro['us'].get('inflation', 0)
if em_inflation < us_inflation:
    validation_warnings.append(
        f"**EM Inflation** ({em_inflation*100:.2f}%) < **US Inflation** ({us_inflation*100:.2f}%) — "
        f"Emerging Markets typically have higher inflation than developed markets."
    )

# Check 3: Equity dividend yield > 6% (very high)
us_div_yield = get_input_value('equity_us_dividend_yield')
if us_div_yield and us_div_yield > 6:
    validation_warnings.append(
        f"**Equity US Dividend Yield**: {us_div_yield:.2f}% — Dividend yields above 6% are historically rare "
        f"and typically signal market stress or data issues."
    )

# Check 4: GDP growth > 4% for DM (optimistic)
us_gdp = macro['us'].get('rgdp_growth', 0)
eu_gdp = macro['eurozone'].get('rgdp_growth', 0)
jp_gdp = macro['japan'].get('rgdp_growth', 0)

if us_gdp > 0.04:
    validation_warnings.append(
        f"**US GDP Growth**: {us_gdp*100:.2f}% — Real GDP growth above 4% is optimistic "
        f"for a developed economy over a 10-year horizon."
    )
if eu_gdp > 0.04:
    validation_warnings.append(
        f"**Eurozone GDP Growth**: {eu_gdp*100:.2f}% — Real GDP growth above 4% is optimistic "
        f"for a developed economy over a 10-year horizon."
    )

# Check 5: T-Bill significantly higher than GDP + Inflation (unusual for extended periods)
for region, region_name in [('us', 'US'), ('eurozone', 'Eurozone')]:
    region_data = macro[region]
    tbill = region_data.get('tbill_rate', 0)
    nominal_gdp = region_data.get('rgdp_growth', 0) + region_data.get('inflation', 0)
    if tbill > nominal_gdp + 0.02:  # T-Bill more than 2% above nominal GDP
        validation_warnings.append(
            f"**{region_name} T-Bill Rate** ({tbill*100:.2f}%) > Nominal GDP ({nominal_gdp*100:.2f}%) + 2% — "
            f"T-Bill rates significantly above nominal GDP are unusual over long horizons."
        )

# Display warnings if any
if validation_warnings:
    st.warning("**⚠️ Input Validation Warnings**")
    with st.expander("View Warnings (click to expand)", expanded=True):
        st.caption("These are soft warnings - your inputs may still be valid for specific scenarios.")
        for warning in validation_warnings:
            st.markdown(f"- {warning}")

# Main content area
col_results, col_details = st.columns([2, 3])

with col_results:
    # Show base currency in header
    currency_label = "EUR" if base_currency == "EUR" else "USD"
    st.markdown(f'<p class="section-header">Expected Returns (10-Year, {currency_label} Base)</p>', unsafe_allow_html=True)

    asset_order = [
        ('liquidity', 'Liquidity', '💵'),
        ('bonds_global', 'Bonds Global', '🏛️'),
        ('bonds_hy', 'Bonds HY', '📊'),
        ('bonds_em', 'Bonds EM', '🌍'),
        ('equity_us', 'Equity US', '🇺🇸'),
        ('equity_europe', 'Equity Europe', '🇪🇺'),
        ('equity_japan', 'Equity Japan', '🇯🇵'),
        ('equity_em', 'Equity EM', '🌏'),
        ('absolute_return', 'Absolute Return', '🎯'),
    ]

    for key, name, icon in asset_order:
        result = results.results[key]
        base_result = base_results.results[key]

        nominal = result.expected_return_nominal * 100
        real = result.expected_return_real * 100
        diff = (result.expected_return_nominal - base_result.expected_return_nominal) * 100

        if abs(diff) < 0.01:
            diff_str = "—"
            diff_color = "#666"
        elif diff > 0:
            diff_str = f"+{diff:.2f}%"
            diff_color = "#28a745"
        else:
            diff_str = f"{diff:.2f}%"
            diff_color = "#dc3545"

        # Check for FX component
        fx_return = result.components.get('fx_return', 0)
        fx_str = ""
        if abs(fx_return) > 0.0001:
            fx_pct = fx_return * 100
            fx_color = "#17a2b8" if fx_pct >= 0 else "#fd7e14"
            fx_str = f'<br/><span style="font-size: 0.75rem; color: {fx_color};">FX: {fx_pct:+.2f}%</span>'

        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 0.8rem; border-radius: 0.5rem;
                    border-left: 4px solid #1E3A5F; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 0.9rem; color: #666;">{icon} {name}</span><br/>
                <span style="font-size: 1.4rem; font-weight: bold; color: #1E3A5F;">{nominal:.2f}%</span>
                <span style="font-size: 0.85rem; color: #666;"> (Real: {real:.2f}%)</span>{fx_str}
            </div>
            <div style="text-align: right;">
                <span style="font-size: 0.8rem; color: {diff_color};">vs Default: {diff_str}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Export buttons
    st.markdown("---")
    st.markdown("**📥 Export Results**")

    # Build export DataFrame
    export_data = []
    for key, name, icon in asset_order:
        result = results.results[key]
        base_result = base_results.results[key]
        asset_enum = AssetClass(key)

        nominal = result.expected_return_nominal * 100
        real = result.expected_return_real * 100
        volatility = EXPECTED_VOLATILITY.get(asset_enum, 0.10) * 100
        diff = (result.expected_return_nominal - base_result.expected_return_nominal) * 100

        export_data.append({
            'Asset Class': name,
            'Expected Return (Nominal)': f"{nominal:.2f}%",
            'Expected Return (Real)': f"{real:.2f}%",
            'Expected Volatility': f"{volatility:.1f}%",
            'vs Default': f"{diff:+.2f}%" if abs(diff) >= 0.01 else "—"
        })

    export_df = pd.DataFrame(export_data)

    col_csv, col_excel = st.columns(2)
    with col_csv:
        csv_buffer = export_df.to_csv(index=False)
        st.download_button(
            label="📄 Download CSV",
            data=csv_buffer,
            file_name=f"cma_results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col_excel:
        # Create Excel file in memory
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            export_df.to_excel(writer, sheet_name='Expected Returns', index=False)

            # Also add macro forecasts sheet
            macro_data = []
            for region_key, region_name in [('us', 'United States'), ('eurozone', 'Eurozone'),
                                             ('japan', 'Japan'), ('em', 'Emerging Markets')]:
                region_data = macro[region_key]
                macro_data.append({
                    'Region': region_name,
                    'E[GDP Growth]': f"{region_data['rgdp_growth']*100:.2f}%",
                    'E[Inflation]': f"{region_data['inflation']*100:.2f}%",
                    'E[T-Bill]': f"{region_data.get('tbill_rate', 0)*100:.2f}%"
                })
            macro_df = pd.DataFrame(macro_data)
            macro_df.to_excel(writer, sheet_name='Macro Forecasts', index=False)

        excel_buffer.seek(0)
        st.download_button(
            label="📊 Download Excel",
            data=excel_buffer,
            file_name=f"cma_results_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

with col_details:
    st.markdown('<p class="section-header">Model Details & Assumptions</p>', unsafe_allow_html=True)

    # Asset selector
    selected_asset = st.selectbox(
        "Select Asset Class for Details",
        options=[key for key, _, _ in asset_order],
        format_func=lambda x: dict((k, f"{i} {n}") for k, n, i in asset_order)[x],
        key="detail_selector"
    )

    if selected_asset and selected_asset in MODEL_FORMULAS:
        model_info = MODEL_FORMULAS[selected_asset]
        result = results.results[selected_asset]

        # Main formula
        st.markdown(f"**{model_info['name']}**")
        st.markdown(f"_{model_info['description']}_")

        st.markdown(f"""
        <div class="formula-box">
            <strong>Main Formula:</strong><br/>
            {model_info['main_formula']}
        </div>
        """, unsafe_allow_html=True)

        # Component breakdown with formulas
        st.markdown("---")
        st.markdown("**Component Breakdown:**")

        for comp_name, comp_value in result.components.items():
            comp_info = model_info['components'].get(comp_name, {})

            with st.expander(f"📐 {comp_name.replace('_', ' ').title()}: **{comp_value * 100:.2f}%**", expanded=False):
                if comp_info:
                    # Formula
                    st.markdown(f"""
                    <div class="formula-box">
                        <strong>Formula:</strong> {comp_info.get('formula', 'N/A')}<br/>
                        <small><em>{comp_info.get('sub_formula', '')}</em></small>
                    </div>
                    """, unsafe_allow_html=True)

                # Show inputs used
                st.markdown("**Inputs Used:**")

                # Get inputs from result
                relevant_inputs = {k: v for k, v in result.inputs_used.items()
                                 if k.startswith(comp_name) or comp_name in k}

                if relevant_inputs:
                    for input_name, input_data in relevant_inputs.items():
                        value = input_data.get('value', 'N/A')
                        source = input_data.get('source', 'default')

                        # Format value
                        if isinstance(value, float):
                            if abs(value) < 0.1 and 'beta' not in input_name.lower():
                                value_str = f"{value * 100:.2f}%"
                            elif 'duration' in input_name.lower() or 'years' in input_name.lower():
                                value_str = f"{value:.1f}"
                            elif 'beta' in input_name.lower():
                                value_str = f"{value:.2f}"
                            else:
                                value_str = f"{value * 100:.2f}%"
                        elif isinstance(value, bool):
                            value_str = "Yes" if value else "No"
                        else:
                            value_str = str(value)

                        # Clean up input name
                        display_name = input_name.replace(f"{comp_name}_", "").replace("_", " ").title()

                        badge = get_source_badge(source)
                        st.markdown(f"- **{display_name}**: {value_str} {badge}", unsafe_allow_html=True)
                else:
                    st.markdown("_No specific inputs for this component_")

        # Show all inputs for this asset class
        st.markdown("---")
        with st.expander("📋 All Model Values (Inputs & Computed)", expanded=False):
            # Separate inputs from computed values
            input_items = []
            computed_items = []
            
            for input_name, input_data in sorted(result.inputs_used.items()):
                value = input_data.get('value', 'N/A')
                source = input_data.get('source', 'default')

                if isinstance(value, float):
                    if 'duration' in input_name.lower() or 'years' in input_name.lower():
                        value_str = f"{value:.1f} years"
                    elif 'beta' in input_name.lower() or 'weight' in input_name.lower():
                        value_str = f"{value:.2f}"
                    else:
                        value_str = f"{value * 100:.3f}%"
                elif isinstance(value, bool):
                    value_str = "Yes" if value else "No"
                else:
                    value_str = str(value)
                
                # Create friendly display name
                display_name = input_name.replace("_", " ").title()
                
                badge = get_source_badge(source)
                item = f"- **{display_name}**: {value_str} {badge}"
                
                if source == 'computed':
                    computed_items.append(item)
                else:
                    input_items.append(item)
            
            # Display inputs first
            if input_items:
                st.markdown("**📥 Inputs (Default or Override):**")
                st.caption("These values can be changed in the sidebar")
                for item in input_items:
                    st.markdown(item, unsafe_allow_html=True)
            
            # Then computed values
            if computed_items:
                st.markdown("")
                st.markdown("**⚙️ Computed Values (Derived from Inputs):**")
                st.caption("These are calculated by the model — change the inputs above to affect them")
                for item in computed_items:
                    st.markdown(item, unsafe_allow_html=True)

# Macro assumptions display
st.divider()
st.markdown('<p class="section-header">10-Year Macro Forecasts (Computed Outputs)</p>', unsafe_allow_html=True)
st.caption("These are the model's computed forecasts based on your inputs. They represent expected average values over the 10-year horizon.")

macro = engine.compute_macro_forecasts()

macro_cols = st.columns(4)
regions = [('us', 'United States 🇺🇸'), ('eurozone', 'Eurozone 🇪🇺'),
           ('japan', 'Japan 🇯🇵'), ('em', 'Emerging Markets 🌍')]

for i, (region_key, region_name) in enumerate(regions):
    with macro_cols[i]:
        region_data = macro[region_key]
        st.markdown(f"**{region_name}**")
        st.markdown(f"- E[GDP Growth]: {region_data['rgdp_growth']*100:.2f}%")
        st.markdown(f"- E[Inflation]: {region_data['inflation']*100:.2f}%")
        if 'tbill_rate' in region_data:
            st.markdown(f"- E[T-Bill]: {region_data['tbill_rate']*100:.2f}%")

# FX Forecast section (only show when EUR base)
if base_currency == "EUR":
    st.markdown("---")
    st.markdown("**Expected FX Changes (EUR Base, Annual):**")
    st.caption("Positive means EUR depreciates vs the foreign currency, adding to foreign asset returns in EUR terms.")

    fx_forecasts = results.fx_forecasts
    if fx_forecasts:
        fx_cols = st.columns(3)
        fx_currencies = [('usd', 'USD 🇺🇸'), ('jpy', 'JPY 🇯🇵'), ('em', 'EM 🌍')]

        for i, (ccy_key, ccy_name) in enumerate(fx_currencies):
            with fx_cols[i]:
                if ccy_key in fx_forecasts:
                    fx_data = fx_forecasts[ccy_key]
                    fx_change = fx_data['fx_change'] * 100
                    carry = fx_data['carry_component'] * 100
                    ppp = fx_data['ppp_component'] * 100

                    color = "#28a745" if fx_change >= 0 else "#dc3545"
                    st.markdown(f"""
                    <div style="background-color: #e8f4f8; padding: 0.5rem; border-radius: 0.3rem; margin-bottom: 0.3rem;">
                        <strong>EUR vs {ccy_name}</strong><br/>
                        <span style="font-size: 1.2rem; color: {color};">{fx_change:+.2f}%/yr</span><br/>
                        <span style="font-size: 0.75rem; color: #666;">Carry: {carry:+.2f}% | PPP: {ppp:+.2f}%</span>
                    </div>
                    """, unsafe_allow_html=True)

# Risk-Return Scatter Plot
st.divider()
st.markdown('<p class="section-header">Risk-Return Profile</p>', unsafe_allow_html=True)

# Prepare data for scatter plot
scatter_data = []
asset_categories = {
    'liquidity': ('Liquidity', '#6c757d', 'Liquidity'),
    'bonds_global': ('Bonds Global', '#1E88E5', 'Bonds'),
    'bonds_hy': ('Bonds HY', '#1565C0', 'Bonds'),
    'bonds_em': ('Bonds EM', '#0D47A1', 'Bonds'),
    'equity_us': ('Equity US', '#E53935', 'Equities'),
    'equity_europe': ('Equity Europe', '#C62828', 'Equities'),
    'equity_japan': ('Equity Japan', '#B71C1C', 'Equities'),
    'equity_em': ('Equity EM', '#D32F2F', 'Equities'),
    'absolute_return': ('Absolute Return', '#43A047', 'Alternatives'),
}

for key, name, icon in asset_order:
    result = results.results[key]
    asset_enum = AssetClass(key)
    
    nominal_return = result.expected_return_nominal * 100
    volatility = EXPECTED_VOLATILITY.get(asset_enum, 0.10) * 100
    
    display_name, color, category = asset_categories.get(key, (name, '#666', 'Other'))
    
    scatter_data.append({
        'name': display_name,
        'return': nominal_return,
        'volatility': volatility,
        'color': color,
        'category': category,
    })

# Create Plotly scatter plot
fig = go.Figure()

# Group by category for legend
categories_added = set()
category_colors = {
    'Liquidity': '#6c757d',
    'Bonds': '#1E88E5',
    'Equities': '#E53935',
    'Alternatives': '#43A047',
}

for item in scatter_data:
    show_legend = item['category'] not in categories_added
    categories_added.add(item['category'])
    
    fig.add_trace(go.Scatter(
        x=[item['volatility']],
        y=[item['return']],
        mode='markers+text',
        name=item['category'] if show_legend else None,
        text=[item['name']],
        textposition='top center',
        textfont=dict(size=10, color='#333'),
        marker=dict(
            size=14,
            color=item['color'],
            line=dict(width=1, color='white'),
        ),
        hovertemplate=f"<b>{item['name']}</b><br>" +
                      f"Expected Return: {item['return']:.2f}%<br>" +
                      f"Expected Volatility: {item['volatility']:.1f}%<br>" +
                      "<extra></extra>",
        legendgroup=item['category'],
        showlegend=show_legend,
    ))

# Update layout
fig.update_layout(
    xaxis_title="Expected Volatility (%)",
    yaxis_title="Expected Return (%)",
    xaxis=dict(
        tickformat='.0f',
        ticksuffix='%',
        gridcolor='#e0e0e0',
        range=[0, max(item['volatility'] for item in scatter_data) * 1.15],
    ),
    yaxis=dict(
        tickformat='.1f',
        ticksuffix='%',
        gridcolor='#e0e0e0',
    ),
    plot_bgcolor='white',
    paper_bgcolor='white',
    height=450,
    margin=dict(l=60, r=40, t=40, b=60),
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=1.02,
        xanchor='center',
        x=0.5,
    ),
    hovermode='closest',
)

st.plotly_chart(fig)

# Sensitivity Analysis Section
st.divider()
with st.expander("📊 What-If Sensitivity Analysis", expanded=False):
    st.markdown("See how expected returns change when key inputs vary.")
    st.caption("Select an input to analyze, then view impact on all asset classes.")

    # Input options for sensitivity analysis
    sensitivity_inputs = {
        'US Inflation': ('macro', 'us', 'inflation_forecast'),
        'US GDP Growth': ('macro', 'us', 'rgdp_growth'),
        'US T-Bill Rate': ('macro', 'us', 'tbill_forecast'),
        'Equity US Dividend Yield': ('equity_us', None, 'dividend_yield'),
        'Equity US CAEY': ('equity_us', None, 'current_caey'),
        'Bonds Global Yield': ('bonds_global', None, 'current_yield'),
    }

    selected_input = st.selectbox(
        "Select Input to Analyze",
        options=list(sensitivity_inputs.keys()),
        key="sensitivity_input_selector"
    )

    # Variation amounts
    variations = [-0.02, -0.01, -0.005, 0, 0.005, 0.01, 0.02]
    variation_labels = ['-2%', '-1%', '-0.5%', 'Base', '+0.5%', '+1%', '+2%']

    if selected_input:
        input_config = sensitivity_inputs[selected_input]
        category, region, param = input_config

        # Build sensitivity table
        sensitivity_data = []
        asset_names_map = {
            'liquidity': 'Liquidity',
            'bonds_global': 'Bonds Global',
            'bonds_hy': 'Bonds HY',
            'bonds_em': 'Bonds EM',
            'equity_us': 'Equity US',
            'equity_europe': 'Equity Europe',
            'equity_japan': 'Equity Japan',
            'equity_em': 'Equity EM',
            'absolute_return': 'Absolute Return',
        }

        for key in asset_names_map.keys():
            row = {'Asset Class': asset_names_map[key]}
            base_return = results.results[key].expected_return_nominal * 100

            for var, label in zip(variations, variation_labels):
                if var == 0:
                    row[label] = base_return
                else:
                    # Build modified overrides
                    modified_overrides = json.loads(json.dumps(overrides)) if overrides else {}

                    # Get current value
                    current_val = get_input_value(f"{category}_{region}_{param}" if region else f"{category}_{param}")
                    if current_val is None:
                        current_val = INPUT_DEFAULTS.get(f"{category}_{region}_{param}" if region else f"{category}_{param}", 0)

                    # Convert to decimal for override (input is in %, override needs decimal)
                    new_val = (current_val / 100) + var

                    # Apply override
                    if region:
                        if category not in modified_overrides:
                            modified_overrides[category] = {}
                        if region not in modified_overrides[category]:
                            modified_overrides[category][region] = {}
                        modified_overrides[category][region][param] = new_val
                    else:
                        if category not in modified_overrides:
                            modified_overrides[category] = {}
                        modified_overrides[category][param] = new_val

                    # Compute with modified overrides
                    try:
                        modified_engine = CMEEngine(modified_overrides, base_currency=base_ccy)
                        modified_results = modified_engine.compute_all_returns("Sensitivity")
                        row[label] = modified_results.results[key].expected_return_nominal * 100
                    except Exception:
                        row[label] = base_return

            sensitivity_data.append(row)

        sensitivity_df = pd.DataFrame(sensitivity_data)

        # Format and style the table
        def style_sensitivity(val, base_val):
            if isinstance(val, str):
                return ''
            diff = val - base_val
            if abs(diff) < 0.01:
                return ''
            elif diff > 0:
                return 'background-color: #d4edda; color: #155724;'
            else:
                return 'background-color: #f8d7da; color: #721c24;'

        # Display as formatted table
        st.markdown(f"**Impact of {selected_input} Changes:**")

        # Create styled dataframe
        display_df = sensitivity_df.copy()
        for col in variation_labels:
            display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}%" if isinstance(x, (int, float)) else x)

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Summary statistics
        st.markdown("---")
        st.caption("**Interpretation:** Green cells indicate higher returns vs base case, red indicates lower returns. "
                   "Assets most sensitive to this input show the largest color changes.")

# Scenario Comparison Section
st.divider()
with st.expander("📈 Scenario Comparison", expanded=False):
    st.markdown("Compare multiple saved scenarios side-by-side.")

    # Load saved scenarios
    comparison_scenarios = load_scenarios(user_id)

    if len(comparison_scenarios) < 2:
        st.info("Save at least 2 scenarios to enable comparison. Use the sidebar to save your current settings.")
    else:
        scenario_names_list = list(comparison_scenarios.keys())

        # Multi-select for scenarios (2-4)
        selected_for_comparison = st.multiselect(
            "Select Scenarios to Compare (2-4)",
            options=scenario_names_list,
            default=scenario_names_list[:min(2, len(scenario_names_list))],
            max_selections=4,
            key="comparison_scenario_selector"
        )

        if len(selected_for_comparison) >= 2:
            # Compute results for each selected scenario
            comparison_results = {}
            for scenario_name in selected_for_comparison:
                scenario_data = comparison_scenarios[scenario_name]
                scenario_overrides = scenario_data.get('overrides', {})
                scenario_base_ccy = scenario_data.get('base_currency', 'usd')

                scenario_engine = CMEEngine(scenario_overrides if scenario_overrides else None,
                                             base_currency=scenario_base_ccy)
                comparison_results[scenario_name] = scenario_engine.compute_all_returns(scenario_name)

            # Build comparison table
            comparison_data = []
            for key, name, icon in asset_order:
                row = {'Asset Class': name}
                for scenario_name in selected_for_comparison:
                    ret = comparison_results[scenario_name].results[key].expected_return_nominal * 100
                    row[scenario_name] = ret
                comparison_data.append(row)

            comparison_df = pd.DataFrame(comparison_data)

            # Calculate differences if exactly 2 scenarios
            if len(selected_for_comparison) == 2:
                s1, s2 = selected_for_comparison
                comparison_df['Difference'] = comparison_df[s1] - comparison_df[s2]

            # Display comparison table
            st.markdown("**Expected Returns Comparison:**")

            display_comp_df = comparison_df.copy()
            for col in selected_for_comparison:
                display_comp_df[col] = display_comp_df[col].apply(lambda x: f"{x:.2f}%")
            if 'Difference' in display_comp_df.columns:
                display_comp_df['Difference'] = comparison_df['Difference'].apply(lambda x: f"{x:+.2f}%")

            st.dataframe(display_comp_df, use_container_width=True, hide_index=True)

            # Grouped bar chart
            st.markdown("---")
            st.markdown("**Visual Comparison:**")

            fig_comp = go.Figure()
            colors = ['#1E3A5F', '#28a745', '#dc3545', '#ffc107']

            for i, scenario_name in enumerate(selected_for_comparison):
                fig_comp.add_trace(go.Bar(
                    name=scenario_name,
                    x=[row['Asset Class'] for row in comparison_data],
                    y=[row[scenario_name] for row in comparison_data],
                    marker_color=colors[i % len(colors)],
                ))

            fig_comp.update_layout(
                barmode='group',
                xaxis_title="Asset Class",
                yaxis_title="Expected Return (%)",
                yaxis=dict(tickformat='.1f', ticksuffix='%'),
                plot_bgcolor='white',
                paper_bgcolor='white',
                height=400,
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
            )

            st.plotly_chart(fig_comp, use_container_width=True)
        else:
            st.warning("Please select at least 2 scenarios to compare.")

# Active overrides display
if overrides:
    st.divider()
    with st.expander("🔧 Active Overrides", expanded=True):
        st.markdown("These values differ from RA defaults:")

        for category, values in overrides.items():
            if isinstance(values, dict):
                for sub_key, sub_values in values.items():
                    if isinstance(sub_values, dict):
                        for param, value in sub_values.items():
                            if isinstance(value, float):
                                if param == 'my_ratio':
                                    st.markdown(f"- **{category}.{sub_key}.{param}**: {value:.2f}")
                                else:
                                    st.markdown(f"- **{category}.{sub_key}.{param}**: {value*100:.2f}%")
                            else:
                                st.markdown(f"- **{category}.{sub_key}.{param}**: {value}")
                    else:
                        if isinstance(sub_values, float):
                            if sub_key in ['duration', 'my_ratio']:
                                st.markdown(f"- **{category}.{sub_key}**: {sub_values}")
                            elif sub_key.startswith('beta_'):
                                st.markdown(f"- **{category}.{sub_key}**: {sub_values}")
                            else:
                                st.markdown(f"- **{category}.{sub_key}**: {sub_values*100:.2f}%")

# Legend
st.divider()
st.markdown("""
<div style="background-color: #f0f0f0; padding: 1rem; border-radius: 0.5rem; font-size: 0.85rem;">
    <strong>Value Types:</strong><br/>
    <span class="default-badge">DEFAULT</span> RA methodology default — can be overridden in sidebar<br/>
    <span class="override-badge">OVERRIDE</span> You changed this value from the default<br/>
    <span class="computed-badge">COMPUTED</span> Calculated by the model from other inputs — change inputs to affect this
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
base_ccy_label = "EUR" if base_currency == "EUR" else "USD"
fx_note = " | FX adjustments applied using PPP methodology" if base_currency == "EUR" else ""
st.markdown(f"""
<div style="text-align: center; color: #666; font-size: 0.85rem;">
    Parkview CMA Tool<br/>
    <strong>Base Currency: {base_ccy_label}</strong>{fx_note}<br/>
    Toggle "Advanced Mode" in sidebar for building block inputs
</div>
""", unsafe_allow_html=True)
