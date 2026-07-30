# Parkview CMA — Complete Methodology Reference

**Purpose**: this document is the exhaustive specification of every calculation, input, default, constant, and dependency in the Parkview Capital Market Assumptions Tool. It is written so that a reader can reconstruct the entire tool as a spreadsheet, formula-for-formula, without reading the source code.

**Scope**: covers all 10 asset classes (Liquidity, Bonds Global, Bonds HY, Bonds EM HC, Bonds Inflation Linked, Equity US/Europe/Japan/EM, Absolute Return), both equity model variants (Research Affiliates and Grinold-Kroner), three base currencies (USD, EUR and CHF), and the FX adjustment mechanism. **CHF exception**: Bonds Inflation Linked is not offered in CHF base (Switzerland has no domestic inflation-linked government bond market), so CHF produces 9 asset classes.

**Defaults shown reflect Q2 2026** (commit `f1dd905`, May 2026). When a default is "displayed in percentage points" it means the UI shows `2.50` for 2.5%; when it is "stored as a decimal" the engine uses `0.025`.

---

## Table of Contents

1. [Conventions](#1-conventions)
2. [Computation Order](#2-computation-order)
3. [Macro Models](#3-macro-models)
4. [FX Adjustment](#4-fx-adjustment)
5. [Bond Framework (Common)](#5-bond-framework-common)
6. [Bonds Global Government](#6-bonds-global-government)
7. [Bonds High Yield](#7-bonds-high-yield)
8. [Bonds Emerging Market Hard Currency](#8-bonds-emerging-market-hard-currency)
9. [Bonds Inflation Linked](#9-bonds-inflation-linked)
10. [Equity — Research Affiliates Model](#10-equity--research-affiliates-model)
11. [Equity — Grinold-Kroner Model](#11-equity--grinold-kroner-model)
12. [Liquidity (Cash)](#12-liquidity-cash)
13. [Absolute Return (Hedge Funds)](#13-absolute-return-hedge-funds)
14. [Default Inputs (Q2 2026)](#14-default-inputs-q2-2026)
15. [Override System](#15-override-system)
16. [Worked Examples](#16-worked-examples)
17. [Spreadsheet Recreation Guide](#17-spreadsheet-recreation-guide)
18. [Source-File Reference](#18-source-file-reference)

---

## 1. Conventions

### 1.1 Units

| Layer | Unit |
|---|---|
| Engine internals (Python `ra_stress_tool/`) | **Decimals** — 0.025 means 2.5% |
| Frontend display (`web/lib/constants.ts`, UI) | **Percentage points** — 2.50 means 2.5% |
| Backend defaults endpoint (`api/routes/defaults.py`) | **Percentage points** |
| Frontend → backend override payload | **Decimals** (the frontend divides by 100 before sending) |
| Pure-number inputs (durations, P/E ratios, MY ratio, betas, inflation_beta) | **Unitless** — sent as-is, no /100 conversion |

The pure-number fields that bypass the /100 conversion when sent as overrides:
`my_ratio`, `duration` (for bonds), `inflation_beta` (for ILBs), `current_pe`, `target_pe`, all `beta_*` factors (for Absolute Return).

**`reversion_speed`** (RA equity λ) is a special case: the UI stores it as a percentage (default 100 = 100%) and the frontend divides by 100 before sending, so the engine receives 1.0. From the spreadsheet author's perspective, treat it the same as any other percentage input — show "100%" in the cell, use 1.0 in the formula.

### 1.2 Forecast horizon

Hard-coded at **10 years** everywhere (`forecast_horizon = 10`). Some sub-formulas reference longer mean-reversion timescales (e.g. equity CAEY reverts over 20 years, EWMA half-lives), but the headline expected return is always a 10-year average.

### 1.3 Output

For each asset class the engine produces:
- `expected_return_nominal` — annual expected return in the base currency, decimal
- `expected_return_real` — `nominal − base-region inflation` (for cash and bonds), or computed within the model (equity RA and ILB derive real first, then add inflation)
- `components` — the additive decomposition (yield, roll, valuation, etc.)
- `inputs_used` — every input value with provenance tag. The Python `InputSource` enum has 3 values: `default`, `override`, `computed`. A fourth string tag `affected_by_override` is attached only to macro-dependency tracking (not part of the enum) — it marks values that weren't directly overridden but were derived from something that was.
- `macro_dependencies` — which macro inputs this asset depends on

### 1.4 Base currency switch

`base_currency ∈ {'usd', 'eur', 'chf'}`. Affects:
- Liquidity uses the base-region T-Bill directly (US, Eurozone, or Switzerland)
- Inflation Linked switches between USD-TIPS and EUR-ILB regime inputs. **Not offered in CHF base** — Switzerland has no domestic linker market; the engine omits the asset class from CHF results entirely.
- Bonds Global switches between USD-Treasury/Global-Agg, Bund/EUR-Sovereign, and Swiss-Confederation (Eidgenossen) regime inputs
- Absolute Return uses the base-region T-Bill as the risk-free leg
- All other assets (Bonds HY, EM HC, all 4 equities) get an additive **FX adjustment** to translate their native-currency return into the base currency. In CHF base this includes **Equity Europe** (EUR is foreign to a CHF investor), so all four FX pairs are active: CHF→USD, CHF→EUR, CHF→JPY, CHF→EM.

The Switzerland macro region exists only to serve CHF base: it is **not** part of the Global RGDP weights (26/15/5/40 unchanged — Switzerland is ~0.9% of world GDP, part of the omitted rest-of-world), and it has no effect on USD- or EUR-base results.

---

## 2. Computation Order

Strict dependency order. A spreadsheet must compute in this sequence:

```
┌─────────────────────────────────────────────────────────┐
│ STEP 1 — Macro forecasts (per region: us, eurozone,     │
│          japan, em)                                     │
│   1a. RGDP growth          (building blocks → E[RGDP])  │
│   1b. Inflation            (building blocks → E[Inf])   │
│   1c. T-Bill rate          (depends on 1a + 1b)         │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ STEP 2 — Global RGDP (GDP-weighted average of 4 regions)│
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ STEP 3 — Asset returns (computable in any order within  │
│          this step; no inter-asset dependencies except  │
│          Absolute Return ← US Equity)                   │
│   3a. Liquidity (uses base-region T-Bill, inflation)    │
│   3b. Bonds Global Gov  (regime: USD or EUR)            │
│   3c. Bonds HY                                          │
│   3d. Bonds EM HC                                       │
│   3e. Bonds Inflation Linked (regime: USD or EUR)       │
│   3f. Equity US, Europe, Japan, EM (RA or GK)           │
│   3g. Absolute Return  (depends on US Equity return)    │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ STEP 4 — FX adjustment (only for foreign-currency       │
│          assets when base ≠ local). Adds an FX term     │
│          to nominal and real return.                    │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Macro Models

### 3.1 Real GDP Growth — `E[RGDP]`

For each region `r ∈ {us, eurozone, japan, em}`:

```
E[RGDP]_r = output_per_capita_growth_r + population_growth_r

output_per_capita_growth_r = productivity_growth_r
                           + demographic_effect_r
                           + adjustment_r
```

Where:

**Demographic effect** (sigmoid of Middle-to-Young ratio):
```
z          = 2.0 × (2.0 − my_ratio_r)
sigmoid_z  = 1 / (1 + exp(−z))
demographic_effect_r = (sigmoid_z − 0.5) × 0.02
```

Result range: `±1%`. Positive when MY < 2.0 (young population, growth tailwind); negative when MY > 2.0 (aging, headwind).

**Adjustment**: hardcoded per region, intended to capture skewness / one-time factors. Currently:
- US: `−0.003` (−0.30%)
- Eurozone: `−0.003` (−0.30%)
- Japan: `−0.003` (−0.30%)
- EM: `−0.005` (−0.50%)

The engine has `adjustment = -0.003 if region in ['us', 'eurozone', 'japan'] else -0.005` ([macro.py:101](ra_stress_tool/models/macro.py:101)). All DM regions share `-0.003`, EM is `-0.005`. The web UI's macro panel does not surface this row separately — it is folded into the building-block computation.

### 3.2 Inflation Forecast — `E[Inflation]`

```
E[Inflation]_r = 0.30 × current_headline_inflation_r
               + 0.70 × long_term_inflation_r
               + adjustment_r
```

`adjustment_r` defaults to `0` (no override applied).

The 30/70 weighting reflects the RA methodology that current inflation captures near-term momentum while the long-term anchor reflects central bank credibility.

### 3.3 T-Bill Rate Forecast — `E[T-Bill]`

```
rate_floor = −0.0075   (−0.75%, a hardcoded minimum applied ONLY
                       to the long-term T-Bill component, not to
                       the final blended E[T-Bill])

long_term_tbill_r = max(rate_floor,
                        country_factor_r + E[RGDP]_r + E[Inflation]_r)

E[T-Bill]_r = 0.30 × current_tbill_r + 0.70 × long_term_tbill_r
```

Country factor for each region (used both as default and as adjustable building block):
- US: `0.000`
- Eurozone: `−0.002` (−0.20%)
- Japan: `−0.005` (−0.50%)
- EM: `−0.034` (−3.40%) — *reflects financial-repression / capital-controls suppression of EM short rates below the theoretical RGDP+Inflation equilibrium; required to keep computed E[T-Bill] near 4% given EM RGDP 3.4% and Inflation 4.0%*
- Switzerland: `−0.012` (−1.20%) — *safe-haven franc: SNB policy rates sit structurally below the RGDP+Inflation equilibrium; calibrated so E[T-Bill] lands near 0.60% given Swiss RGDP 1.2% and Inflation 0.85%*

### 3.4 Direct-forecast override path

The engine allows users to bypass the building-block math by overriding `inflation_forecast`, `rgdp_growth`, or `tbill_forecast` directly. If overridden, the override wins; the building blocks become informational. This is exposed in the UI as "Direct Forecast Overrides" with the building blocks shown below as the underlying composition.

### 3.5 Global RGDP

GDP-weighted average across 4 regions. Used **only** by the RA equity model as a cap on real EPS growth.

```
weights = {us: 0.26, eurozone: 0.15, japan: 0.05, em: 0.40}
total_weight = sum(weights) = 0.86

E[RGDP]_global = Σ ((weights[r] / total_weight) × E[RGDP]_r)
                                              for r in regions
```

The denominator normalises because the four explicit regions sum to 0.86 (rest-of-world omitted).

### 3.6 Building-block defaults (Q2 2026)

| Region | curr inflation | LT inflation | curr T-Bill | pop growth | productivity | MY ratio | country factor |
|---|---|---|---|---|---|---|---|
| US | 3.00% | 3.00% | 3.60% | 0.40% | 1.20% | 2.1 | 0.00% |
| Eurozone | 2.00% | 2.00% | 2.10% | 0.10% | 1.49% | 2.3 | −0.20% |
| Japan | 1.50% | 1.50% | 1.62% | −0.20% | 1.59% | 2.3 | −0.50% |
| EM | 4.00% | 4.00% | 4.00% | 1.00% | 2.44% | 1.5 | −3.40% |
| Switzerland* | 0.50% | 1.00% | 0.00% | 0.70% | 1.00% | 2.2 | −1.20% |

\* CHF base only; not in Global RGDP weights. Calibrated mid-2026: FSO CPI 0.5% YoY, SNB policy 0% (SARON ≈ −0.04%), FSO population growth 0.7%, productivity ~1.0% (FSO 2000–2022 average), LT inflation anchor 1.0% (SNB price-stability range 0–2%, long-term survey expectations). The MY ratio is expressed in the tool's own convention (sigmoid midpoint 2.0; US 2.1, EZ/JP 2.3) — Switzerland is set at 2.2: aging, but softened by immigration relative to EZ/Japan.

### 3.7 Computed forecasts from these defaults

| Region | E[Inflation] | E[RGDP] | E[T-Bill] |
|---|---|---|---|
| US | 3.00% | 1.2003% | 4.0202% |
| Eurozone | 2.00% | 0.9987% | 2.5891% |
| Japan | 1.50% | 0.7987% | 1.7451% |
| EM | 4.00% | 3.4021% | 4.0015% |
| Switzerland | 0.85% | 1.2026% | 0.5968% |

**Global RGDP**: `2.1659%` (weighted average using the 26/15/5/40 weights above, normalised by 0.86).

---

## 4. FX Adjustment

When `base_currency ≠ asset_local_currency`, an additive FX term is applied. The formula captures **unhedged** foreign-asset returns as experienced by the base-currency investor.

### 4.1 Asset → Local Currency Map

| Asset Class | Local Currency | FX adj. USD base | FX adj. EUR base | FX adj. CHF base |
|---|---|---|---|---|
| Liquidity | `base` (no FX) | No | No | No |
| Bonds Global Gov | `base` (regime-based) | No | No | No |
| Bonds HY | `usd` | No | Yes | Yes |
| Bonds EM HC | `usd` | No | Yes | Yes |
| Bonds Inflation Linked | `base` (regime-based) | No | No | — (not offered) |
| Equity US | `usd` | No | Yes | Yes |
| Equity Europe | `eur` | Yes | No | Yes |
| Equity Japan | `jpy` | Yes | Yes | Yes |
| Equity EM | `em` | Yes | Yes | Yes |
| Absolute Return | `base` (no FX) | No | No | No |

### 4.2 Currency → Macro Region Map

| Currency | Macro Region |
|---|---|
| `usd` | `us` |
| `eur` | `eurozone` |
| `jpy` | `japan` |
| `em` | `em` |
| `chf` | `switzerland` |

### 4.3 FX Formula

For a base-currency investor holding a foreign-currency asset:

```
home   = base currency region
foreign = asset local currency region

carry_component = E[T-Bill]_home − E[T-Bill]_foreign
ppp_component   = E[Inflation]_home − E[Inflation]_foreign

CARRY_WEIGHT = 0.30
PPP_WEIGHT   = 0.70

fx_change = CARRY_WEIGHT × carry_component
          + PPP_WEIGHT   × ppp_component
```

Interpretation: `fx_change > 0` means the **home currency is expected to depreciate** vs the foreign currency → the foreign asset's return is **boosted** when measured in home-currency terms.

```
asset_return_in_base = asset_return_in_local_currency + fx_change
```

The same `fx_change` is added to both nominal and real returns (FX is treated as a translation effect, not a real/nominal distinction).

### 4.4 Worked numbers (Q2 2026)

USD base, EUR-denominated asset (e.g. Equity Europe):
```
carry = 4.0202% − 2.5891% = +1.4311%
ppp   = 3.0000% − 2.0000% = +1.0000%
fx    = 0.30 × 1.4311 + 0.70 × 1.0000 = +0.4293 + 0.7000 = +1.1293%
```
→ USD depreciates ~1.13% vs EUR per year → +1.13% added to EUR asset's USD-base return.

USD base, JPY asset (Equity Japan):
```
carry = 4.0202% − 1.7451% = +2.2751%
ppp   = 3.0000% − 1.5000% = +1.5000%
fx    = 0.30 × 2.2751 + 0.70 × 1.5000 = +0.6825 + 1.0500 = +1.7325%
```

USD base, EM asset (Equity EM):
```
carry = 4.0202% − 4.0015% = +0.0187%
ppp   = 3.0000% − 4.0000% = −1.0000%
fx    = 0.30 × 0.0187 + 0.70 × −1.0000 = +0.0056 − 0.7000 = −0.6944%
```
→ USD appreciates vs EM → EM asset return is **reduced** by 0.69% in USD terms.

CHF base, USD-denominated asset (e.g. Equity US, Bonds HY, Bonds EM HC):
```
carry = 0.5968% − 4.0202% = −3.4234%
ppp   = 0.8500% − 3.0000% = −2.1500%
fx    = 0.30 × −3.4234 + 0.70 × −2.1500 = −1.0270 − 1.5050 = −2.5320%
```
→ CHF expected to **appreciate** ~2.53%/yr vs USD → USD assets lose 2.53%/yr in CHF terms. This is the defining feature of the CHF set: all four pairs are negative (CHF→USD −2.53%, CHF→EUR −1.40%, CHF→JPY −0.80%, CHF→EM −3.23%), so every foreign asset gets a haircut for the safe-haven franc.

---

## 5. Bond Framework (Common)

All four bond classes share a common backbone with class-specific extensions. The base formula:

```
E[Nominal Return] = avg_yield
                  + roll_return
                  + valuation_return
                  − credit_loss

E[Real Return]    = E[Nominal Return] − inflation_forecast
```

(Inflation Linked overrides this — see §9.)

### 5.1 Average Yield over horizon

```
implied_TP = current_yield − tbill_forecast

If current_yield is OVERRIDE and current_term_premium is NOT OVERRIDE:
    effective_current_TP = implied_TP
    # NOTE: fair_term_premium is NOT modified by this branch — it
    # retains whatever default or override value it had. This means
    # if a user overrides only current_yield, the implied current TP
    # will mean-revert toward the unchanged fair_TP over the horizon.
    # For HY in particular, overriding current_yield to (say) 9% gives
    # implied current_TP ~5%, but fair_TP stays at its default 1.00%
    # → large negative valuation drag from TP mean reversion.
Else:
    effective_current_TP = current_term_premium  (default or override)

reversion_speed = abs(MEAN_REVERSION_PARAMS['bond_term_premium_bounds'][0])
                = abs(−1.0) = 1.0

avg_TP over horizon (years = 10):
    total = 0
    value = effective_current_TP
    For year in 1..10:
        total += value
        value = value + reversion_speed × (fair_TP − value)
    avg_TP = total / 10
```

With `reversion_speed = 1.0`, after the first iteration `value = fair_TP`, so the closed-form is:

```
avg_TP = (effective_current_TP + fair_TP × 9) / 10
```

```
avg_yield = tbill_forecast + avg_TP
```

This is what shows as `yield` in the breakdown output.

### 5.2 Roll Return

```
maturity_years = 10
slope          = current_term_premium / maturity_years
roll_return    = slope × duration
```

Note: uses `current_term_premium`, not the average.

### 5.3 Valuation Return (term premium mean reversion)

```
monthly_reversion       = 0.03
reversion_fraction      = 1 − (1 − monthly_reversion)^(horizon × 12)
                        = 1 − 0.97^120
                        = 1 − 0.025860
                        ≈ 0.97414
reversion_fraction      = min(reversion_fraction, 1.0)

expected_tp_change      = (fair_term_premium − current_term_premium) × reversion_fraction
valuation_return        = −duration × expected_tp_change / horizon
```

Interpretation: if `fair_TP > current_TP`, TP is expected to rise → yields rise → bond prices fall → negative valuation return.

### 5.4 Credit Loss

```
credit_loss = default_rate × (1 − recovery_rate)
```

Annual figure, subtracted from yield-component-plus-roll-plus-valuation.

---

## 6. Bonds Global Government

**Asset class identifier**: `bonds_global`

**Regime-based** (Q2 2026 change; CHF added Q3 2026): the engine selects between three parameter sets based on `base_currency`:
- USD base → uses US Treasury / Global Aggregate USD-centric inputs and US macro region
- EUR base → uses Bund / EUR sovereign aggregate inputs and Eurozone macro region
- CHF base → uses Swiss Confederation (Eidgenossen) inputs and Switzerland macro region

**No FX adjustment** is applied to Bonds Global. It is treated as a native-currency asset on both sides.

### 6.1 Formula

Standard bond framework (§5). Credit loss = 0 (DM sovereign assumed default-free).

```
E[Nominal] = avg_yield + roll_return + valuation_return − 0
E[Real]    = E[Nominal] − inflation_forecast
           (using inflation from the regime's macro region)
```

### 6.2 Inputs

| Field | USD regime | EUR regime | CHF regime | Unit |
|---|---|---|---|---|
| `current_yield` | 4.60% | 3.00% | 0.40% | % |
| `duration` | 8.0 | 7.5 | 9.0 | years |
| `current_term_premium` | 0.81% | 0.40% | −0.20% | % |
| `fair_term_premium` | 1.00% | 0.50% | 0.20% | % |

CHF regime notes: 10y Eidgenosse ≈ 0.40% (Jul 2026); the SBI domestic government market is long-duration (~9–10y; the 7–15y segment ETF shows 10.2y effective duration). The Swiss curve is flat, so the current TP is slightly **negative** vs E[T-Bill] 0.60%, normalizing to a small positive fair TP.

### 6.3 Macro inputs consumed

- `tbill_forecast` of the regime's macro region (US for USD, Eurozone for EUR)
- `inflation_forecast` of the regime's macro region (for real-return derivation)

### 6.4 Override paths

- USD regime: `bonds_global.usd.<field>`
- EUR regime: `bonds_global.eur.<field>`
- CHF regime: `bonds_global.chf.<field>`

---

## 7. Bonds High Yield

**Asset class identifier**: `bonds_hy`

Always uses **US** macro (T-Bill and inflation) regardless of base currency. FX adjustment applied if base = EUR.

### 7.1 Formula

```
base_compute_return = standard bond framework (§5)

# HY-specific spread valuation add-on
hy_reversion_fraction = 0.5     (50% reversion over horizon, NOT the 97.41% used by TP)
spread_change         = (fair_credit_spread − credit_spread) × 0.5
spread_valuation      = −duration × spread_change / horizon

E[Nominal] = base_compute_return + spread_valuation
E[Real]    = E[Nominal] − US inflation_forecast
```

The HY model's `valuation_return` component (from §5.3) is the **sum** of TP-valuation and credit-spread-valuation, both stored under the `valuation` key in the breakdown.

### 7.2 Inputs

| Field | Default | Unit |
|---|---|---|
| `current_yield` | 7.10% | % |
| `duration` | 3.0 | years |
| `current_term_premium` | 1.00% | % |
| `fair_term_premium` | 1.00% | % |
| `credit_spread` | 2.60% | % |
| `fair_credit_spread` | 4.00% | % |
| `default_rate` | 3.40% | % |
| `recovery_rate` | 40.0% | % |

### 7.3 Override paths

`bonds_hy.<field>` — flat structure (no regime).

---

## 8. Bonds Emerging Market Hard Currency

**Asset class identifier**: `bonds_em`

Always USD-denominated (definitional — "hard currency" = USD-issued EM sovereign debt). Always uses **US** macro. FX adjustment applied if base = EUR.

### 8.1 Formula

```
em_spread             = 0.02 (hardcoded 2% EM sovereign spread over US Treasury curve)
em_tbill_forecast     = US E[T-Bill] + em_spread

# Standard bond framework with em_tbill_forecast as the base rate
E[Nominal] = (em_tbill_forecast + avg_TP)   ← appears as "yield" in output
           + roll_return
           + valuation_return
           − credit_loss
E[Real]    = E[Nominal] − US inflation_forecast
```

The 2% `em_spread` is a hardcoded constant in `bonds.py:558` — not user-overridable.

### 8.2 Inputs

| Field | Default | Unit |
|---|---|---|
| `current_yield` | 6.00% | % |
| `duration` | 5.8 | years |
| `current_term_premium` | 0.81% | % |
| `fair_term_premium` | 1.00% | % |
| `default_rate` | 3.40% | % |
| `recovery_rate` | 55.0% | % |

### 8.3 Override paths

`bonds_em.<field>` — flat structure.

---

## 9. Bonds Inflation Linked

**Asset class identifier**: `inflation_linked`

**Regime-based**: USD base → US TIPS inputs and US macro; EUR base → EUR ILB inputs and Eurozone macro. No FX adjustment.

**Not offered in CHF base**: Switzerland has no domestic inflation-linked government bond market. In CHF base the engine omits this asset class from results entirely (9 assets instead of 10); calling its model directly with CHF raises an error, and the UI shows an explanatory notice instead of inputs.

### 9.1 Formula

This model does **not** use the §5 common framework. Its decomposition is:

```
# Real-side
real_carry          = current_real_yield
real_roll_return    = (current_real_term_premium / 10) × duration
expected_rtp_change = (fair_real_term_premium − current_real_term_premium) × reversion_fraction
                     where reversion_fraction = 1 − 0.97^120 ≈ 0.97414
real_valuation      = −duration × expected_rtp_change / horizon

real_return         = real_carry
                    + real_roll_return
                    + real_valuation
                    + liquidity_technical

# Inflation pass-through
inflation_indexation = inflation_forecast × inflation_beta

# Nominal
nominal_return = real_return + inflation_indexation − index_lag_drag

credit_loss = 0  (DM sovereign assumed default-free)
```

The component named `index_lag_drag` is **subtracted**; in the output it appears as a negative number (the engine writes `-abs(value)`).

### 9.2 Inputs

| Field | USD regime default | EUR regime default | Unit |
|---|---|---|---|
| `current_real_yield` | 2.10% | 0.75% | % |
| `duration` | 4.3 | 7.5 | years |
| `current_real_term_premium` | 0.80% | 0.15% | % |
| `fair_real_term_premium` | 0.80% | 0.10% | % |
| `inflation_beta` | 1.00 | 1.00 | unitless |
| `index_lag_drag` | 0.10% | 0.15% | % |
| `liquidity_technical` | 0.05% | 0.10% | % |

EUR regime values were not updated in Q2 2026 — they retain prior defaults.

### 9.3 Override paths

- USD regime: `inflation_linked.usd.<field>`
- EUR regime: `inflation_linked.eur.<field>`

---

## 10. Equity — Research Affiliates Model

**Asset class identifiers**: `equity_us`, `equity_europe`, `equity_japan`, `equity_em`

Computes **real return first**, then adds regional inflation. FX adjustment applied when local currency ≠ base.

### 10.1 Formula

```
# Dividend yield: taken as current value, no mean reversion
dividend_yield = input

# Real EPS growth: blended with regional, capped at global RGDP
country_weight  = 0.50
regional_weight = 0.50
blended_eps = country_weight  × real_eps_growth
            + regional_weight × regional_eps_growth

If global_rgdp is provided:
    real_eps_growth_capped = min(blended_eps, global_rgdp)
Else:
    real_eps_growth_capped = blended_eps

# Valuation change: CAEY mean reversion over 20 years
full_reversion_years = 20
reversion_speed (λ)  = input (default 1.0 = full reversion)

If current_caey > 0 AND reversion_speed > 0:
    caey_annual_change = (fair_caey / current_caey) ^ (λ / 20) − 1

    # Average year-on-year price change over 10-year horizon
    cumulative_valuation = 0
    caey = current_caey
    For year in 0..9:
        caey_next      = caey × (1 + caey_annual_change)
        year_valuation = caey / caey_next − 1
        cumulative_valuation += year_valuation
        caey = caey_next
    valuation_change = cumulative_valuation / 10
Else:
    valuation_change   = 0
    caey_annual_change = 0

# Total real return
E[Real Return]    = dividend_yield + real_eps_growth_capped + valuation_change

# Nominal return
E[Nominal Return] = E[Real Return] + regional_inflation_forecast
```

Because `caey_annual_change` is constant year-to-year, `year_valuation = 1/(1 + caey_annual_change) − 1` is constant too, so:

```
valuation_change = year_valuation
                 = 1/(1 + caey_annual_change) − 1
                 = −caey_annual_change / (1 + caey_annual_change)
```

### 10.2 Region → Macro Region Map

| Equity Region | Macro Region |
|---|---|
| `us` | `us` |
| `europe` | `eurozone` |
| `japan` | `japan` |
| `em` | `em` |

### 10.3 Inputs (Q2 2026)

| Field | US | Europe | Japan | EM | Unit |
|---|---|---|---|---|---|
| `dividend_yield` | 1.10% | 2.80% | 1.90% | 2.20% | % |
| `current_caey` | 2.50% | 4.40% | 3.70% | 3.80% | % |
| `fair_caey` | 4.30% | 4.30% | 3.70% | 5.80% | % |
| `real_eps_growth` (country) | 1.80% | 1.20% | 0.80% | 3.00% | % |
| `regional_eps_growth` | 1.60% | 1.60% | 1.60% | 2.80% | % |
| `reversion_speed` | 100% (= 1.0) | 100% | 100% | 100% | unitless |

### 10.4 Override paths

`equity_us.<field>`, `equity_europe.<field>`, `equity_japan.<field>`, `equity_em.<field>`.

---

## 11. Equity — Grinold-Kroner Model

Alternative equity model, toggled by `equity_model_type='gk'`. Same regional structure as RA, but different decomposition. Computes **nominal return directly**; real is back-computed.

### 11.1 Formula

```
dividend_yield        = input
net_buyback_yield     = input  (positive for buybacks, negative for net issuance)
margin_change         = input

# Revenue growth: auto-computed from macro unless explicitly overridden
If revenue_growth was set as an override:
    revenue_growth = override_value
Else:
    revenue_growth = regional_inflation
                   + regional_rgdp
                   + revenue_gdp_wedge

# Valuation change: P/E mean reversion over horizon (10 years)
If current_pe > 0 AND target_pe > 0:
    valuation_change = (target_pe / current_pe) ^ (1 / 10) − 1
Else:
    valuation_change = 0

# Total
E[Nominal Return] = dividend_yield
                  + net_buyback_yield
                  + revenue_growth
                  + margin_change
                  + valuation_change

# Real (back-computed)
E[Real Return]    = E[Nominal Return] − regional_inflation_forecast
```

The frontend default for `revenue_growth` is set equal to the macro-computed value so that, when the user has not touched it, the override-builder considers it "not different from default" and does not send it as an override — preserving the macro link in the engine.

### 11.2 Inputs (Q2 2026)

| Field | US | Europe | Japan | EM | Unit |
|---|---|---|---|---|---|
| `dividend_yield` | 1.10% | 2.80% | 1.90% | 2.20% | % |
| `net_buyback_yield` | 1.30% | 0.70% | 1.40% | −0.60% | % |
| `revenue_growth` (display) | 6.20% | 3.50% | 2.80% | 7.90% | % |
| `revenue_gdp_wedge` | 2.00% | 0.50% | 0.50% | 0.50% | % |
| `margin_change` | −0.50% | 0.00% | 0.30% | 0.00% | % |
| `current_pe` | 21.3 | 14.9 | 21.9 | 11.7 | ratio (x) |
| `target_pe` | 22.7 | 16.4 | 22.1 | 15.0 | ratio (x) |

Auto-computed `revenue_growth` values using new macro:
- US: 3.00 + 1.20 + 2.00 = 6.20%
- EZ: 2.00 + 1.00 + 0.50 = 3.50% (uses E[RGDP] 1.00, not the 0.9987 computed value)
- JP: 1.50 + 0.80 + 0.50 = 2.80%
- EM: 4.00 + 3.40 + 0.50 = 7.90%

In the engine these use the precise computed RGDP values (1.2003, 0.9987, 0.7987, 3.4021), giving tiny rounding differences.

### 11.3 Override paths

Same as RA: `equity_us.<field>`, etc. The toggle `equity_model_type` controls which fields are read.

---

## 12. Liquidity (Cash)

**Asset class identifier**: `liquidity`

```
E[Nominal Return] = E[T-Bill]_base-region
E[Real Return]    = E[Nominal] − E[Inflation]_base-region
```

No additional inputs. Uses the base-region macro forecasts directly. No FX adjustment.

### 12.1 Override paths

None. Adjust the underlying macro fields if needed.

---

## 13. Absolute Return (Hedge Funds)

**Asset class identifier**: `absolute_return`

Fama-French factor model with manager skill.

### 13.1 Formula

```
Factors: market, size, value, profitability, investment, momentum

# Market factor premium is computed live from the active equity model
# (RA or GK, US region)
us_equity_nominal_return = (computed in §10 or §11)

factor_premium[market] = us_equity_nominal_return − E[T-Bill]_base

# Other factor premia: 50% of historical (a discount for forward-looking estimates)
historical_factor_premia = {
    market:        0.05    (5.0%)   ← unused; market is dynamic above
    size:          0.02    (2.0%)
    value:         0.03    (3.0%)
    profitability: 0.025   (2.5%)
    investment:    0.025   (2.5%)
    momentum:      0.06    (6.0%)
}
historical_discount = 0.50

For factor in [size, value, profitability, investment, momentum]:
    factor_premium[factor] = historical_factor_premia[factor] × historical_discount

# Sum factor returns
factor_return = Σ (beta[factor] × factor_premium[factor]) for factor in [market, size, value, profitability, investment, momentum]

# Trading alpha
default_trading_alpha = historical_discount × 0.02 = 0.01   (1.0%, = 50% of 2% historical)
trading_alpha = input  (default 0.01)

# Total
E[Nominal Return] = E[T-Bill]_base + factor_return + trading_alpha
E[Real Return]    = E[Nominal] − E[Inflation]_base
```

No FX adjustment (uses base-currency T-Bill directly).

### 13.2 Inputs

| Field | Default | Unit |
|---|---|---|
| `beta_market` | 0.30 | unitless |
| `beta_size` | 0.10 | unitless |
| `beta_value` | 0.05 | unitless |
| `beta_profitability` | 0.05 | unitless |
| `beta_investment` | 0.05 | unitless |
| `beta_momentum` | 0.10 | unitless |
| `trading_alpha` | 1.00% | % |

### 13.3 Override paths

`absolute_return.<field>`.

---

## 14. Default Inputs (Q2 2026)

Complete dump, percentage points unless otherwise noted.

### 14.1 Macro defaults

| Region | curr_inflation | LT_inflation | curr_tbill | pop_growth | productivity | my_ratio | country_factor |
|---|---|---|---|---|---|---|---|
| US | 3.00 | 3.00 | 3.60 | 0.40 | 1.20 | 2.1 | 0.00 |
| Eurozone | 2.00 | 2.00 | 2.10 | 0.10 | 1.49 | 2.3 | −0.20 |
| Japan | 1.50 | 1.50 | 1.62 | −0.20 | 1.59 | 2.3 | −0.50 |
| EM | 4.00 | 4.00 | 4.00 | 1.00 | 2.44 | 1.5 | −3.40 |
| Switzerland | 0.50 | 1.00 | 0.00 | 0.70 | 1.00 | 2.2 | −1.20 |

Direct-forecast display defaults (what the UI shows in the "Direct Forecast Overrides" fields, equal to the computed building-block forecasts):

| Region | inflation_forecast | rgdp_growth | tbill_forecast |
|---|---|---|---|
| US | 3.00 | 1.20 | 4.02 |
| Eurozone | 2.00 | 1.00 | 2.59 |
| Japan | 1.50 | 0.80 | 1.75 |
| EM | 4.00 | 3.40 | 4.00 |
| Switzerland | 0.85 | 1.20 | 0.60 |

### 14.2 Bonds Global Government (regime-based)

| Field | USD regime | EUR regime | CHF regime |
|---|---|---|---|
| `current_yield` | 4.60 | 3.00 | 0.40 |
| `duration` | 8.0 | 7.5 | 9.0 |
| `current_term_premium` | 0.81 | 0.40 | −0.20 |
| `fair_term_premium` | 1.00 | 0.50 | 0.20 |

### 14.3 Bonds High Yield

| Field | Default |
|---|---|
| `current_yield` | 7.10 |
| `duration` | 3.0 |
| `current_term_premium` | 1.00 |
| `fair_term_premium` | 1.00 |
| `credit_spread` | 2.60 |
| `fair_credit_spread` | 4.00 |
| `default_rate` | 3.40 |
| `recovery_rate` | 40.0 |

### 14.4 Bonds EM Hard Currency

| Field | Default |
|---|---|
| `current_yield` | 6.00 |
| `duration` | 5.8 |
| `current_term_premium` | 0.81 |
| `fair_term_premium` | 1.00 |
| `default_rate` | 3.40 |
| `recovery_rate` | 55.0 |

### 14.5 Bonds Inflation Linked (regime-based)

| Field | USD regime (TIPS) | EUR regime |
|---|---|---|
| `current_real_yield` | 2.10 | 0.75 |
| `duration` | 4.3 | 7.5 |
| `current_real_term_premium` | 0.80 | 0.15 |
| `fair_real_term_premium` | 0.80 | 0.10 |
| `inflation_beta` | 1.00 | 1.00 |
| `index_lag_drag` | 0.10 | 0.15 |
| `liquidity_technical` | 0.05 | 0.10 |

### 14.6 Equity RA model

| Field | US | Europe | Japan | EM |
|---|---|---|---|---|
| `dividend_yield` | 1.10 | 2.80 | 1.90 | 2.20 |
| `current_caey` | 2.50 | 4.40 | 3.70 | 3.80 |
| `fair_caey` | 4.30 | 4.30 | 3.70 | 5.80 |
| `real_eps_growth` (country) | 1.80 | 1.20 | 0.80 | 3.00 |
| `regional_eps_growth` | 1.60 | 1.60 | 1.60 | 2.80 |
| `reversion_speed` | 100 | 100 | 100 | 100 |

### 14.7 Equity GK model

| Field | US | Europe | Japan | EM |
|---|---|---|---|---|
| `dividend_yield` | 1.10 | 2.80 | 1.90 | 2.20 |
| `net_buyback_yield` | 1.30 | 0.70 | 1.40 | −0.60 |
| `revenue_growth` (display) | 6.20 | 3.50 | 2.80 | 7.90 |
| `revenue_gdp_wedge` | 2.00 | 0.50 | 0.50 | 0.50 |
| `margin_change` | −0.50 | 0.00 | 0.30 | 0.00 |
| `current_pe` (ratio) | 21.3 | 14.9 | 21.9 | 11.7 |
| `target_pe` (ratio) | 22.7 | 16.4 | 22.1 | 15.0 |

### 14.8 Absolute Return

| Field | Default |
|---|---|
| `beta_market` | 0.30 |
| `beta_size` | 0.10 |
| `beta_value` | 0.05 |
| `beta_profitability` | 0.05 |
| `beta_investment` | 0.05 |
| `beta_momentum` | 0.10 |
| `trading_alpha` | 1.00 |

### 14.9 Volatilities (used for the risk-return chart, not the return calc)

| Asset | Volatility |
|---|---|
| Liquidity | 1.0% |
| Bonds Global | 6.0% |
| Bonds HY | 10.0% |
| Bonds EM HC | 12.0% |
| Bonds Inflation Linked | 7.0% |
| Equity US | 16.0% |
| Equity Europe | 18.0% |
| Equity Japan | 18.0% |
| Equity EM | 24.0% |
| Absolute Return | 8.0% |

### 14.10 Constants

| Constant | Value | Source |
|---|---|---|
| `rate_floor` (T-Bill floor) | −0.75% | TBILL_PARAMS, MEAN_REVERSION_PARAMS |
| Inflation `current_weight` | 0.30 | INFLATION_PARAMS |
| Inflation `long_term_weight` | 0.70 | INFLATION_PARAMS |
| T-Bill `current_weight` | 0.30 | TBILL_PARAMS |
| T-Bill `long_term_weight` | 0.70 | TBILL_PARAMS |
| Bond TP reversion_speed | 1.0 | `abs(MEAN_REVERSION_PARAMS['bond_term_premium_bounds'][0])` |
| Bond valuation monthly reversion | 0.03 | hardcoded in bonds.py:222 |
| HY spread reversion_fraction | 0.5 | hardcoded in bonds.py:460 |
| EM `em_spread` | 2.00% | hardcoded in bonds.py:558 |
| FX `CARRY_WEIGHT` | 0.30 | currency.py:21 |
| FX `PPP_WEIGHT` | 0.70 | currency.py:22 |
| Equity `country_weight` | 0.50 | EQUITY_PARAMS |
| Equity `regional_weight` | 0.50 | EQUITY_PARAMS |
| Equity `valuation_reversion_years` | 20 | EQUITY_PARAMS |
| GK Equity `pe_reversion_years` | 10 | EQUITY_PARAMS_GK |
| Sigmoid midpoint (MY ratio) | 2.0 | utils/ewma.py:172 |
| Sigmoid steepness | 2.0 | utils/ewma.py:172 |
| Sigmoid output scale | 0.02 | utils/ewma.py:196 |
| HF `historical_discount` | 0.50 | HEDGE_FUND_PARAMS |
| Global RGDP weights | 26/15/5/40 | macro.py:351 |

### 14.11 Adjustment defaults (rarely overridden)

| Region | rgdp_adjustment | inflation_adjustment |
|---|---|---|
| US | −0.30% | 0.00% |
| Eurozone | −0.30% | 0.00% |
| Japan | −0.30% | 0.00% |
| EM | −0.50% | 0.00% |

---

## 15. Override System

Users can override any input. The override structure follows the asset-class hierarchy. The frontend sends only the fields that differ from defaults.

### 15.1 Override payload structure

```json
{
  "macro": {
    "us":       {"<field>": value},
    "eurozone": {"<field>": value},
    "japan":    {"<field>": value},
    "em":       {"<field>": value}
  },
  "bonds_global": {
    "usd": {"<field>": value},
    "eur": {"<field>": value}
  },
  "bonds_hy":  {"<field>": value},
  "bonds_em":  {"<field>": value},
  "inflation_linked": {
    "usd": {"<field>": value},
    "eur": {"<field>": value}
  },
  "equity_us":     {"<field>": value},
  "equity_europe": {"<field>": value},
  "equity_japan":  {"<field>": value},
  "equity_em":     {"<field>": value},
  "absolute_return": {"<field>": value}
}
```

All percentage values are sent as **decimals** (frontend divides by 100 before sending). Unitless fields (durations, P/Es, betas, MY ratio, inflation_beta) sent as-is. `reversion_speed` is a special case — the UI stores it as a percentage (100 = 100%) and the frontend divides by 100 like other percentages, so the engine receives 1.0.

### 15.2 Direct vs Building-block macro overrides

Macro has two layers:
- **Direct forecast fields**: `inflation_forecast`, `rgdp_growth`, `tbill_forecast`. If set, these short-circuit the building-block computation entirely.
- **Building blocks**: everything else (`population_growth`, `productivity_growth`, `my_ratio`, `current_headline_inflation`, `long_term_inflation`, `current_tbill`, `country_factor`). If set, the corresponding forecast is **recomputed** from the new block values.

The frontend's "Direct Forecast Overrides" UI section displays the **computed** values when nothing is dirty. If the user touches a building block, the displayed forecast auto-syncs to the new computed value (via `useEffect` in `MacroInputPanel.tsx`).

If the user explicitly types into a Direct Forecast field, that value becomes a **dirty override** and stops syncing. From then on it overrides the building-block computation.

### 15.3 Override-source provenance

The Python `InputSource` enum (in `inputs/overrides.py:17-21`) has **three** values:
- `default` — value came from `DEFAULT_*` configs
- `override` — user explicitly set this value
- `computed` — value was derived (e.g., E[T-Bill] is always computed unless directly overridden)

A fourth tag, `affected_by_override`, is **not** part of the enum — it is a free-standing string generated in `main.py` (`_get_macro_sources`, `_build_macro_dependencies`) only for macro-dependency tracking. It marks a value that wasn't itself overridden but was derived from an overridden upstream input.

---

## 16. Worked Examples

All examples use Q2 2026 defaults and USD base currency unless noted.

### 16.1 Example 1 — US E[RGDP], E[Inflation], E[T-Bill]

Building blocks: `pop=0.40%`, `prod=1.20%`, `my_ratio=2.1`, `curr_inf=3.00%`, `LT_inf=3.00%`, `curr_tb=3.60%`, `country_factor=0.00%`.

```
# Sigmoid demographic effect
z       = 2.0 × (2.0 − 2.1) = −0.2
sig     = 1 / (1 + exp(−z)) = 1 / (1 + exp(0.2)) = 1 / 1.22140 = 0.45017
demo    = (0.45017 − 0.5) × 0.02 = −0.04983 × 0.02 = −0.0009967  (−0.0997%)

# RGDP
output_per_capita = 1.20 + (−0.0997) + (−0.30) = 0.8003%
E[RGDP] = 0.4 + 0.8003 = 1.2003%   ✓

# Inflation
E[Inflation] = 0.30 × 3.00 + 0.70 × 3.00 = 3.00%   ✓

# T-Bill
LT_TB  = max(−0.75, 0.00 + 1.2003 + 3.00) = 4.2003%
E[T-Bill] = 0.30 × 3.60 + 0.70 × 4.2003 = 1.080 + 2.9402 = 4.0202%   ✓
```

### 16.2 Example 2 — Global RGDP

```
weights = {us: 0.26, eurozone: 0.15, japan: 0.05, em: 0.40}
total   = 0.86

us_contrib = (0.26 / 0.86) × 1.2003 = 0.30233 × 1.2003 = 0.36289
ez_contrib = (0.15 / 0.86) × 0.9987 = 0.17442 × 0.9987 = 0.17419
jp_contrib = (0.05 / 0.86) × 0.7987 = 0.05814 × 0.7987 = 0.04643
em_contrib = (0.40 / 0.86) × 3.4021 = 0.46512 × 3.4021 = 1.58234

Global RGDP = 0.36289 + 0.17419 + 0.04643 + 1.58234 = 2.16585%  ≈ 2.1659%   ✓
```

### 16.3 Example 3 — USD Bonds Global Government (USD base)

Regime: USD. Inputs: `current_yield=4.60%`, `duration=8.0`, `current_TP=0.81%`, `fair_TP=1.00%`. Macro: US E[T-Bill]=4.0202%, US E[Inflation]=3.00%.

```
# Average yield over horizon (reversion_speed=1.0 → closed form)
avg_TP    = (0.81 + 1.00 × 9) / 10 = (0.81 + 9.00) / 10 = 0.981%
avg_yield = 4.0202 + 0.981 = 5.0012%   ✓

# Roll return (uses current_TP, not avg)
roll = (0.81 / 10) × 8.0 = 0.0081 × 8.0 = 0.0648 = 0.648%   ✓

# Valuation return (TP rising → drag)
reversion_fraction   = 1 − 0.97^120 = 1 − 0.02586 = 0.97414
expected_tp_change   = (1.00 − 0.81) × 0.97414 = 0.19 × 0.97414 = 0.18509%
valuation_return     = −8.0 × 0.18509 / 10 = −0.14807%   ✓ (engine: −0.1481)

# Credit loss (sovereign, default-free)
credit_loss = 0

# Totals
E[Nominal] = 5.0012 + 0.648 + (−0.1481) − 0 = 5.5011%   ✓ (engine: 5.5012)
E[Real]    = 5.5011 − 3.00 = 2.5011%   ✓ (engine: 2.5012)
```

### 16.4 Example 4 — Bonds High Yield (USD base)

Inputs: `current_yield=7.10%`, `duration=3.0`, `current_TP=1.00%`, `fair_TP=1.00%`, `credit_spread=2.60%`, `fair_credit_spread=4.00%`, `default_rate=3.40%`, `recovery_rate=40%`. US macro: E[T-Bill]=4.0202%, E[Inflation]=3.00%.

```
# Step 1: standard bond framework
avg_TP    = (1.00 + 1.00 × 9) / 10 = 1.00%
avg_yield = 4.0202 + 1.00 = 5.0202%   ✓

roll = (1.00 / 10) × 3.0 = 0.30%   ✓

reversion_fraction = 0.97414
tp_change          = (1.00 − 1.00) × 0.97414 = 0
tp_valuation       = −3.0 × 0 / 10 = 0%

credit_loss = 3.40 × (1 − 0.40) = 3.40 × 0.60 = 2.04%   ✓

base_nominal = 5.0202 + 0.30 + 0 − 2.04 = 3.2802%

# Step 2: HY-specific spread valuation add-on
spread_change    = (4.00 − 2.60) × 0.5 = 1.40 × 0.5 = 0.70%
spread_valuation = −3.0 × 0.70 / 10 = −0.21%   ✓

E[Nominal] = 3.2802 + (−0.21) = 3.0702%   ✓
E[Real]    = 3.0702 − 3.00 = 0.0702%   ✓
```

In the breakdown output, `valuation` is the sum of `tp_valuation + spread_valuation = 0 + (−0.21) = −0.21%`.

### 16.5 Example 5 — Bonds EM Hard Currency (USD base)

Inputs: `current_yield=6.00%`, `duration=5.8`, `current_TP=0.81%`, `fair_TP=1.00%`, `default_rate=3.40%`, `recovery_rate=55%`. US macro: E[T-Bill]=4.0202%, E[Inflation]=3.00%.

```
# EM-specific base rate
em_spread          = 2.00% (hardcoded)
em_tbill_forecast  = 4.0202 + 2.00 = 6.0202%

# Standard bond framework with em_tbill as tbill
avg_TP    = (0.81 + 1.00 × 9) / 10 = 0.981%
avg_yield = 6.0202 + 0.981 = 7.0012%   ✓

roll = (0.81 / 10) × 5.8 = 0.4698%   ✓

reversion_fraction = 0.97414
tp_change          = (1.00 − 0.81) × 0.97414 = 0.18509%
tp_valuation       = −5.8 × 0.18509 / 10 = −0.10735%   ✓ (engine: −0.1074)

credit_loss = 3.40 × (1 − 0.55) = 3.40 × 0.45 = 1.53%   ✓

E[Nominal] = 7.0012 + 0.4698 + (−0.1074) − 1.53 = 5.8337%   ✓
E[Real]    = 5.8337 − 3.00 = 2.8337%   ✓
```

### 16.6 Example 6 — Bonds Inflation Linked USD (USD base, TIPS)

Inputs: `current_real_yield=2.10%`, `duration=4.3`, `current_real_TP=0.80%`, `fair_real_TP=0.80%`, `inflation_beta=1.00`, `index_lag_drag=0.10%`, `liquidity_technical=0.05%`. US E[Inflation]=3.00%.

```
real_carry      = 2.10%
real_roll       = (0.80 / 10) × 4.3 = 0.344%   ✓

reversion_fraction = 0.97414
expected_rtp_change = (0.80 − 0.80) × 0.97414 = 0
real_valuation     = −4.3 × 0 / 10 = 0%

inflation_indexation = 3.00 × 1.00 = 3.00%
index_lag_drag       = 0.10%   (subtracted)
liquidity_technical  = 0.05%

real_return    = 2.10 + 0.344 + 0 + 0.05 = 2.494%   ✓
E[Nominal]     = 2.494 + 3.00 − 0.10 = 5.394%   ✓
```

### 16.7 Example 7 — Equity US (RA model, USD base)

Inputs: `dividend_yield=1.10%`, `current_caey=2.50%`, `fair_caey=4.30%`, `country_eps_growth=1.80%`, `regional_eps_growth=1.60%`, `reversion_speed=1.0`. US E[Inflation]=3.00%. Global RGDP=2.1659%.

```
# Dividend
DY = 1.10%

# EPS growth (blended, capped at global RGDP)
blended = 0.50 × 1.80 + 0.50 × 1.60 = 0.90 + 0.80 = 1.70%
capped  = min(1.70, 2.1659) = 1.70%   (not capped)
real_eps_growth = 1.70%   ✓

# Valuation change (CAEY mean reversion)
caey_annual_change = (4.30 / 2.50)^(1.0 / 20) − 1
                   = 1.72^0.05 − 1

# ln(1.72) = 0.54232
# 0.05 × 0.54232 = 0.02712
# exp(0.02712) = 1.02749
# 1.02749 − 1 = 0.02749 = 2.749%

# Year-on-year price change (constant when annual_change is constant):
year_val = 1 / 1.02749 − 1 = 0.97324 − 1 = −0.02676 = −2.676%
valuation_change = −2.676%   ✓ (engine: −2.6752)

# Totals
E[Real]    = 1.10 + 1.70 + (−2.676) = 0.1240%   ✓ (engine: 0.1248)
E[Nominal] = 0.124 + 3.00 = 3.1240%   ✓ (engine: 3.1248)
```

### 16.8 Example 8 — Equity Europe (RA model, USD base, with FX)

Inputs: `DY=2.80%`, `current_caey=4.40%`, `fair_caey=4.30%`, `country_eps=1.20%`, `regional_eps=1.60%`. EZ E[Inflation]=2.00%. Global RGDP=2.1659%.

```
# Local-currency calc (EUR)
DY = 2.80%
blended = 0.50 × 1.20 + 0.50 × 1.60 = 1.40%
capped  = min(1.40, 2.1659) = 1.40%

caey_annual_change = (4.30 / 4.40)^(1/20) − 1
                   = 0.9773^0.05 − 1
# ln(0.9773) = −0.022965
# 0.05 × −0.022965 = −0.001148
# exp(−0.001148) = 0.998853
# − 1 = −0.001147 = −0.1147%

year_val = 1 / 0.998853 − 1 = 0.001149 = +0.1149%
valuation_change = +0.1149%   ✓ (engine: +0.1150)

# Local-currency total
E[Real]_local    = 2.80 + 1.40 + 0.1149 = 4.3149%
E[Nominal]_local = 4.3149 + 2.00 = 6.3149%

# FX adjustment (USD base, EUR asset)
fx_change = 0.30 × (4.0202 − 2.5891) + 0.70 × (3.00 − 2.00)
          = 0.30 × 1.4311 + 0.70 × 1.0000
          = 0.4293 + 0.7000 = 1.1293%   ✓

# USD-base total
E[Nominal] = 6.3149 + 1.1293 = 7.4442%   ✓ (engine: 7.4444)
E[Real]    = 4.3149 + 1.1293 = 5.4442%   ✓ (engine: 5.4444)
```

### 16.9 Example 9 — Equity EM (RA model, EPS cap kicks in)

Inputs: `DY=2.20%`, `current_caey=3.80%`, `fair_caey=5.80%`, `country_eps=3.00%`, `regional_eps=2.80%`. EM E[Inflation]=4.00%. Global RGDP=2.1659%.

```
# EPS growth (blended → capped)
blended = 0.50 × 3.00 + 0.50 × 2.80 = 2.90%
capped  = min(2.90, 2.1659) = 2.1659%   ← cap applied
real_eps_growth = 2.1659%   ✓

# Valuation: CAEY rising → negative
caey_annual_change = (5.80 / 3.80)^(1/20) − 1
                   = 1.5263^0.05 − 1
# ln(1.5263) = 0.4231
# 0.05 × 0.4231 = 0.02116
# exp(0.02116) = 1.02138
# − 1 = 0.02138 = 2.138%

year_val = 1 / 1.02138 − 1 = 0.97907 − 1 = −0.02093 = −2.093%
valuation_change = −2.093%   ✓ (engine: −2.0921)

# Local-currency total
E[Real]_local    = 2.20 + 2.1659 + (−2.0921) = 2.2738%
E[Nominal]_local = 2.2738 + 4.00 = 6.2738%

# FX (USD base, EM asset)
fx_change = 0.30 × (4.0202 − 4.0015) + 0.70 × (3.00 − 4.00)
          = 0.30 × 0.0187 + 0.70 × −1.00
          = 0.00561 − 0.700 = −0.6944%   ✓

# USD-base total
E[Nominal] = 6.2738 + (−0.6944) = 5.5794%   ✓
E[Real]    = 2.2738 + (−0.6944) = 1.5794%   ✓
```

### 16.10 Example 10 — Equity US (GK model, USD base)

Inputs: `DY=1.10%`, `net_buyback=1.30%`, `revenue_gdp_wedge=2.00%`, `margin_change=−0.50%`, `current_pe=21.3`, `target_pe=22.7`. US macro: E[Inflation]=3.00%, E[RGDP]=1.2003%.

```
# Revenue growth (auto-computed; default value not sent as override)
revenue_growth = 3.00 + 1.2003 + 2.00 = 6.2003%

# Valuation
valuation_change = (22.7 / 21.3)^(1/10) − 1
# 22.7/21.3 = 1.06573
# ln(1.06573) = 0.06367
# 0.06367/10 = 0.006367
# exp(0.006367) = 1.006387
# − 1 = 0.006387 = 0.6387%

# Total
E[Nominal] = 1.10 + 1.30 + 6.2003 + (−0.50) + 0.6387 = 8.739%   ✓ (engine: 8.74)
E[Real]    = 8.739 − 3.00 = 5.739%   ✓
```

### 16.11 Example 11 — Liquidity (USD base)

```
E[Nominal] = E[T-Bill]_us = 4.0202%
E[Real]    = 4.0202 − 3.00 = 1.0202%   ✓
```

### 16.11b Example — Swiss macro chain + a CHF-base asset

Building blocks: `pop=0.70%`, `prod=1.00%`, `my_ratio=2.2`, `curr_inf=0.50%`, `LT_inf=1.00%`, `curr_tb=0.00%`, `country_factor=−1.20%`.

```
# Demographics (MY 2.2)
z    = 2.0 × (2.0 − 2.2) = −0.4
sig  = 1 / (1 + exp(0.4)) = 0.40131
demo = (0.40131 − 0.5) × 0.02 = −0.19737% 

# RGDP
output_per_capita = 1.00 + (−0.1974) + (−0.30) = 0.5026%
E[RGDP] = 0.70 + 0.5026 = 1.2026%   ✓

# Inflation
E[Inflation] = 0.30 × 0.50 + 0.70 × 1.00 = 0.85%   ✓

# T-Bill (safe-haven country factor)
LT_TB = max(−0.75, −1.20 + 1.2026 + 0.85) = 0.8526%
E[T-Bill] = 0.30 × 0.00 + 0.70 × 0.8526 = 0.5968%   ✓

# Bonds Global (CHF regime): yield 0.40%, dur 9.0, TP −0.20 → 0.20
avg_TP    = (−0.20 + 0.20 × 9) / 10 = 0.16%
avg_yield = 0.5968 + 0.16 = 0.7568%
roll      = (−0.20 / 10) × 9.0 = −0.18%
valuation = −9.0 × (0.20 − (−0.20)) × 0.97414 / 10 = −0.3507%
E[Nominal] = 0.7568 − 0.18 − 0.3507 = 0.2261%   ✓ (engine: 0.2261)
E[Real]    = 0.2261 − 0.85 = −0.6239%   ✓

# Bonds HY in CHF base: US-native calc 3.0702% (Example 4) + CHF→USD fx −2.5320%
E[Nominal] = 3.0702 − 2.5320 = 0.5382%   ✓ (engine: 0.5382)
```

Note: Bonds Inflation Linked is omitted in CHF base (no Swiss linker market) — CHF results contain 9 asset classes.

### 16.12 Example 12 — Absolute Return (USD base, GK equity active)

Inputs: betas `(market 0.30, size 0.10, value 0.05, profitability 0.05, investment 0.05, momentum 0.10)`, `trading_alpha=1.00%`.

```
# Market premium (live from US equity in active model — GK here)
# Use the precise engine value, not Example 10's rounded display
us_equity_nominal = 8.7389% (engine value; Example 10 displays it as 8.74)
market_premium    = 8.7389 − 4.0202 = 4.7187%

# Other premia (50% of historical)
size_prem  = 2.00 × 0.5 = 1.00%
val_prem   = 3.00 × 0.5 = 1.50%
prof_prem  = 2.50 × 0.5 = 1.25%
inv_prem   = 2.50 × 0.5 = 1.25%
mom_prem   = 6.00 × 0.5 = 3.00%

# Factor returns
contrib_market = 0.30 × 4.7187 = 1.4156
contrib_size   = 0.10 × 1.00   = 0.1000
contrib_value  = 0.05 × 1.50   = 0.0750
contrib_prof   = 0.05 × 1.25   = 0.0625
contrib_inv    = 0.05 × 1.25   = 0.0625
contrib_mom    = 0.10 × 3.00   = 0.3000

factor_return = 1.4156 + 0.1000 + 0.0750 + 0.0625 + 0.0625 + 0.3000 = 2.0156%

# Total (GK active)
E[Nominal] = 4.0202 + 2.0156 + 1.00 = 7.0358%   ✓ (engine: 7.0358)
E[Real]    = 7.0358 − 3.00 = 4.0358%            ✓ (engine: 4.0358)
```

(If you build the spreadsheet using Example 10's rounded `8.74%`, you will get `factor_return ≈ 2.0159%` and `E[Nominal] ≈ 7.0361%` — a 3bp drift from the engine. Use full-precision US equity in this chain.)

(Note: with the **RA** equity model active, US equity nominal is 3.1240%, market_premium becomes negative −0.8962%, and factor_return collapses to a smaller number, ~0.33%. The engine output for default RA-mode shows `factor_return: +0.3314`. This is why Abs Return differs significantly between RA and GK toggles.)

```
# With RA active (engine default test):
factor_return = 0.3314%
E[Nominal]    = 4.0202 + 0.3314 + 1.00 = 5.3516%   ✓
E[Real]       = 5.3516 − 3.00 = 2.3516%   ✓
```

---

## 17. Spreadsheet Recreation Guide

Suggested sheet layout, one logical block per worksheet:

### 17.1 Sheet 1: Macro Inputs

Rows: 7 building-block fields (`pop_growth`, `productivity_growth`, `my_ratio`, `current_headline_inflation`, `long_term_inflation`, `current_tbill`, `country_factor`) plus 4 region columns. Plus a `rgdp_adjustment` row (default −0.30% / −0.50%).

### 17.2 Sheet 2: Macro Computed

For each region:
- `demographic_effect` = `(1 / (1 + EXP(-(2*(2-my_ratio)))) - 0.5) * 0.02`
- `output_per_capita`  = `productivity + demographic_effect + adjustment`
- `E[RGDP]`            = `output_per_capita + pop_growth`
- `E[Inflation]`       = `0.3*curr_inf + 0.7*LT_inf`
- `LT_TB`              = `MAX(-0.0075, country_factor + E[RGDP] + E[Inflation])`
- `E[T-Bill]`          = `0.3*curr_tb + 0.7*LT_TB`

Plus a `Global RGDP` cell:
`= (0.26*E[RGDP]_us + 0.15*E[RGDP]_ez + 0.05*E[RGDP]_jp + 0.40*E[RGDP]_em) / 0.86`

### 17.3 Sheet 3: FX Adjustment

For each base/foreign pair, columns:
- `home_TB`, `foreign_TB`, `home_inf`, `foreign_inf`
- `carry`           = `home_TB - foreign_TB`
- `ppp`             = `home_inf - foreign_inf`
- `fx_change`       = `0.3*carry + 0.7*ppp`

You only need the pairs: USD→EUR, USD→JPY, USD→EM, EUR→USD, EUR→JPY, EUR→EM.

### 17.4 Sheet 4: Bond Common Helpers

A reusable helper sheet with the bond framework as named formulas:
- `avg_TP`   = `(current_TP + fair_TP*9)/10`
- `avg_yield` = `tbill_forecast + avg_TP`
- `roll`     = `(current_TP/10) * duration`
- `rev_frac` = `1 - 0.97^120` (constant ≈ 0.97414)
- `tp_change` = `(fair_TP - current_TP) * rev_frac`
- `valuation` = `-duration * tp_change / 10`

### 17.5 Sheet 5: Bonds Global (regime selector)

Row 1: dropdown for base currency (USD / EUR). Use `INDIRECT` or `IF()` to pull from the right regime block. Or use two parallel blocks (USD and EUR) and `IF(base="EUR", eur_block, usd_block)`.

### 17.6 Sheet 6: Bonds HY

All HY-specific. Add:
- `tp_valuation` (= valuation from sheet 4 helpers)
- `spread_valuation` = `-duration * (fair_spread - current_spread) * 0.5 / 10`
- `total_valuation` = `tp_valuation + spread_valuation`
- `credit_loss` = `default_rate * (1 - recovery_rate)`

### 17.7 Sheet 7: Bonds EM HC

Same as Sheet 6 but no spread_valuation. **Important**: use `em_tbill_forecast = US_E[T-Bill] + 0.02` as the "tbill" input to the avg_yield formula.

### 17.8 Sheet 8: Bonds Inflation Linked (regime selector)

Same pattern as Sheet 5. Plus inflation-pass-through:
- `inflation_indexation` = `inflation_forecast * inflation_beta`
- `nominal` = `real_return + inflation_indexation - index_lag_drag`

### 17.9 Sheet 9: Equity RA (4 regions)

For each region:
- `blended_eps`    = `0.5*country_eps + 0.5*regional_eps`
- `capped_eps`     = `MIN(blended_eps, Global_RGDP)`
- `caey_annual`    = `IF(AND(current_caey>0, reversion_speed>0), (fair_caey/current_caey)^(reversion_speed/20) - 1, 0)`
- `valuation`      = `IF(AND(current_caey>0, reversion_speed>0), 1/(1+caey_annual) - 1, 0)`   (closed-form; same as engine's loop)
- `real_return`    = `DY + capped_eps + valuation`
- `nominal_return` = `real_return + regional_inflation`

### 17.10 Sheet 10: Equity GK (4 regions)

For each region:
- `revenue_growth` = `regional_inflation + regional_rgdp + wedge`
- `valuation`      = `(target_pe/current_pe)^(1/10) - 1`
- `nominal`        = `DY + buyback + revenue_growth + margin + valuation`
- `real`           = `nominal - regional_inflation`

### 17.11 Sheet 11: Liquidity, Abs Return

Trivial — pull from macro/FX/equity sheets.

For Abs Return:
- `market_prem` = `US_equity_nominal - US_E[TBill]`
- Other premia: lookup table
- `factor_return` = SUMPRODUCT of betas × premia
- `nominal` = `base_TB + factor_return + trading_alpha`

### 17.12 Sheet 12: FX Application

For each asset, look up its local currency, look up the corresponding `fx_change` from Sheet 3, add to the local-currency return.

### 17.13 Sheet 13: Final Output

Summary table:
| Asset | Local Return | FX Adj | Nominal (base) | Real (base) |

---

## 18. Source-File Reference

If a discrepancy with a spreadsheet is found, the engine is the source of truth. Files to consult:

| File | Purpose |
|---|---|
| `ra_stress_tool/config.py` | All hardcoded defaults (decimals), constants, asset→currency map |
| `ra_stress_tool/models/macro.py` | RGDP, Inflation, T-Bill, Global RGDP, sigmoid demographic |
| `ra_stress_tool/models/bonds.py` | BondModel base, GovernmentBondModel (regime-aware), HighYieldBondModel, EMBondModel, InflationLinkedBondModel |
| `ra_stress_tool/models/equities.py` | EquityModel (RA), EquityModelGK |
| `ra_stress_tool/models/alternatives.py` | HedgeFundModel |
| `ra_stress_tool/models/currency.py` | FXModel — carry + PPP formula |
| `ra_stress_tool/main.py` | `CMEEngine` orchestration, FX application, macro/asset dispatch |
| `ra_stress_tool/utils/ewma.py` | Sigmoid function, EWMA utilities |
| `ra_stress_tool/inputs/overrides.py` | OverrideManager, TrackedValue, nested-dict merge |
| `ra_stress_tool/inputs/defaults.py` | DefaultInputs class, GK overlay |
| `api/routes/defaults.py` | `INPUT_DEFAULTS` and `INPUT_DEFAULTS_GK_EQUITY` (percentage-point form) |
| `api/routes/calculate.py` | API entry point — `/api/calculate/full` |
| `web/lib/constants.ts` | Frontend `DEFAULT_INPUTS` and `DEFAULT_INPUTS_GK_EQUITY` |
| `web/lib/types.ts` | Type definitions (override structure, regime types) |
| `web/lib/formulas.ts` | Formula display strings shown in the UI |
| `web/stores/inputStore.ts` | Override builder (frontend → backend payload conversion) |

### 18.1 Verifying the engine

The engine can be exercised standalone:

```python
from ra_stress_tool.main import CMEEngine

# USD base, RA equity model
engine = CMEEngine(base_currency='usd', equity_model_type='ra')
results = engine.compute_all_returns()

for key, asset in results.results.items():
    print(f"{asset.asset_class}: nominal={asset.expected_return_nominal*100:.4f}%  real={asset.expected_return_real*100:.4f}%")
    for c, v in asset.components.items():
        print(f"  {c}: {v*100:+.4f}%")
```

Toggle `base_currency='eur'` or `equity_model_type='gk'` to verify other modes.

### 18.2 Known engine-vs-spreadsheet rounding sources

- `caey_annual_change` uses fractional exponents (`^0.05`) — spreadsheets and Python `**` agree to ~1e-15 precision but display rounding may show 0.01% drift.
- EM RGDP-cap value: spreadsheet computes Global RGDP independently per row, so confirm you're reusing the same global value (not recomputing) for the EM EPS cap.
- HY `valuation` in the engine's breakdown is `tp_valuation + spread_valuation` summed under one key — a spreadsheet should show them separately or sum to match.
- Absolute Return depends on the **active** equity model — the engine's "factor_return" output will differ depending on the `equity_model_type` toggle.

---

*Document generated for Q2 2026 default snapshot. Last update: commit `f1dd905`.*
