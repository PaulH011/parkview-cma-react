"""
Methodology Page - Comprehensive documentation of the Parkview CMA calculation methodology.

This page serves as a help/reference guide for users to understand:
1. How each expected return is calculated
2. What each input means and its default value
3. How building blocks (advanced mode inputs) contribute to final calculations
"""

import streamlit as st

# =============================================================================
# Authentication - Require login to access this page
# =============================================================================
from auth.middleware import require_auth, logout
from auth.database import init_db

init_db()
user = require_auth()

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A5F;
        margin-bottom: 0.5rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1E3A5F;
        border-bottom: 2px solid #1E3A5F;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .subsection-header {
        font-size: 1.2rem;
        font-weight: bold;
        color: #2E5A8F;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
    }
    .formula-box {
        background-color: #e8f4f8;
        border: 1px solid #b8d4e3;
        border-radius: 0.5rem;
        padding: 1rem;
        font-family: 'Courier New', monospace;
        margin: 1rem 0;
        font-size: 1.1rem;
    }
    .formula-box-highlight {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 0.5rem;
        padding: 1rem;
        font-family: 'Courier New', monospace;
        margin: 1rem 0;
        font-size: 1.1rem;
    }
    .input-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
    }
    .input-table th {
        background-color: #1E3A5F;
        color: white;
        padding: 0.75rem;
        text-align: left;
    }
    .input-table td {
        padding: 0.75rem;
        border-bottom: 1px solid #ddd;
    }
    .input-table tr:hover {
        background-color: #f5f5f5;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .example-box {
        background-color: #e2e3e5;
        border: 1px solid #d6d8db;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .nav-link {
        color: #1E3A5F;
        text-decoration: none;
        font-weight: bold;
    }
    .toc-item {
        padding: 0.25rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<p class="main-header">📚 Methodology Reference Guide</p>', unsafe_allow_html=True)
st.markdown("""
This guide documents the complete calculation methodology used in the Parkview 
Capital Market Assumptions (CMA) tool. Use this reference to understand 
how expected returns are calculated and what each input assumption means.
""")

# User info and logout in sidebar
st.sidebar.markdown(f"""
<div style="background-color: #e8f4f8; padding: 0.5rem 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
    <span style="color: #1E3A5F; font-size: 0.9rem;">Logged in as:</span><br/>
    <strong style="color: #1E3A5F;">{user['email']}</strong>
</div>
""", unsafe_allow_html=True)

if st.sidebar.button("🚪 Logout", use_container_width=True):
    logout()
    st.rerun()

st.sidebar.divider()

# Sidebar navigation
st.sidebar.header("📑 Quick Navigation")
st.sidebar.markdown("""
- [Overview](#overview)
- [Base Currency & FX](#base-currency-fx-adjustments)
- [Macro Models](#macro-models)
  - [GDP Growth](#gdp-growth-model)
  - [Inflation](#inflation-model)
  - [T-Bill Rate](#t-bill-rate-model)
- [Asset Class Models](#asset-class-models)
  - [Liquidity](#liquidity-cash-t-bills)
  - [Bonds Global](#bonds-global-government)
  - [Bonds High Yield](#bonds-high-yield)
  - [Bonds EM](#bonds-em-hard-currency)
  - [Equity](#equity-models)
  - [Absolute Return](#absolute-return-hedge-funds)
- [Input Reference](#input-reference)
- [EWMA Methodology](#ewma-methodology)
""")

# =============================================================================
# OVERVIEW
# =============================================================================
st.markdown('<p class="section-header" id="overview">Overview</p>', unsafe_allow_html=True)

st.markdown("""
The Parkview CMA methodology produces 10-year expected returns for major asset classes. 
The methodology is built on several key principles:

1. **Building Block Approach**: Returns are decomposed into fundamental components (yield, growth, valuation changes, etc.)
2. **Mean Reversion**: Valuations and spreads are assumed to revert to fair value over time
3. **Forward-Looking Macro**: Economic forecasts drive rate expectations
4. **Consistency**: All asset classes use the same underlying macro assumptions

### Forecast Horizon
All expected returns are computed as **10-year annualized averages**. This horizon allows for:
- Mean reversion effects to materialize
- Business cycle variations to smooth out
- Long-term equilibrium relationships to dominate
""")

st.markdown("""
<div class="info-box">
<strong>💡 Key Concept: Real vs. Nominal Returns</strong><br/>
<ul>
<li><strong>Nominal Return</strong> = What you actually receive (includes inflation)</li>
<li><strong>Real Return</strong> = Purchasing power gain (excludes inflation)</li>
<li>Nominal Return = Real Return + Expected Inflation</li>
</ul>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# BASE CURRENCY & FX ADJUSTMENTS
# =============================================================================
st.markdown('<p class="section-header" id="base-currency-fx-adjustments">Base Currency & FX Adjustments</p>', unsafe_allow_html=True)

st.markdown("""
The tool supports two base currencies: **USD** and **EUR**. When you select a base currency, 
all returns are expressed from that currency's perspective, with appropriate FX adjustments 
applied to foreign assets.
""")

st.markdown("""
<div class="info-box">
<strong>💱 Base Currency Toggle</strong><br/>
Use the <strong>Base Currency</strong> selector in the sidebar to switch between USD and EUR perspectives.
All expected returns will automatically adjust to reflect the chosen base currency.
</div>
""", unsafe_allow_html=True)

st.markdown('<p class="subsection-header">📊 FX Adjustment Formula</p>', unsafe_allow_html=True)

st.markdown("""
When viewing returns in a currency different from the asset's local currency, an FX adjustment is applied:
""")

st.markdown("""
<div class="formula-box-highlight">
<strong>E[FX Return] = 30% × (Home T-Bill - Foreign T-Bill) + 70% × (Home Inflation - Foreign Inflation)</strong>
</div>
""", unsafe_allow_html=True)

st.markdown("""
This formula is based on **Purchasing Power Parity (PPP)** theory with two components:

| Component | Weight | Formula | Interpretation |
|-----------|--------|---------|----------------|
| **Carry** | 30% | Home T-Bill - Foreign T-Bill | Short-term interest rate differential |
| **PPP** | 70% | Home Inflation - Foreign Inflation | Long-term inflation differential |

**How to interpret:**
- A **positive** FX return means the home currency is expected to **depreciate** vs the foreign currency
- This **adds** to foreign asset returns when expressed in home currency terms
- A **negative** FX return means the home currency is expected to **appreciate**, reducing foreign asset returns
""")

with st.expander("🔧 Example: EUR Investor Holding US Equities"):
    st.markdown("""
    **Scenario:** EUR-based investor, US equity return = 5.0%
    
    **Macro assumptions:**
    - EUR T-Bill: 3.0%, USD T-Bill: 4.0%
    - EUR Inflation: 2.5%, USD Inflation: 2.2%
    
    **FX Calculation:**
    ```
    Carry component = 3.0% - 4.0% = -1.0%
    PPP component = 2.5% - 2.2% = +0.3%
    
    FX Return = 30% × (-1.0%) + 70% × (+0.3%)
             = -0.30% + 0.21%
             = -0.09%
    ```
    
    **Interpretation:**
    - EUR is expected to **appreciate slightly** vs USD (negative FX return)
    - This **reduces** US equity returns for EUR investors
    - Total EUR return = 5.0% + (-0.09%) = **4.91%**
    """)

st.markdown('<p class="subsection-header">📋 Asset Currency Mapping</p>', unsafe_allow_html=True)

st.markdown("""
Each asset class has a "local currency" that determines when FX adjustments apply:

| Asset Class | Local Currency | USD Base | EUR Base |
|-------------|---------------|----------|----------|
| **Liquidity** | Base currency | No FX adjustment | No FX adjustment |
| **Bonds Global** | USD | No FX adjustment | FX adjustment applied |
| **Bonds High Yield** | USD | No FX adjustment | FX adjustment applied |
| **Bonds EM** | USD | No FX adjustment | FX adjustment applied |
| **Equity US** | USD | No FX adjustment | FX adjustment applied |
| **Equity Europe** | EUR | FX adjustment applied | No FX adjustment |
| **Equity Japan** | JPY | FX adjustment applied | FX adjustment applied |
| **Equity EM** | EM currencies | FX adjustment applied | FX adjustment applied |
| **Absolute Return** | Base currency | No FX adjustment | No FX adjustment |

**Key points:**
- **Liquidity** and **Absolute Return** always use the base currency, so no FX adjustment is ever needed
- **Bonds Global** and **Bonds HY** are USD-denominated, so EUR investors see FX adjustments
- **Equity Europe** is EUR-denominated, so USD investors see FX adjustments
- **EM assets** always have FX adjustments regardless of base currency
""")

st.markdown("""
<div class="warning-box">
<strong>⚠️ Important:</strong> FX forecasts are based on PPP theory, which assumes currencies move toward 
equilibrium over the long term. In practice, currencies can deviate from PPP for extended periods. 
The 10-year horizon helps smooth short-term volatility, but FX remains a significant source of uncertainty.
</div>
""", unsafe_allow_html=True)

# =============================================================================
# MACRO MODELS
# =============================================================================
st.markdown('<p class="section-header" id="macro-models">Macro Economic Models</p>', unsafe_allow_html=True)

st.markdown("""
Macro forecasts are the foundation for all asset class returns. The tool computes forecasts 
for four regions: **US**, **Eurozone**, **Japan**, and **Emerging Markets (EM)**.
""")

# GDP Growth
st.markdown('<p class="subsection-header" id="gdp-growth-model">📈 GDP Growth Model</p>', unsafe_allow_html=True)

st.markdown("""
Real GDP growth is the primary driver of long-term earnings and economic prosperity.
""")

st.markdown("""
<div class="formula-box">
<strong>E[Real GDP Growth] = E[Output-per-Capita Growth] + E[Population Growth]</strong>
</div>
""", unsafe_allow_html=True)

st.markdown("""
Where Output-per-Capita Growth is computed as:
""")

st.markdown("""
<div class="formula-box">
E[Output-per-Capita] = Productivity Growth + Demographic Effect + Adjustment
</div>
""", unsafe_allow_html=True)

st.markdown("""
**Components Explained:**

| Component | Description | How It's Determined |
|-----------|-------------|---------------------|
| **Population Growth** | Expected population growth rate | UN Population Database forecasts |
| **Productivity Growth** | Output per worker growth | EWMA of historical data (5-year half-life) |
| **Demographic Effect** | Impact of aging population | Sigmoid function of MY (Middle/Young) ratio |
| **Adjustment** | Skewness correction | Small negative adjustment (-0.3% to -0.5%) |

**The MY Ratio (Middle/Young):**
- Measures working-age population structure
- Higher MY ratio = older workforce = lower growth
- Typical values: US ~2.1, Japan ~2.5, EM ~1.5
""")

with st.expander("🔧 Advanced: Demographic Effect Calculation"):
    st.markdown("""
    The demographic effect uses a sigmoid transformation of the MY ratio:
    
    ```
    demographic_effect = sigmoid_transform(my_ratio)
    ```
    
    This captures the non-linear relationship between population aging and economic growth:
    - MY < 1.5: Positive demographic dividend (young, growing workforce)
    - MY ~ 2.0: Neutral effect
    - MY > 2.5: Demographic drag (aging workforce)
    """)

# Inflation
st.markdown('<p class="subsection-header" id="inflation-model">📊 Inflation Model</p>', unsafe_allow_html=True)

st.markdown("""
<div class="formula-box">
<strong>E[Inflation] = 30% × Current Headline Inflation + 70% × Long-Term Inflation</strong>
</div>
""", unsafe_allow_html=True)

st.markdown("""
**Component Details:**

| Component | Description | Default Values |
|-----------|-------------|----------------|
| **Current Headline** | Latest YoY CPI reading | US: 2.5%, EU: 2.2%, JP: 2.0%, EM: 4.5% |
| **Long-Term Inflation** | Central bank target or EWMA of core | US: 2.2%, EU: 2.0%, JP: 1.5%, EM: 3.5% |
| **Weights** | Fixed weights on current vs long-term | 30% / 70% |

**Why 30/70 Weighting?**
- Current inflation captures near-term momentum
- Long-term anchor represents central bank credibility
- Blended approach balances responsiveness with stability
""")

with st.expander("🔧 Advanced: Long-Term Inflation Determination"):
    st.markdown("""
    Long-term inflation is determined by:
    
    **For Developed Markets (US, Eurozone, Japan):**
    - EWMA of core inflation with 5-year half-life
    - Anchored around central bank targets
    
    **For Emerging Markets:**
    - EWMA with shorter 2-year half-life (more responsive)
    - Higher structural inflation due to catch-up growth
    """)

# T-Bill Rate
st.markdown('<p class="subsection-header" id="t-bill-rate-model">💵 T-Bill Rate Model</p>', unsafe_allow_html=True)

st.markdown("""
<div class="formula-box">
<strong>E[T-Bill] = 30% × Current T-Bill + 70% × Long-Term T-Bill</strong>
</div>
""", unsafe_allow_html=True)

st.markdown("""
Where the Long-Term T-Bill rate is:
""")

st.markdown("""
<div class="formula-box">
Long-Term T-Bill = max(-0.75%, Country Factor + E[Real GDP] + E[Inflation])
</div>
""", unsafe_allow_html=True)

st.markdown("""
**Component Details:**

| Component | Description | Default Values |
|-----------|-------------|----------------|
| **Current T-Bill** | Today's 3-month T-Bill rate | US: 4.5%, EU: 3.5%, JP: 0.1%, EM: 6.0% |
| **Country Factor** | Liquidity/risk premium adjustment | US: 0%, EU: -0.2%, JP: -0.5%, EM: +0.5% |
| **Rate Floor** | Minimum possible rate | -0.75% (allows for negative rates) |

**The Fisher Equation Logic:**
The long-term T-Bill formula is based on the Fisher equation: 
*Nominal Rate = Real Rate + Inflation*

Where Real Rate ≈ Real GDP Growth in equilibrium.
""")

# =============================================================================
# ASSET CLASS MODELS
# =============================================================================
st.markdown('<p class="section-header" id="asset-class-models">Asset Class Models</p>', unsafe_allow_html=True)

# Liquidity
st.markdown('<p class="subsection-header" id="liquidity-cash-t-bills">💵 Liquidity (Cash/T-Bills)</p>', unsafe_allow_html=True)

st.markdown("""
<div class="formula-box-highlight">
<strong>E[Liquidity Return] = E[T-Bill Rate]</strong>
</div>
""", unsafe_allow_html=True)

st.markdown("""
The simplest asset class - cash returns equal the expected average T-Bill rate over the forecast horizon.

**Key Points:**
- No credit risk (government backed)
- No duration risk (short maturity)
- Real return = Nominal return - Inflation
- Typically the lowest returning asset class
""")

# Bonds Global
st.markdown('<p class="subsection-header" id="bonds-global-government">🏛️ Bonds Global (Government)</p>', unsafe_allow_html=True)

st.markdown("""
<div class="formula-box-highlight">
<strong>E[Bond Return] = Yield Component + Roll Return + Valuation Return - Credit Losses</strong>
</div>
""", unsafe_allow_html=True)

st.markdown("""
For developed market government bonds, Credit Losses = 0 (assumed default-free).
""")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    #### Yield Component
    ```
    Avg Yield = E[T-Bill] + Avg Term Premium
    ```
    
    The yield you earn from holding the bond. Term premium mean-reverts 
    from current to fair value over time.
    
    | Input | Default |
    |-------|---------|
    | Current Yield | 3.5% |
    | Duration | 7.0 years |
    | Current Term Premium | 1.0% |
    | Fair Term Premium | 1.5% |
    """)

with col2:
    st.markdown("""
    #### Roll Return
    ```
    Roll Return = (Term Premium / Maturity) × Duration
    ```
    
    Captures the "roll down" effect as bonds approach maturity 
    and move down the yield curve.
    
    #### Valuation Return
    ```
    Valuation = -Duration × (ΔTerm Premium / Horizon)
    ```
    
    Capital gain/loss from yield changes. Rising yields = 
    falling prices = negative valuation return.
    """)

with st.expander("🔧 Advanced: Term Premium Mean Reversion"):
    st.markdown("""
    The term premium mean-reverts toward fair value using exponential decay:
    
    ```
    avg_term_premium = weighted_average(current_tp → fair_tp over 10 years)
    ```
    
    **Mean Reversion Parameters:**
    - Speed: ~3% per month
    - Window: 50 years for fair value calculation
    - Half-life: 20 years
    
    **Example:**
    - Current Term Premium: 0.5%
    - Fair Term Premium: 1.5%
    - Over 10 years, TP rises from 0.5% toward 1.5%
    - Average TP ≈ 1.0% (roughly midpoint)
    """)

# Bonds High Yield
st.markdown('<p class="subsection-header" id="bonds-high-yield">📊 Bonds High Yield</p>', unsafe_allow_html=True)

st.markdown("""
High yield bonds follow the same framework but include **credit spread** and **credit losses**.
""")

st.markdown("""
<div class="formula-box-highlight">
<strong>E[HY Return] = Yield + Roll Return + Valuation Return - Credit Losses</strong>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    #### Credit Spread Component
    ```
    Avg Yield = E[T-Bill] + Term Premium + Credit Spread
    ```
    
    Credit spread also mean-reverts to fair value.
    
    | Input | Default |
    |-------|---------|
    | Current Yield | 7.5% |
    | Duration | 4.0 years |
    | Credit Spread | 3.5% |
    | Fair Credit Spread | 4.0% |
    """)

with col2:
    st.markdown("""
    #### Credit Loss Component
    ```
    Credit Loss = Default Rate × (1 - Recovery Rate)
    ```
    
    Annual expected loss from defaults.
    
    | Input | Default |
    |-------|---------|
    | Default Rate | 5.5% |
    | Recovery Rate | 40% |
    | **Annual Credit Loss** | **3.3%** |
    """)

st.markdown("""
<div class="warning-box">
<strong>⚠️ Important:</strong> High yield returns include both the <em>income</em> from higher yields 
AND the <em>loss</em> from defaults. The net excess return over government bonds is typically 
smaller than the raw spread suggests.
</div>
""", unsafe_allow_html=True)

# Bonds EM
st.markdown('<p class="subsection-header" id="bonds-em-hard-currency">🌍 Bonds EM (Hard Currency)</p>', unsafe_allow_html=True)

st.markdown("""
EM hard currency bonds are USD-denominated sovereign bonds issued by emerging market countries.
They follow the same framework as other USD bonds with EM-specific credit assumptions.
""")

st.markdown("""
| Input | Default | Note |
|-------|---------|------|
| Current Yield | 6.5% | Higher than DM due to EM credit spread |
| Duration | 5.5 years | Typically shorter than DM |
| Default Rate | 2.8% | EM hard currency sovereign default rate |
| Recovery Rate | 55% | Typical EM sovereign recovery |

**Why USD-Denominated?**
Hard currency bonds are issued in USD, meaning:
- No FX adjustment for USD-based investors (same as Bonds Global, Bonds HY)
- EUR investors receive EUR/USD FX adjustment
- Credit risk is higher than local currency (cannot print USD to repay)
""")

# Equity
st.markdown('<p class="subsection-header" id="equity-models">📈 Equity Models (US, Europe, Japan, EM)</p>', unsafe_allow_html=True)

st.markdown("""
<div class="formula-box-highlight">
<strong>E[Real Equity Return] = Dividend Yield + Real EPS Growth + Valuation Change</strong>
</div>
""", unsafe_allow_html=True)

st.markdown("""
Note: This produces a **real** return. Add inflation to get nominal return.
""")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    #### Dividend Yield
    ```
    Current trailing 12-month 
    dividend yield
    ```
    
    Taken as current value with 
    no mean reversion assumed.
    
    | Region | Default |
    |--------|---------|
    | US | 1.5% |
    | Europe | 3.0% |
    | Japan | 2.2% |
    | EM | 3.0% |
    """)

with col2:
    st.markdown("""
    #### Real EPS Growth
    ```
    EPS = 50% × Country + 
          50% × Regional
    Capped at Global GDP
    ```
    
    Blended country/regional growth 
    based on 50-year log-linear trends.
    
    | Region | Default |
    |--------|---------|
    | US | 1.8% |
    | Europe | 1.2% |
    | Japan | 0.8% |
    | EM | 3.0% |
    """)

with col3:
    st.markdown("""
    #### Valuation Change
    ```
    Uses CAEY mean reversion
    over 20 years
    ```
    
    CAEY = 1/CAPE (Cyclically 
    Adjusted Earnings Yield)
    
    | Region | Current | Fair |
    |--------|---------|------|
    | US | 3.5% | 5.0% |
    | Europe | 5.5% | 5.5% |
    | Japan | 5.5% | 5.0% |
    | EM | 6.5% | 6.0% |
    """)

with st.expander("🔧 Advanced: CAEY Valuation Change Calculation"):
    st.markdown("""
    **CAEY (Cyclically Adjusted Earnings Yield)** = 1 / CAPE
    
    The valuation change formula:
    ```
    Annual CAEY Change = (Fair CAEY / Current CAEY)^(1/20) - 1
    Valuation Return = -Annual CAEY Change (averaged over 10 years)
    ```
    
    **Example - US Equity:**
    - Current CAEY: 3.5% (CAPE ≈ 28)
    - Fair CAEY: 5.0% (CAPE ≈ 20)
    - CAEY needs to rise 43% over 20 years
    - Annual CAEY increase: ~1.8%
    - This means prices fall relative to earnings → **negative valuation return**
    
    **Why 20 Years for Full Reversion?**
    - Valuations are persistent and mean-revert slowly
    - 20-year horizon captures full cycle
    - We average the effect over our 10-year forecast horizon
    """)

with st.expander("🔧 Advanced: EPS Growth Methodology"):
    st.markdown("""
    **Country EPS Growth** is derived from a 50-year log-linear regression of real earnings.
    
    **Regional EPS Growth** averages across the region:
    - Developed Markets (DM): Average of US, Europe, Japan
    - Emerging Markets: EM aggregate
    
    **The 50/50 Blend:**
    ```
    Blended EPS = 0.5 × Country EPS + 0.5 × Regional EPS
    ```
    
    This smooths out country-specific volatility while respecting local trends.
    
    **Global GDP Cap:**
    EPS growth is capped at Global GDP growth to prevent unrealistic assumptions 
    (corporate profits can't grow faster than the economy indefinitely).
    """)

# Absolute Return
st.markdown('<p class="subsection-header" id="absolute-return-hedge-funds">🎯 Absolute Return (Hedge Funds)</p>', unsafe_allow_html=True)

st.markdown("""
<div class="formula-box-highlight">
<strong>E[HF Return] = E[T-Bill] + Σ(βᵢ × Factor Premiumᵢ) + Trading Alpha</strong>
</div>
""", unsafe_allow_html=True)

st.markdown("""
The hedge fund model uses the **Fama-French factor framework** to decompose returns.
""")

st.markdown("""
#### Factor Exposures (Betas) and Premia

| Factor | Symbol | Default β | Historical Premium | Description |
|--------|--------|-----------|-------------------|-------------|
| **Market** | MKT-RF | 0.30 | Equity Return - T-Bill | Equity market exposure |
| **Size** | SMB | 0.10 | 2.0% | Small minus Big |
| **Value** | HML | 0.05 | 3.0% | High minus Low B/M |
| **Profitability** | RMW | 0.05 | 2.5% | Robust minus Weak |
| **Investment** | CMA | 0.05 | 2.5% | Conservative minus Aggressive |
| **Momentum** | UMD | 0.10 | 6.0% | Up minus Down |
""")

st.markdown("""
#### Trading Alpha
```
Expected Alpha = 50% × Historical Alpha
Default: 1.0% (50% of ~2% historical)
```

Alpha represents manager skill beyond systematic factor exposures. 
The 50% haircut accounts for:
- Alpha decay over time
- Survivor bias in historical data
- Capacity constraints
""")

with st.expander("🔧 Advanced: Factor Return Calculation"):
    st.markdown("""
    **Total Factor Return:**
    ```
    Factor Return = Σ(βᵢ × E[Premiumᵢ])
    ```
    
    **Example with defaults:**
    ```
    Market:       0.30 × 5.00% = 1.50%
    Size:         0.10 × 1.00% = 0.10%  (50% of 2%)
    Value:        0.05 × 1.50% = 0.08%  (50% of 3%)
    Profitability: 0.05 × 1.25% = 0.06%  (50% of 2.5%)
    Investment:   0.05 × 1.25% = 0.06%  (50% of 2.5%)
    Momentum:     0.10 × 3.00% = 0.30%  (50% of 6%)
    ─────────────────────────────
    Total Factor Return ≈ 2.10%
    ```
    
    **Note:** Non-market factors use 50% of historical premiums for forward-looking estimates.
    """)

# =============================================================================
# INPUT REFERENCE
# =============================================================================
st.markdown('<p class="section-header" id="input-reference">Input Reference Tables</p>', unsafe_allow_html=True)

st.markdown("""
This section provides complete reference tables for all inputs available in the tool.
""")

# Macro Inputs
st.markdown("### 🌍 Macro Inputs by Region")

macro_data = {
    "Input": [
        "Population Growth", "Productivity Growth", "MY Ratio",
        "Current Headline Inflation", "Long-Term Inflation",
        "Current T-Bill", "Country Factor",
        "E[Inflation] (direct)", "E[GDP Growth] (direct)", "E[T-Bill] (direct)"
    ],
    "US": ["0.4%", "1.2%", "2.1", "2.5%", "2.2%", "4.5%", "0.0%", "—", "—", "—"],
    "Europe": ["0.1%", "1.0%", "2.3", "2.2%", "2.0%", "3.5%", "-0.2%", "—", "—", "—"],
    "Japan": ["-0.5%", "0.8%", "2.5", "2.0%", "1.5%", "0.1%", "-0.5%", "—", "—", "—"],
    "EM": ["1.0%", "2.5%", "1.5", "4.5%", "3.5%", "6.0%", "+0.5%", "—", "—", "—"],
    "Mode": ["Advanced", "Advanced", "Advanced", "Advanced", "Advanced", "Advanced", "Advanced", "Basic", "Basic", "Basic"],
    "Description": [
        "UN Population Database forecast",
        "EWMA of historical output-per-capita (5yr half-life)",
        "Middle/Young population ratio (affects demographic drag)",
        "Latest YoY CPI reading",
        "Central bank target or EWMA of core inflation",
        "Today's 3-month T-Bill rate",
        "Liquidity premium adjustment",
        "Direct override of computed 10-year inflation forecast",
        "Direct override of computed 10-year GDP forecast",
        "Direct override of computed 10-year T-Bill forecast"
    ]
}

st.dataframe(macro_data, hide_index=True)

# Bond Inputs
st.markdown("### 🏦 Bond Inputs")

bond_data = {
    "Input": [
        "Current Yield", "Duration (years)", 
        "Current Term Premium", "Fair Term Premium",
        "Credit Spread", "Fair Credit Spread",
        "Default Rate", "Recovery Rate"
    ],
    "Bonds Global": ["3.5%", "7.0", "1.0%", "1.5%", "—", "—", "0%", "100%"],
    "Bonds HY": ["7.5%", "4.0", "1.0%", "1.5%", "3.5%", "4.0%", "5.5%", "40%"],
    "Bonds EM": ["6.5%", "5.5", "1.5%", "2.0%", "—", "—", "2.8%", "55%"],
    "Mode": ["Basic", "Basic", "Advanced", "Advanced", "Advanced", "Advanced", "Basic", "Basic"],
    "Description": [
        "Yield to maturity of bond index",
        "Modified duration",
        "Current yield minus T-Bill rate",
        "Long-term average term premium (EWMA 20yr half-life)",
        "Spread vs duration-matched Treasury",
        "Long-term average credit spread",
        "Annual default probability",
        "Amount recovered on default"
    ]
}

st.dataframe(bond_data, hide_index=True)

# Equity Inputs
st.markdown("### 📈 Equity Inputs")

equity_data = {
    "Input": [
        "Dividend Yield", "Current CAEY", "Fair CAEY",
        "Country EPS Growth", "Regional EPS Growth"
    ],
    "US": ["1.5%", "3.5%", "5.0%", "1.8%", "1.6%"],
    "Europe": ["3.0%", "5.5%", "5.5%", "1.2%", "1.6%"],
    "Japan": ["2.2%", "5.5%", "5.0%", "0.8%", "1.6%"],
    "EM": ["3.0%", "6.5%", "6.0%", "3.0%", "2.8%"],
    "Mode": ["Basic", "Basic", "Basic", "Advanced", "Advanced"],
    "Description": [
        "Trailing 12-month dividend yield",
        "Cyclically Adjusted Earnings Yield (1/CAPE)",
        "Long-term average CAEY (EWMA 20yr half-life)",
        "50-year log-linear trend EPS growth",
        "Regional average EPS growth (DM or EM)"
    ]
}

st.dataframe(equity_data, hide_index=True)

# Hedge Fund Inputs
st.markdown("### 🎯 Absolute Return (Hedge Fund) Inputs")

hf_data = {
    "Input": ["Trading Alpha", "Market β", "Size β", "Value β", "Profitability β", "Investment β", "Momentum β"],
    "Default": ["1.0%", "0.30", "0.10", "0.05", "0.05", "0.05", "0.10"],
    "Range": ["-5% to 10%", "-1 to 2", "-1 to 2", "-1 to 2", "-1 to 2", "-1 to 2", "-1 to 2"],
    "Description": [
        "Manager skill beyond factors (50% of historical ~2%)",
        "Equity market exposure",
        "Small-cap exposure (SMB factor)",
        "Value stock exposure (HML factor)",
        "Quality/profitability exposure (RMW factor)",
        "Conservative investment exposure (CMA factor)",
        "Momentum exposure (UMD factor)"
    ]
}

st.dataframe(hf_data, hide_index=True)

# =============================================================================
# EWMA METHODOLOGY
# =============================================================================
st.markdown('<p class="section-header" id="ewma-methodology">EWMA Methodology</p>', unsafe_allow_html=True)

st.markdown("""
Many "fair value" estimates use **Exponentially Weighted Moving Averages (EWMA)** to 
compute long-term averages that give more weight to recent observations.
""")

st.markdown("""
<div class="formula-box">
<strong>EWMA Formula:</strong><br/>
EWMA_t = λ × X_t + (1-λ) × EWMA_{t-1}<br/><br/>
Where λ = 1 - exp(-ln(2) / half_life)
</div>
""", unsafe_allow_html=True)

st.markdown("""
#### EWMA Parameters Used in This Model

| Calculation | Window (Years) | Half-Life (Years) | Purpose |
|-------------|---------------|-------------------|---------|
| Productivity Growth | 10 | 5 | GDP building block |
| Inflation (DM) | 10 | 5 | Inflation forecast |
| Inflation (EM) | 10 | 2 | Inflation forecast (faster adjustment) |
| T-Bill Country Factor | 10 | 5 | Rate forecast |
| Bond Term Premium | 50 | 20 | Fair value for mean reversion |
| Credit Spread | 50 | 20 | Fair value for mean reversion |
| Equity CAEY | 50 | 20 | Fair value for mean reversion |

**Why Different Parameters?**
- **Short half-life (2-5 years)**: For inputs that change frequently (inflation, productivity)
- **Long half-life (20 years)**: For structural relationships (term premium, valuations)
- **Long windows (50 years)**: Capture full business/market cycles
""")

# =============================================================================
# MEAN REVERSION
# =============================================================================
st.markdown('<p class="section-header" id="mean-reversion">Mean Reversion Assumptions</p>', unsafe_allow_html=True)

st.markdown("""
Mean reversion is a core assumption: valuations and spreads that deviate from fair value 
are expected to gradually return to normal.
""")

st.markdown("""
#### Mean Reversion Parameters

| Variable | Current → Fair | Time Horizon | Speed |
|----------|---------------|--------------|-------|
| Bond Term Premium | Partial | 10 years | ~3% per month |
| Credit Spread (HY) | 50% | 10 years | — |
| Equity CAEY | Full | 20 years | — |

**Important Notes:**
- Mean reversion is **not guaranteed** — it's an assumption based on historical patterns
- Extreme valuations can persist for extended periods
- The tool allows you to override fair values to test different assumptions
""")

# =============================================================================
# FAQ
# =============================================================================
st.markdown('<p class="section-header">❓ Frequently Asked Questions</p>', unsafe_allow_html=True)

with st.expander("Why are US equity returns lower than historical averages?"):
    st.markdown("""
    US equity returns in the model may be lower than historical averages (10%+) for several reasons:
    
    1. **High Valuations**: Current CAEY of 3.5% (CAPE ~28) is below fair value of 5.0% (CAPE ~20). 
       This creates a valuation headwind as CAEY is expected to rise (prices fall relative to earnings).
    
    2. **Lower Dividend Yields**: Current yields (~1.5%) are below historical averages (~4%).
    
    3. **Building Block Approach**: The model builds returns from fundamentals rather than 
       extrapolating historical returns, which may have benefited from multiple expansion.
    """)

with st.expander("Why is there a GDP cap on EPS growth?"):
    st.markdown("""
    Corporate earnings cannot grow faster than the economy indefinitely because:
    
    1. Profits are a share of GDP — if profits grow faster than GDP, they would eventually 
       exceed 100% of GDP (impossible)
    
    2. Historical corporate profit share has been relatively stable long-term
    
    3. The cap prevents overly optimistic assumptions in high-growth regions
    """)

with st.expander("What's the difference between Basic and Advanced mode?"):
    st.markdown("""
    **Basic Mode** provides:
    - Direct forecast overrides (E[Inflation], E[GDP], E[T-Bill])
    - Primary asset inputs (yields, durations, valuations)
    - Sufficient for most stress testing scenarios
    
    **Advanced Mode** adds:
    - Building block inputs (population growth, productivity, MY ratio)
    - Intermediate calculations (term premiums, credit spreads)
    - Full control over how forecasts are computed
    
    Advanced mode is useful when you want to understand or modify the 
    underlying drivers of forecasts rather than just the final numbers.
    """)

with st.expander("How should I interpret negative valuation returns?"):
    st.markdown("""
    Negative valuation returns indicate that current valuations are **expensive** relative to fair value:
    
    - **Bonds**: Negative valuation = term premiums expected to rise → yields rise → prices fall
    - **Equities**: Negative valuation = CAEY expected to rise → CAPE expected to fall → P/E compression
    
    This doesn't mean you'll lose money — it means the valuation component subtracts from 
    total return rather than adding to it. Total return can still be positive if yield and 
    growth components are large enough.
    """)

with st.expander("How often should default values be updated?"):
    st.markdown("""
    Default values in this tool represent **typical** starting points but should be updated regularly:
    
    | Input Type | Update Frequency |
    |------------|------------------|
    | Current yields, T-Bills | Monthly or more |
    | Dividend yields, CAEY | Quarterly |
    | Macro forecasts (GDP, inflation) | Quarterly |
    | Fair values (EWMA-based) | Annually |
    | Structural parameters | Rarely (methodology changes) |
    
    The tool is designed for **scenario analysis** — changing inputs to see how returns respond — 
    rather than providing definitive forecasts.
    """)

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <strong>Parkview CMA Methodology Reference</strong><br/>
    <em>Return to the main tool to run stress tests.</em>
</div>
""", unsafe_allow_html=True)
