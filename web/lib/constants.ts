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
      tbill_forecast: 4.00,
      // Building blocks
      population_growth: 0.40,
      productivity_growth: 1.20,
      my_ratio: 2.1,
      current_headline_inflation: 3.00,
      long_term_inflation: 3.00,
      current_tbill: 3.53,
      country_factor: 0.00,
    },
    eurozone: {
      inflation_forecast: 2.00,
      rgdp_growth: 1.00,
      tbill_forecast: 2.50,
      population_growth: 0.10,
      productivity_growth: 1.49,
      my_ratio: 2.3,
      current_headline_inflation: 2.00,
      long_term_inflation: 2.00,
      current_tbill: 1.80,
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
    global: {
      current_yield: 3.50,
      duration: 7.0,
      fair_term_premium: 1.50,
      current_term_premium: 1.00,
    },
    hy: {
      current_yield: 7.50,
      duration: 4.0,
      credit_spread: 2.71,
      fair_credit_spread: 4.00,
      default_rate: 5.50,
      recovery_rate: 40.0,
    },
    em: {
      current_yield: 5.77,
      duration: 5.5,
      fair_term_premium: 2.00,
      current_term_premium: 1.50,
      default_rate: 2.80,
      recovery_rate: 55.0,
    },
    inflation_linked: {
      usd: {
        current_real_yield: 1.80,
        duration: 6.4,
        current_real_term_premium: 0.30,
        fair_real_term_premium: 0.20,
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
    us: {
      dividend_yield: 1.13,
      current_caey: 2.48,
      fair_caey: 5.00,
      real_eps_growth: 1.80,
      regional_eps_growth: 1.60,
      reversion_speed: 100,
    },
    europe: {
      dividend_yield: 3.00,
      current_caey: 5.50,
      fair_caey: 5.50,
      real_eps_growth: 1.20,
      regional_eps_growth: 1.60,
      reversion_speed: 100,
    },
    japan: {
      dividend_yield: 2.20,
      current_caey: 5.50,
      fair_caey: 5.00,
      real_eps_growth: 0.80,
      regional_eps_growth: 1.60,
      reversion_speed: 100,
    },
    em: {
      dividend_yield: 3.00,
      current_caey: 6.50,
      fair_caey: 6.00,
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

// Grinold-Kroner equity defaults (values in percentage points / ratios)
export const DEFAULT_INPUTS_GK_EQUITY: Record<EquityRegion, EquityInputsGK> = {
  us: {
    dividend_yield: 1.30,
    net_buyback_yield: 1.50,
    revenue_growth: 5.50,          // computed: inflation 2.3 + GDP 1.2 + wedge 2.0
    revenue_gdp_wedge: 2.00,
    margin_change: -0.50,
    current_pe: 22.0,
    target_pe: 20.0,
  },
  europe: {
    dividend_yield: 3.00,
    net_buyback_yield: 0.50,
    revenue_growth: 3.40,          // inflation 2.1 + GDP 0.8 + wedge 0.5
    revenue_gdp_wedge: 0.50,
    margin_change: 0.00,
    current_pe: 14.0,
    target_pe: 14.0,
  },
  japan: {
    dividend_yield: 2.20,
    net_buyback_yield: 0.80,
    revenue_growth: 2.50,          // inflation 1.7 + GDP 0.3 + wedge 0.5
    revenue_gdp_wedge: 0.50,
    margin_change: 0.30,
    current_pe: 15.0,
    target_pe: 14.5,
  },
  em: {
    dividend_yield: 3.00,
    net_buyback_yield: -1.50,
    revenue_growth: 7.30,          // inflation 3.8 + GDP 3.0 + wedge 0.5
    revenue_gdp_wedge: 0.50,
    margin_change: 0.00,
    current_pe: 12.0,
    target_pe: 12.0,
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
