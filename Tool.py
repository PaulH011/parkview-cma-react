"""
Streamlit Frontend for Parkview CMA Tool

Run with: streamlit run app.py
"""

import streamlit as st
from ra_stress_tool.main import CMEEngine
from ra_stress_tool.config import AssetClass

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
        'description': 'Emerging market USD-denominated sovereign bonds. No FX adjustment for USD base; EUR/USD adjustment applied when EUR base.',
        'components': {
            'yield': {
                'formula': 'Avg Yield = E[US T-Bill] + Avg Term Premium + EM Spread',
                'sub_formula': 'USD-denominated; uses US T-Bill plus EM credit spread',
                'inputs': ['current_yield', 'duration', 'tbill_forecast', 'current_term_premium', 'fair_term_premium']
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

# Header with logo
col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.image("assets/parkview_logo.png", width=150)
with col_title:
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
    """Build override dictionary from session state"""
    overrides = {}

    # Macro overrides (both basic and advanced)
    for region in ['us', 'eurozone', 'japan', 'em']:
        region_overrides = {}

        # Basic macro inputs
        for key in ['inflation_forecast', 'rgdp_growth', 'tbill_forecast']:
            session_key = f"macro_{region}_{key}"
            if session_key in st.session_state and st.session_state[session_key] is not None:
                region_overrides[key] = st.session_state[session_key] / 100

        # Advanced macro inputs (building blocks)
        advanced_keys = [
            'population_growth', 'productivity_growth', 'my_ratio',
            'current_headline_inflation', 'long_term_inflation',
            'current_tbill', 'country_factor'
        ]
        for key in advanced_keys:
            session_key = f"macro_{region}_{key}"
            if session_key in st.session_state and st.session_state[session_key] is not None:
                if key == 'my_ratio':
                    region_overrides[key] = st.session_state[session_key]  # Not a percentage
                else:
                    region_overrides[key] = st.session_state[session_key] / 100

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
            if session_key in st.session_state and st.session_state[session_key] is not None:
                if key in ['duration']:
                    bond_overrides[key] = st.session_state[session_key]
                else:
                    bond_overrides[key] = st.session_state[session_key] / 100
        if bond_overrides:
            overrides[bond_key] = bond_overrides

    # Equity overrides
    for region in ['us', 'europe', 'japan', 'em']:
        equity_key = f"equity_{region}"
        equity_overrides = {}
        for key in ['dividend_yield', 'real_eps_growth', 'current_caey', 'fair_caey', 'regional_eps_growth']:
            session_key = f"{equity_key}_{key}"
            if session_key in st.session_state and st.session_state[session_key] is not None:
                equity_overrides[key] = st.session_state[session_key] / 100
        if equity_overrides:
            overrides[equity_key] = equity_overrides

    # Hedge fund overrides
    hf_overrides = {}
    for key in ['trading_alpha', 'beta_market', 'beta_value', 'beta_momentum', 'beta_size', 'beta_profitability', 'beta_investment']:
        session_key = f"absolute_return_{key}"
        if session_key in st.session_state and st.session_state[session_key] is not None:
            if key == 'trading_alpha':
                hf_overrides[key] = st.session_state[session_key] / 100
            else:
                hf_overrides[key] = st.session_state[session_key]
    if hf_overrides:
        overrides['absolute_return'] = hf_overrides

    return overrides

# Sidebar for inputs
with st.sidebar:
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

    st.header("Input Assumptions")

    # Mode toggle
    advanced_mode = st.toggle("Advanced Mode", value=False,
                              help="Show all building block inputs (population growth, productivity, etc.)")

    # Reset button
    if st.button("Reset to Defaults"):
        for key in list(st.session_state.keys()):
            if key not in ['overrides', 'base_currency_toggle']:
                del st.session_state[key]
        st.rerun()

    st.divider()

    # Macro Assumptions
    with st.expander("🌍 Macro Assumptions", expanded=True):
        tab_us, tab_eu, tab_jp, tab_em = st.tabs(["US", "Europe", "Japan", "EM"])

        with tab_us:
            st.markdown("**📊 Direct Forecast Overrides:**")
            st.caption("Override the 10-year forecast directly (bypasses building block calculations)")
            st.number_input("E[Inflation] — 10yr Avg (%)", min_value=-2.0, max_value=15.0, value=None,
                           step=0.1, key="macro_us_inflation_forecast",
                           placeholder="2.29", help="Default: 2.29% | Directly override the 10-year inflation forecast")
            st.number_input("E[Real GDP Growth] — 10yr Avg (%)", min_value=-5.0, max_value=10.0, value=None,
                           step=0.1, key="macro_us_rgdp_growth",
                           placeholder="1.20", help="Default: 1.20% | Directly override the 10-year GDP forecast")
            st.number_input("E[T-Bill Rate] — 10yr Avg (%)", min_value=-1.0, max_value=15.0, value=None,
                           step=0.1, key="macro_us_tbill_forecast",
                           placeholder="3.79", help="Default: 3.79% | Directly override the 10-year T-Bill forecast")

            if advanced_mode:
                st.markdown("---")
                st.markdown("**🔧 Building Blocks (GDP Model):**")
                st.caption("GDP = Output-per-Capita Growth + Population Growth")
                st.number_input("Population Growth (%)", min_value=-3.0, max_value=5.0, value=None,
                               step=0.1, key="macro_us_population_growth",
                               placeholder="0.40", help="Default: 0.40% | UN Population Database forecast")
                st.number_input("Productivity Growth (%)", min_value=-2.0, max_value=5.0, value=None,
                               step=0.1, key="macro_us_productivity_growth",
                               placeholder="1.20", help="Default: 1.20% | EWMA of historical output-per-capita (5yr half-life)")
                st.number_input("MY Ratio", min_value=0.5, max_value=4.0, value=None,
                               step=0.1, key="macro_us_my_ratio",
                               placeholder="2.1", help="Default: 2.1 | Middle/Young population ratio (affects demographic drag)")

                st.markdown("**🔧 Building Blocks (Inflation Model):**")
                st.caption("E[Inflation] = 30% × Current Headline + 70% × Long-Term Target")
                st.number_input("Current Headline Inflation — Today (%)", min_value=-2.0, max_value=15.0, value=None,
                               step=0.1, key="macro_us_current_headline_inflation",
                               placeholder="2.50", help="Default: 2.50% | Latest YoY CPI reading")
                st.number_input("Long-Term Inflation Target (%)", min_value=0.0, max_value=10.0, value=None,
                               step=0.1, key="macro_us_long_term_inflation",
                               placeholder="2.20", help="Default: 2.20% | EWMA of core inflation (5yr half-life)")

                st.markdown("**🔧 Building Blocks (T-Bill Model):**")
                st.caption("E[T-Bill] = 30% × Current T-Bill + 70% × Long-Term Equilibrium")
                st.number_input("Current T-Bill Rate — Today (%)", min_value=-1.0, max_value=15.0, value=None,
                               step=0.1, key="macro_us_current_tbill",
                               placeholder="4.50", help="Default: 4.50% | Today's 3-month T-Bill rate")
                st.number_input("Country Factor (%)", min_value=-2.0, max_value=2.0, value=None,
                               step=0.1, key="macro_us_country_factor",
                               placeholder="0.00", help="Default: 0.00% | Liquidity premium adjustment")

        with tab_eu:
            st.markdown("**📊 Direct Forecast Overrides:**")
            st.caption("Override the 10-year forecast directly")
            st.number_input("E[Inflation] — 10yr Avg (%)", min_value=-2.0, max_value=15.0, value=None,
                           step=0.1, key="macro_eurozone_inflation_forecast",
                           placeholder="2.06", help="Default: 2.06%")
            st.number_input("E[Real GDP Growth] — 10yr Avg (%)", min_value=-5.0, max_value=10.0, value=None,
                           step=0.1, key="macro_eurozone_rgdp_growth",
                           placeholder="0.51", help="Default: 0.51%")

            if advanced_mode:
                st.markdown("---")
                st.markdown("**🔧 Building Blocks (GDP):**")
                st.number_input("Population Growth (%)", min_value=-3.0, max_value=5.0, value=None,
                               step=0.1, key="macro_eurozone_population_growth",
                               placeholder="0.10", help="Default: 0.10%")
                st.number_input("Productivity Growth (%)", min_value=-2.0, max_value=5.0, value=None,
                               step=0.1, key="macro_eurozone_productivity_growth",
                               placeholder="1.00", help="Default: 1.00%")
                st.number_input("MY Ratio", min_value=0.5, max_value=4.0, value=None,
                               step=0.1, key="macro_eurozone_my_ratio",
                               placeholder="2.3", help="Default: 2.3")

                st.markdown("**🔧 Building Blocks (Inflation):**")
                st.number_input("Current Headline Inflation (%)", min_value=-2.0, max_value=15.0, value=None,
                               step=0.1, key="macro_eurozone_current_headline_inflation",
                               placeholder="2.20", help="Default: 2.20%")
                st.number_input("Long-Term Inflation Target (%)", min_value=0.0, max_value=10.0, value=None,
                               step=0.1, key="macro_eurozone_long_term_inflation",
                               placeholder="2.00", help="Default: 2.00% (ECB target)")

        with tab_jp:
            st.markdown("**📊 Direct Forecast Overrides:**")
            st.caption("Override the 10-year forecast directly")
            st.number_input("E[Inflation] — 10yr Avg (%)", min_value=-2.0, max_value=15.0, value=None,
                           step=0.1, key="macro_japan_inflation_forecast",
                           placeholder="1.65", help="Default: 1.65%")
            st.number_input("E[Real GDP Growth] — 10yr Avg (%)", min_value=-5.0, max_value=10.0, value=None,
                           step=0.1, key="macro_japan_rgdp_growth",
                           placeholder="-0.46", help="Default: -0.46%")

            if advanced_mode:
                st.markdown("---")
                st.markdown("**🔧 Building Blocks (GDP):**")
                st.number_input("Population Growth (%)", min_value=-3.0, max_value=5.0, value=None,
                               step=0.1, key="macro_japan_population_growth",
                               placeholder="-0.50", help="Default: -0.50% (declining population)")
                st.number_input("Productivity Growth (%)", min_value=-2.0, max_value=5.0, value=None,
                               step=0.1, key="macro_japan_productivity_growth",
                               placeholder="0.80", help="Default: 0.80%")
                st.number_input("MY Ratio", min_value=0.5, max_value=4.0, value=None,
                               step=0.1, key="macro_japan_my_ratio",
                               placeholder="2.5", help="Default: 2.5 (aging population)")

                st.markdown("**🔧 Building Blocks (Inflation):**")
                st.number_input("Current Headline Inflation (%)", min_value=-2.0, max_value=15.0, value=None,
                               step=0.1, key="macro_japan_current_headline_inflation",
                               placeholder="2.00", help="Default: 2.00%")
                st.number_input("Long-Term Inflation Target (%)", min_value=0.0, max_value=10.0, value=None,
                               step=0.1, key="macro_japan_long_term_inflation",
                               placeholder="1.50", help="Default: 1.50%")

        with tab_em:
            st.markdown("**📊 Direct Forecast Overrides:**")
            st.caption("Override the 10-year forecast directly")
            st.number_input("E[Inflation] — 10yr Avg (%)", min_value=-2.0, max_value=15.0, value=None,
                           step=0.1, key="macro_em_inflation_forecast",
                           placeholder="3.80", help="Default: 3.80%")
            st.number_input("E[Real GDP Growth] — 10yr Avg (%)", min_value=-5.0, max_value=10.0, value=None,
                           step=0.1, key="macro_em_rgdp_growth",
                           placeholder="3.46", help="Default: 3.46%")

            if advanced_mode:
                st.markdown("---")
                st.markdown("**🔧 Building Blocks (GDP):**")
                st.number_input("Population Growth (%)", min_value=-3.0, max_value=5.0, value=None,
                               step=0.1, key="macro_em_population_growth",
                               placeholder="1.00", help="Default: 1.00%")
                st.number_input("Productivity Growth (%)", min_value=-2.0, max_value=5.0, value=None,
                               step=0.1, key="macro_em_productivity_growth",
                               placeholder="2.50", help="Default: 2.50%")
                st.number_input("MY Ratio", min_value=0.5, max_value=4.0, value=None,
                               step=0.1, key="macro_em_my_ratio",
                               placeholder="1.5", help="Default: 1.5 (younger population)")

                st.markdown("**🔧 Building Blocks (Inflation):**")
                st.caption("EM uses 2-year half-life for EWMA")
                st.number_input("Current Headline Inflation (%)", min_value=-2.0, max_value=15.0, value=None,
                               step=0.1, key="macro_em_current_headline_inflation",
                               placeholder="4.50", help="Default: 4.50%")
                st.number_input("Long-Term Inflation Target (%)", min_value=0.0, max_value=10.0, value=None,
                               step=0.1, key="macro_em_long_term_inflation",
                               placeholder="3.50", help="Default: 3.50%")

    # Bond Assumptions
    with st.expander("🏦 Bond Assumptions", expanded=False):
        tab_gov, tab_hy, tab_emb = st.tabs(["Global Gov", "High Yield", "EM Hard"])

        with tab_gov:
            st.markdown("**Primary Inputs:**")
            st.number_input("Current Yield (%)", min_value=0.0, max_value=15.0, value=None,
                           step=0.1, key="bonds_global_current_yield",
                           placeholder="3.50", help="Default: 3.50% | Yield to maturity of bond index")
            st.number_input("Duration (years)", min_value=0.0, max_value=30.0, value=None,
                           step=0.5, key="bonds_global_duration",
                           placeholder="7.0", help="Default: 7.0 years | Modified duration")

            if advanced_mode:
                st.markdown("---")
                st.markdown("**🔧 Building Blocks:**")
                st.number_input("Current Term Premium (%)", min_value=-2.0, max_value=5.0, value=None,
                               step=0.1, key="bonds_global_current_term_premium",
                               placeholder="1.00", help="Default: 1.00% | Current yield - T-Bill")
                st.number_input("Fair Term Premium (%)", min_value=-1.0, max_value=5.0, value=None,
                               step=0.1, key="bonds_global_fair_term_premium",
                               placeholder="1.50", help="Default: 1.50% | EWMA 20yr half-life, 50yr window")

        with tab_hy:
            st.markdown("**Primary Inputs:**")
            st.number_input("Current Yield (%)", min_value=0.0, max_value=20.0, value=None,
                           step=0.1, key="bonds_hy_current_yield",
                           placeholder="7.50", help="Default: 7.50%")
            st.number_input("Duration (years)", min_value=0.0, max_value=15.0, value=None,
                           step=0.5, key="bonds_hy_duration",
                           placeholder="4.0", help="Default: 4.0 years")
            st.number_input("Default Rate (%)", min_value=0.0, max_value=20.0, value=None,
                           step=0.1, key="bonds_hy_default_rate",
                           placeholder="5.50", help="Default: 5.50% | Annual default probability")
            st.number_input("Recovery Rate (%)", min_value=0.0, max_value=100.0, value=None,
                           step=1.0, key="bonds_hy_recovery_rate",
                           placeholder="40.0", help="Default: 40% | Recovery on default")

            if advanced_mode:
                st.markdown("---")
                st.markdown("**🔧 Building Blocks:**")
                st.number_input("Credit Spread (%)", min_value=0.0, max_value=20.0, value=None,
                               step=0.1, key="bonds_hy_credit_spread",
                               placeholder="3.50", help="Default: 3.50% | Spread vs duration-matched Treasury")
                st.number_input("Fair Credit Spread (%)", min_value=0.0, max_value=20.0, value=None,
                               step=0.1, key="bonds_hy_fair_credit_spread",
                               placeholder="4.00", help="Default: 4.00% | EWMA 20yr half-life")
                st.number_input("Current Term Premium (%)", min_value=-2.0, max_value=5.0, value=None,
                               step=0.1, key="bonds_hy_current_term_premium",
                               placeholder="1.00", help="Default: 1.00%")
                st.number_input("Fair Term Premium (%)", min_value=-1.0, max_value=5.0, value=None,
                               step=0.1, key="bonds_hy_fair_term_premium",
                               placeholder="1.50", help="Default: 1.50%")

        with tab_emb:
            st.markdown("**Primary Inputs:**")
            st.number_input("Current Yield (%)", min_value=0.0, max_value=20.0, value=None,
                           step=0.1, key="bonds_em_current_yield",
                           placeholder="6.50", help="Default: 6.50%")
            st.number_input("Duration (years)", min_value=0.0, max_value=15.0, value=None,
                           step=0.5, key="bonds_em_duration",
                           placeholder="5.5", help="Default: 5.5 years")
            st.number_input("Default Rate (%)", min_value=0.0, max_value=10.0, value=None,
                           step=0.1, key="bonds_em_default_rate",
                           placeholder="2.80", help="Default: 2.80% | EM hard currency sovereign default rate")
            st.number_input("Recovery Rate (%)", min_value=0.0, max_value=100.0, value=None,
                           step=1.0, key="bonds_em_recovery_rate",
                           placeholder="55.0", help="Default: 55% | EM sovereign recovery rate")

            if advanced_mode:
                st.markdown("---")
                st.markdown("**🔧 Building Blocks:**")
                st.number_input("Current Term Premium (%)", min_value=-2.0, max_value=5.0, value=None,
                               step=0.1, key="bonds_em_current_term_premium",
                               placeholder="1.50", help="Default: 1.50%")
                st.number_input("Fair Term Premium (%)", min_value=-1.0, max_value=5.0, value=None,
                               step=0.1, key="bonds_em_fair_term_premium",
                               placeholder="2.00", help="Default: 2.00%")

    # Equity Assumptions
    with st.expander("📈 Equity Assumptions", expanded=False):
        tab_eq_us, tab_eq_eu, tab_eq_jp, tab_eq_em = st.tabs(["US", "Europe", "Japan", "EM"])

        with tab_eq_us:
            st.markdown("**Primary Inputs:**")
            st.number_input("Dividend Yield (%)", min_value=0.0, max_value=10.0, value=None,
                           step=0.1, key="equity_us_dividend_yield",
                           placeholder="1.50", help="Default: 1.50% | Trailing 12-month dividend yield")
            st.number_input("Current CAEY (%)", min_value=1.0, max_value=15.0, value=None,
                           step=0.1, key="equity_us_current_caey",
                           placeholder="3.50", help="Default: 3.50% (CAPE ~28) | 1/CAPE")
            st.number_input("Fair CAEY (%)", min_value=1.0, max_value=15.0, value=None,
                           step=0.1, key="equity_us_fair_caey",
                           placeholder="5.00", help="Default: 5.00% (CAPE ~20) | EWMA 20yr half-life")

            if advanced_mode:
                st.markdown("---")
                st.markdown("**🔧 Building Blocks (EPS Growth):**")
                st.caption("Final EPS = 50% Country + 50% Regional, capped at Global GDP")
                st.number_input("Country EPS Growth (%)", min_value=-5.0, max_value=10.0, value=None,
                               step=0.1, key="equity_us_real_eps_growth",
                               placeholder="1.80", help="Default: 1.80% | 50-year log-linear trend")
                st.number_input("Regional (DM) EPS Growth (%)", min_value=-5.0, max_value=10.0, value=None,
                               step=0.1, key="equity_us_regional_eps_growth",
                               placeholder="1.60", help="Default: 1.60% | DM average")

        with tab_eq_eu:
            st.markdown("**Primary Inputs:**")
            st.number_input("Dividend Yield (%)", min_value=0.0, max_value=10.0, value=None,
                           step=0.1, key="equity_europe_dividend_yield",
                           placeholder="3.00", help="Default: 3.00%")
            st.number_input("Current CAEY (%)", min_value=1.0, max_value=15.0, value=None,
                           step=0.1, key="equity_europe_current_caey",
                           placeholder="5.50", help="Default: 5.50%")
            st.number_input("Fair CAEY (%)", min_value=1.0, max_value=15.0, value=None,
                           step=0.1, key="equity_europe_fair_caey",
                           placeholder="5.50", help="Default: 5.50%")

            if advanced_mode:
                st.markdown("---")
                st.markdown("**🔧 Building Blocks (EPS Growth):**")
                st.number_input("Country EPS Growth (%)", min_value=-5.0, max_value=10.0, value=None,
                               step=0.1, key="equity_europe_real_eps_growth",
                               placeholder="1.20", help="Default: 1.20%")
                st.number_input("Regional (DM) EPS Growth (%)", min_value=-5.0, max_value=10.0, value=None,
                               step=0.1, key="equity_europe_regional_eps_growth",
                               placeholder="1.60", help="Default: 1.60%")

        with tab_eq_jp:
            st.markdown("**Primary Inputs:**")
            st.number_input("Dividend Yield (%)", min_value=0.0, max_value=10.0, value=None,
                           step=0.1, key="equity_japan_dividend_yield",
                           placeholder="2.20", help="Default: 2.20%")
            st.number_input("Current CAEY (%)", min_value=1.0, max_value=15.0, value=None,
                           step=0.1, key="equity_japan_current_caey",
                           placeholder="5.50", help="Default: 5.50%")
            st.number_input("Fair CAEY (%)", min_value=1.0, max_value=15.0, value=None,
                           step=0.1, key="equity_japan_fair_caey",
                           placeholder="5.00", help="Default: 5.00%")

            if advanced_mode:
                st.markdown("---")
                st.markdown("**🔧 Building Blocks (EPS Growth):**")
                st.number_input("Country EPS Growth (%)", min_value=-5.0, max_value=10.0, value=None,
                               step=0.1, key="equity_japan_real_eps_growth",
                               placeholder="0.80", help="Default: 0.80%")
                st.number_input("Regional (DM) EPS Growth (%)", min_value=-5.0, max_value=10.0, value=None,
                               step=0.1, key="equity_japan_regional_eps_growth",
                               placeholder="1.60", help="Default: 1.60%")

        with tab_eq_em:
            st.markdown("**Primary Inputs:**")
            st.number_input("Dividend Yield (%)", min_value=0.0, max_value=10.0, value=None,
                           step=0.1, key="equity_em_dividend_yield",
                           placeholder="3.00", help="Default: 3.00%")
            st.number_input("Current CAEY (%)", min_value=1.0, max_value=15.0, value=None,
                           step=0.1, key="equity_em_current_caey",
                           placeholder="6.50", help="Default: 6.50%")
            st.number_input("Fair CAEY (%)", min_value=1.0, max_value=15.0, value=None,
                           step=0.1, key="equity_em_fair_caey",
                           placeholder="6.00", help="Default: 6.00%")

            if advanced_mode:
                st.markdown("---")
                st.markdown("**🔧 Building Blocks (EPS Growth):**")
                st.caption("EM uses 5-year minimum data window")
                st.number_input("Country EPS Growth (%)", min_value=-5.0, max_value=10.0, value=None,
                               step=0.1, key="equity_em_real_eps_growth",
                               placeholder="3.00", help="Default: 3.00%")
                st.number_input("Regional (EM) EPS Growth (%)", min_value=-5.0, max_value=10.0, value=None,
                               step=0.1, key="equity_em_regional_eps_growth",
                               placeholder="2.80", help="Default: 2.80%")

    # Hedge Fund Assumptions
    with st.expander("🎯 Absolute Return Assumptions", expanded=False):
        st.markdown("**Primary Inputs:**")
        st.number_input("Trading Alpha (%)", min_value=-5.0, max_value=10.0, value=None,
                       step=0.1, key="absolute_return_trading_alpha",
                       placeholder="1.00", help="Default: 1.00% | 50% of historical alpha (~2%)")

        st.markdown("**Factor Betas:**")
        col1, col2 = st.columns(2)
        with col1:
            st.number_input("Market β", min_value=-1.0, max_value=2.0, value=None,
                           step=0.05, key="absolute_return_beta_market",
                           placeholder="0.30", help="Default: 0.30 | Equity market exposure")
            st.number_input("Size β", min_value=-1.0, max_value=2.0, value=None,
                           step=0.05, key="absolute_return_beta_size",
                           placeholder="0.10", help="Default: 0.10 | Small-minus-Big (SMB)")
            st.number_input("Value β", min_value=-1.0, max_value=2.0, value=None,
                           step=0.05, key="absolute_return_beta_value",
                           placeholder="0.05", help="Default: 0.05 | High-minus-Low (HML)")
        with col2:
            st.number_input("Profitability β", min_value=-1.0, max_value=2.0, value=None,
                           step=0.05, key="absolute_return_beta_profitability",
                           placeholder="0.05", help="Default: 0.05 | Robust-minus-Weak (RMW)")
            st.number_input("Investment β", min_value=-1.0, max_value=2.0, value=None,
                           step=0.05, key="absolute_return_beta_investment",
                           placeholder="0.05", help="Default: 0.05 | Conservative-minus-Aggressive (CMA)")
            st.number_input("Momentum β", min_value=-1.0, max_value=2.0, value=None,
                           step=0.05, key="absolute_return_beta_momentum",
                           placeholder="0.10", help="Default: 0.10 | Up-minus-Down (UMD)")

# Build overrides and compute results
overrides = build_overrides()
base_ccy = base_currency.lower()  # 'usd' or 'eur'
engine = CMEEngine(overrides if overrides else None, base_currency=base_ccy)
results = engine.compute_all_returns("Current Scenario")

# Also compute base case for comparison (same base currency)
base_engine = CMEEngine(None, base_currency=base_ccy)
base_results = base_engine.compute_all_returns("RA Defaults")

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
