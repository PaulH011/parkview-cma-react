/**
 * TypeScript types for the Parkview CMA Tool
 */

// Region types
export type MacroRegion = 'us' | 'eurozone' | 'japan' | 'em' | 'switzerland';
export type EquityRegion = 'us' | 'europe' | 'japan' | 'em';
export type BondType = 'global' | 'hy' | 'em' | 'inflation_linked';

// Asset class identifiers
export type AssetClass =
  | 'liquidity'
  | 'bonds_global'
  | 'bonds_hy'
  | 'bonds_em'
  | 'inflation_linked'
  | 'equity_us'
  | 'equity_europe'
  | 'equity_japan'
  | 'equity_em'
  | 'absolute_return';

// Base currency
export type BaseCurrency = 'usd' | 'eur' | 'chf';

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

// Regime-based Bonds Global (USD = UST/Global Agg, EUR = Bund/EUR sovereign agg)
export interface BondGlobalRegimeInputs {
  current_yield: number;
  duration: number;
  current_term_premium: number;
  fair_term_premium: number;
}

export interface BondGlobalInputs {
  usd: BondGlobalRegimeInputs;
  eur: BondGlobalRegimeInputs;
  chf: BondGlobalRegimeInputs;
}

export interface InflationLinkedRegimeInputs {
  current_real_yield: number;
  duration: number;
  current_real_term_premium: number;
  fair_real_term_premium: number;
  inflation_beta: number;
  index_lag_drag: number;
  liquidity_technical: number;
}

export interface InflationLinkedInputs {
  usd: InflationLinkedRegimeInputs;
  eur: InflationLinkedRegimeInputs;
}

// Equity input structure (RA model)
export interface EquityInputs {
  dividend_yield: number;
  current_caey: number;
  fair_caey: number;
  real_eps_growth: number;
  regional_eps_growth: number;
  reversion_speed: number;
}

// Equity input structure (Grinold-Kroner model)
export interface EquityInputsGK {
  dividend_yield: number;       // Current trailing dividend yield (%)
  net_buyback_yield: number;    // Buybacks minus dilution (%)
  revenue_growth: number;       // Nominal revenue growth (%) — computed from macro or overridden
  revenue_gdp_wedge: number;    // Revenue premium over nominal GDP (%)
  margin_change: number;        // Annual profit margin change (%)
  current_pe: number;           // Current forward P/E ratio (x)
  target_pe: number;            // Equilibrium P/E ratio (x)
}

// Equity model type toggle
export type EquityModelType = 'ra' | 'gk';

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
  bonds: {
    global: BondGlobalInputs;
    hy: BondInputs;
    em: BondInputs;
    inflation_linked: InflationLinkedInputs;
  };
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
  inputs_used: Record<string, { value: unknown; source: string }>;
  macro_dependencies: Record<string, MacroDependency>;
}

// Calculation response from API
// results is Partial: inflation_linked is absent in CHF base
// (Switzerland has no domestic inflation-linked bond market)
export interface CalculateResponse {
  scenario_name: string;
  base_currency: string;
  results: Partial<Record<AssetClass, AssetResult>>;
  macro_forecasts: Record<MacroRegion, {
    rgdp_growth: number;
    inflation: number;
    tbill_rate: number;
  }>;
  fx_forecasts?: Record<string, {
    fx_change: number;
    carry_component: number;
    ppp_component: number;
  }> | null;
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
  bonds_global?: {
    usd?: Partial<BondGlobalRegimeInputs>;
    eur?: Partial<BondGlobalRegimeInputs>;
    chf?: Partial<BondGlobalRegimeInputs>;
  };
  bonds_hy?: Partial<BondInputs>;
  bonds_em?: Partial<BondInputs>;
  inflation_linked?: {
    usd?: Partial<InflationLinkedRegimeInputs>;
    eur?: Partial<InflationLinkedRegimeInputs>;
  };
  equity_us?: Partial<EquityInputs> | Partial<EquityInputsGK>;
  equity_europe?: Partial<EquityInputs> | Partial<EquityInputsGK>;
  equity_japan?: Partial<EquityInputs> | Partial<EquityInputsGK>;
  equity_em?: Partial<EquityInputs> | Partial<EquityInputsGK>;
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
  { key: 'inflation_linked', name: 'Bonds Inflation Linked', icon: '📈', volatility: 0.07 },
  { key: 'equity_us', name: 'Equity US', icon: '🇺🇸', volatility: 0.16 },
  { key: 'equity_europe', name: 'Equity Europe', icon: '🇪🇺', volatility: 0.18 },
  { key: 'equity_japan', name: 'Equity Japan', icon: '🇯🇵', volatility: 0.18 },
  { key: 'equity_em', name: 'Equity EM', icon: '🌏', volatility: 0.24 },
  { key: 'absolute_return', name: 'Absolute Return', icon: '🎯', volatility: 0.08 },
];
