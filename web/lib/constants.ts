/**
 * Default values and constants for the Parkview CMA Tool
 *
 * These match the INPUT_DEFAULTS in app.py and api/routes/defaults.py
 * Values are in percentage points (e.g., 2.29 means 2.29%)
 */

import type { AllInputs, EquityInputsGK, EquityRegion } from './types';

export const DEFAULT_INPUTS: AllInputs = {
  macro: {
    us: {
      // Q2 2026 defaults — direct forecasts back-solved through building blocks
      // E[RGDP] = Output-per-Capita + Population = (Prod + Demo + Adj) + Pop
      // E[Inflation] = 30% × Current + 70% × Long-Term
      // E[T-Bill] = 30% × Current + 70% × max(-0.75%, CF + GDP + Inflation)
      inflation_forecast: 3.00,
      rgdp_growth: 1.20,
      tbill_forecast: 4.02,         // 0.3*3.60 + 0.7*4.20
      // Building blocks
      population_growth: 0.40,
      productivity_growth: 1.20,
      my_ratio: 2.1,
      current_headline_inflation: 3.00,
      long_term_inflation: 3.00,
      current_tbill: 3.60,
      country_factor: 0.00,
    },
    eurozone: {
      inflation_forecast: 2.00,
      rgdp_growth: 1.00,
      tbill_forecast: 2.59,         // 0.3*2.10 + 0.7*2.80
      population_growth: 0.10,
      productivity_growth: 1.49,
      my_ratio: 2.3,
      current_headline_inflation: 2.00,
      long_term_inflation: 2.00,
      current_tbill: 2.10,
      country_factor: -0.20,
    },
    japan: {
      inflation_forecast: 1.50,
      rgdp_growth: 0.80,
      tbill_forecast: 1.75,
      population_growth: -0.20,
      productivity_growth: 1.59,
      my_ratio: 2.3,
      current_headline_inflation: 1.50,
      long_term_inflation: 1.50,
      current_tbill: 1.62,
      country_factor: -0.50,
    },
    em: {
      inflation_forecast: 4.00,
      rgdp_growth: 3.40,
      tbill_forecast: 4.00,
      population_growth: 1.00,
      productivity_growth: 2.44,
      my_ratio: 1.5,
      current_headline_inflation: 4.00,
      long_term_inflation: 4.00,
      current_tbill: 4.00,
      // Negative country factor reflects structurally suppressed EM short rates
      // (financial repression / capital controls) — needed so the 10y avg lands
      // on 4% rather than the ~7% implied by RGDP + Inflation.
      country_factor: -3.40,
    },
  },
  bonds: {
    // Q2 2026 defaults. Term-premium fields are set so the model's
    // avg_yield = E[T-Bill] + avg_TP equals the stated current_yield
    // (current_TP = fair_TP = current_yield - E[T-Bill]).
    global: {
      // Regime-based: USD = US Treasury / Global Agg, EUR = Bund / EUR sovereign agg
      usd: {
        current_yield: 4.60,           // US 10y UST proxy
        duration: 8.0,
        // TP normalizes upward (0.81 -> 1.00) over horizon
        current_term_premium: 0.81,
        fair_term_premium: 1.00,
      },
      eur: {
        current_yield: 3.00,           // 10y Bund
        duration: 7.5,
        // TP normalizes upward 0.40 -> 0.50 over horizon
        current_term_premium: 0.40,
        fair_term_premium: 0.50,
      },
    },
    hy: {
      current_yield: 7.10,
      duration: 3.0,
      // TP now represents duration risk only (credit risk captured by
      // credit_spread + credit_loss). Yield component will be ~5% (T-Bill + TP).
      current_term_premium: 1.00,
      fair_term_premium: 1.00,
      credit_spread: 2.60,
      fair_credit_spread: 4.00,
      default_rate: 3.40,
      recovery_rate: 40.0,
    },
    em: {
      current_yield: 6.00,             // EM USD-denominated sovereign aggregate
      duration: 5.8,
      // EM model adds em_spread=2% on top of US T-Bill internally.
      // Base rate = 4+2 = 6%. TP rises from 0.81 -> 1.00 over horizon.
      current_term_premium: 0.81,
      fair_term_premium: 1.00,
      default_rate: 3.40,
      recovery_rate: 55.0,
    },
    inflation_linked: {
      usd: {
        current_real_yield: 2.10,      // 10y TIPS
        duration: 4.3,
        current_real_term_premium: 0.80,
        fair_real_term_premium: 0.80,
        inflation_beta: 1.00,
        index_lag_drag: 0.10,
        liquidity_technical: 0.05,
      },
      eur: {
        current_real_yield: 0.75,
        duration: 7.5,
        current_real_term_premium: 0.15,
        fair_real_term_premium: 0.10,
        inflation_beta: 1.00,
        index_lag_drag: 0.15,
        liquidity_technical: 0.10,
      },
    },
  },
  equity: {
    // Q2 2026 RA equity defaults
    us: {
      dividend_yield: 1.10,
      current_caey: 2.50,             // CAPE ~40
      fair_caey: 4.30,                // CAPE ~23
      real_eps_growth: 1.80,
      regional_eps_growth: 1.60,
      reversion_speed: 100,
    },
    europe: {
      dividend_yield: 2.80,
      current_caey: 4.40,
      fair_caey: 4.30,                // basically at fair value
      real_eps_growth: 1.20,
      regional_eps_growth: 1.60,
      reversion_speed: 100,
    },
    japan: {
      dividend_yield: 1.90,
      current_caey: 3.70,
      fair_caey: 3.70,                // at fair value
      real_eps_growth: 0.80,
      regional_eps_growth: 1.60,
      reversion_speed: 100,
    },
    em: {
      dividend_yield: 2.20,
      current_caey: 3.80,             // CAPE ~26 — currently rich vs fair
      fair_caey: 5.80,                // CAPE ~17
      real_eps_growth: 3.00,
      regional_eps_growth: 2.80,
      reversion_speed: 100,
    },
  },
  absolute_return: {
    trading_alpha: 1.00,
    beta_market: 0.30,
    beta_size: 0.10,
    beta_value: 0.05,
    beta_profitability: 0.05,
    beta_investment: 0.05,
    beta_momentum: 0.10,
  },
};

