/**
 * TypeScript types for the Parkview CMA Tool
 */

// Region types
export type MacroRegion = 'us' | 'eurozone' | 'japan' | 'em';
export type EquityRegion = 'us' | 'europe' | 'japan' | 'em';
export type BondType = 'global' | 'hy' | 'em';

// Asset class identifiers
export type AssetClass =
  | 'liquidity'
  | 'bonds_global'
  | 'bonds_hy'
  | 'bonds_em'
  | 'equity_us'
  | 'equity_europe'
  | 'equity_japan'
  | 'equity_em'
  | 'absolute_return';

// Base currency
export type BaseCurrency = 'usd' | 'eur';

// Macro input structure
export interface MacroInputs {
  inflation_forecast: number;
  rgdp_growth: number;
  tbill_forecast: number;
  population_growth: number;
  productivity_growth: number;
  my_ratio: number;
  current_headline_inflation: number;
  long_term_inflation: number;
  current_tbill: number;
  country_factor: number;
}

// Bond input structure
export interface BondInputs {
  current_yield: number;
  duration: number;
  current_term_premium?: number;
  fair_term_premium?: number;
  credit_spread?: number;
  fair_credit_spread?: number;
  default_rate?: number;
  recovery_rate?: number;
}

// Equity input structure
export interface EquityInputs {
  dividend_yield: number;
  current_caey: number;
  fair_caey: number;
  real_eps_growth: number;
  regional_eps_growth: number;
  reversion_speed: number;
}

// Absolute return input structure
export interface AbsoluteReturnInputs {
  trading_alpha: number;
  beta_market: number;
  beta_size: number;
  beta_value: number;
  beta_profitability: number;
  beta_investment: number;
  beta_momentum: number;
}

// All inputs structure
export interface AllInputs {
  macro: Record<MacroRegion, MacroInputs>;
  bonds: Record<BondType, BondInputs>;
  equity: Record<EquityRegion, EquityInputs>;
  absolute_return: AbsoluteReturnInputs;
}

// Macro dependency tracking
export interface MacroDependency {
  macro_input: string;           // e.g., "us.inflation_forecast"
  value_used: number;            // The actual value used
  source: 'default' | 'override' | 'computed' | 'affected_by_override';
  affects: string[];             // Which components this affects
  impact_description: string;    // Human-readable description
}

// Asset result from API
export interface AssetResult {
  expected_return_nominal: number;
  expected_return_real: number;
  components: Record<string, number>;
  inputs_used: Record<string, { value: any; source: string }>;
  macro_dependencies: Record<string, MacroDependency>;
}

// Calculation response from API
export interface CalculateResponse {
  scenario_name: string;
  base_currency: string;
  results: Record<AssetClass, AssetResult>;
  macro_forecasts: Record<MacroRegion, {
    rgdp_growth: number;
    inflation: number;
    tbill_rate: number;
  }>;
}

// Macro preview response from API
export interface MacroPreviewResponse {
  rgdp_growth: number;
  inflation: number;
  tbill: number;
  intermediate: {
    population_growth: number;
    productivity_growth: number;
    my_ratio: number;
    demographic_effect: number;
    adjustment: number;
    output_per_capita: number;
    current_headline_inflation: number;
    long_term_inflation: number;
    current_tbill: number;
    country_factor: number;
    long_term_tbill: number;
  };
}

// Override structure (matches backend)
export interface Overrides {
  macro?: Partial<Record<MacroRegion, Partial<MacroInputs>>>;
  bonds_global?: Partial<BondInputs>;
  bonds_hy?: Partial<BondInputs>;
  bonds_em?: Partial<BondInputs>;
  equity_us?: Partial<EquityInputs>;
  equity_europe?: Partial<EquityInputs>;
  equity_japan?: Partial<EquityInputs>;
  equity_em?: Partial<EquityInputs>;
  absolute_return?: Partial<AbsoluteReturnInputs>;
}

// Display info for asset classes
export interface AssetDisplayInfo {
  key: AssetClass;
  name: string;
  icon: string;
  volatility: number;
}

export const ASSET_DISPLAY_INFO: AssetDisplayInfo[] = [
  { key: 'liquidity', name: 'Liquidity', icon: '💵', volatility: 0.01 },
  { key: 'bonds_global', name: 'Bonds Global', icon: '🏛️', volatility: 0.06 },
  { key: 'bonds_hy', name: 'Bonds HY', icon: '📊', volatility: 0.10 },
  { key: 'bonds_em', name: 'Bonds EM', icon: '🌍', volatility: 0.12 },
  { key: 'equity_us', name: 'Equity US', icon: '🇺🇸', volatility: 0.16 },
  { key: 'equity_europe', name: 'Equity Europe', icon: '🇪🇺', volatility: 0.18 },
  { key: 'equity_japan', name: 'Equity Japan', icon: '🇯🇵', volatility: 0.18 },
  { key: 'equity_em', name: 'Equity EM', icon: '🌏', volatility: 0.24 },
  { key: 'absolute_return', name: 'Absolute Return', icon: '🎯', volatility: 0.08 },
];
