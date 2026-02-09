/**
 * Default values and constants for the Parkview CMA Tool
 *
 * These match the INPUT_DEFAULTS in app.py and api/routes/defaults.py
 * Values are in percentage points (e.g., 2.29 means 2.29%)
 */

import type { AllInputs } from './types';

export const DEFAULT_INPUTS: AllInputs = {
  macro: {
    us: {
      // Direct forecasts: computed from building blocks below
      // E[RGDP] = Output-per-Capita + Population = (Prod + Demo + Adj) + Pop
      // E[Inflation] = 30% × Current + 70% × Long-Term
      // E[T-Bill] = 30% × Current + 70% × max(-0.75%, CF + GDP + Inflation)
      inflation_forecast: 2.29,
      rgdp_growth: 1.20,
      tbill_forecast: 3.54,
      // Building blocks
      population_growth: 0.40,
      productivity_growth: 1.20,
      my_ratio: 2.1,
      current_headline_inflation: 2.50,
      long_term_inflation: 2.20,
      current_tbill: 3.67,
      country_factor: 0.00,
    },
    eurozone: {
      inflation_forecast: 2.06,
      rgdp_growth: 0.51,
      tbill_forecast: 2.27,
      population_growth: 0.10,
      productivity_growth: 1.00,
      my_ratio: 2.3,
      current_headline_inflation: 2.20,
      long_term_inflation: 2.00,
      current_tbill: 2.04,
      country_factor: -0.20,
    },
    japan: {
      inflation_forecast: 1.65,
      rgdp_growth: -0.46,
      tbill_forecast: 0.71,
      population_growth: -0.50,
      productivity_growth: 0.80,
      my_ratio: 2.5,
      current_headline_inflation: 2.00,
      long_term_inflation: 1.50,
      current_tbill: 0.75,
      country_factor: -0.50,
    },
    em: {
      inflation_forecast: 3.80,
      rgdp_growth: 3.46,
      tbill_forecast: 7.23,
      population_growth: 1.00,
      productivity_growth: 2.50,
      my_ratio: 1.5,
      current_headline_inflation: 4.50,
      long_term_inflation: 3.50,
      current_tbill: 6.00,
      country_factor: 0.50,
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