// Q2 2026 Grinold-Kroner equity defaults (values in percentage points / ratios)
export const DEFAULT_INPUTS_GK_EQUITY: Record<EquityRegion, EquityInputsGK> = {
  us: {
    dividend_yield: 1.10,
    net_buyback_yield: 1.30,
    revenue_growth: 6.20,          // auto-computed: inflation 3.0 + GDP 1.2 + wedge 2.0
    revenue_gdp_wedge: 2.00,
    margin_change: -0.50,
    current_pe: 21.3,
    target_pe: 22.7,
  },
  europe: {
    dividend_yield: 2.80,
    net_buyback_yield: 0.70,
    revenue_growth: 3.50,          // inflation 2.0 + GDP 1.0 + wedge 0.5
    revenue_gdp_wedge: 0.50,
    margin_change: 0.00,
    current_pe: 14.9,
    target_pe: 16.4,
  },
  japan: {
    dividend_yield: 1.90,
    net_buyback_yield: 1.40,
    revenue_growth: 2.80,          // inflation 1.5 + GDP 0.8 + wedge 0.5
    revenue_gdp_wedge: 0.50,
    margin_change: 0.30,
    current_pe: 21.9,
    target_pe: 22.1,
  },
  em: {
    dividend_yield: 2.20,
    net_buyback_yield: -0.60,
    revenue_growth: 7.90,          // inflation 4.0 + GDP 3.4 + wedge 0.5
    revenue_gdp_wedge: 0.50,
    margin_change: 0.00,
    current_pe: 11.7,
    target_pe: 15.0,
  },
};

// Region display names
export const REGION_NAMES: Record<string, string> = {
  us: 'United States',
  eurozone: 'Eurozone',
  japan: 'Japan',
  em: 'Emerging Markets',
  europe: 'Europe',
};

// Macro field display names
export const MACRO_FIELD_NAMES: Record<string, string> = {
  inflation_forecast: 'E[Inflation]',
  rgdp_growth: 'E[Real GDP Growth]',
  tbill_forecast: 'E[T-Bill Rate]',
  population_growth: 'Population Growth',
  productivity_growth: 'Productivity Growth',
  my_ratio: 'MY Ratio',
  current_headline_inflation: 'Current Headline Inflation',
  long_term_inflation: 'Long-Term Inflation Target',
  current_tbill: 'Current T-Bill Rate',
  country_factor: 'Country Factor',
};

// Building block field keys (used for preview calculations)
export const BUILDING_BLOCK_KEYS = [
  'population_growth',
  'productivity_growth',
  'my_ratio',
  'current_headline_inflation',
  'long_term_inflation',
  'current_tbill',
  'country_factor',
] as const;

// Direct forecast field keys
export const DIRECT_FORECAST_KEYS = [
  'inflation_forecast',
  'rgdp_growth',
  'tbill_forecast',
] as const;
