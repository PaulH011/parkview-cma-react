/**
 * Formula definitions and display information for each asset class
 */

import type { AssetClass } from './types';

export interface FormulaComponent {
  key: string;
  name: string;
  formula: string;
  description: string;
  inputs: string[];
  color: string; // For the waterfall chart
  subtract?: boolean; // If true, this component is subtracted in the formula
}

export interface AssetFormula {
  mainFormula: string;
  description: string;
  components: FormulaComponent[];
}

export const ASSET_FORMULAS: Record<AssetClass, AssetFormula> = {
  liquidity: {
    mainFormula: 'E[Return] = E[T-Bill Rate]',
    description: 'Cash return equals the expected T-Bill rate over the forecast horizon.',
    components: [
      {
        key: 'tbill_rate',
        name: 'T-Bill Rate',
        formula: 'E[T-Bill] = 30% × Current + 70% × Long-Term',
        description: 'Long-Term = max(-0.75%, Country Factor + GDP + Inflation)',
        inputs: ['current_tbill', 'country_factor', 'rgdp_forecast', 'inflation_forecast'],
        color: '#3b82f6',
      },
    ],
  },

  bonds_global: {
    mainFormula: 'E[Return] = Yield + Roll Return + Valuation - Credit Loss',
    description: 'Government bond returns based on yield, roll-down, and term premium mean reversion.',
    components: [
      {
        key: 'yield',
        name: 'Yield',
        formula: 'Avg Yield = E[T-Bill] + Avg Term Premium',
        description: 'Average yield over the forecast horizon as term premium mean-reverts',
        inputs: ['current_yield', 'tbill_forecast', 'current_term_premium', 'fair_term_premium'],
        color: '#22c55e',
      },
      {
        key: 'roll_return',
        name: 'Roll Return',
        formula: 'Roll = (Term Premium / Maturity) × Duration',
        description: 'Yield curve roll-down as bonds approach maturity',
        inputs: ['duration', 'term_premium'],
        color: '#3b82f6',
      },
      {
        key: 'valuation',
        name: 'Valuation',
        formula: 'Valuation = -Duration × (ΔTerm Premium / Horizon)',
        description: 'Price impact from term premium mean reversion',
        inputs: ['duration', 'current_term_premium', 'fair_term_premium'],
        color: '#f59e0b',
      },
      {
        key: 'credit_loss',
        name: 'Credit Loss',
        formula: 'Credit Loss = 0% (Sovereign)',
        description: 'Developed market government bonds assumed risk-free',
        inputs: [],
        color: '#ef4444',
        subtract: true,
      },
    ],
  },

  bonds_hy: {
    mainFormula: 'E[Return] = Yield + Roll + Valuation - Credit Loss',
    description: 'High yield bonds with credit spread and default loss components.',
    components: [
      {
        key: 'yield',
        name: 'Yield',
        formula: 'Avg Yield = E[T-Bill] + Term Premium + Credit Spread',
        description: 'Includes credit spread which also mean-reverts to fair value',
        inputs: ['current_yield', 'tbill_forecast', 'credit_spread', 'fair_credit_spread'],
        color: '#22c55e',
      },
      {
        key: 'roll_return',
        name: 'Roll Return',
        formula: 'Roll = (Term Premium / Maturity) × Duration',
        description: 'Shorter duration reduces roll return vs government bonds',
        inputs: ['duration', 'term_premium'],
        color: '#3b82f6',
      },
      {
        key: 'valuation',
        name: 'Valuation',
        formula: 'Valuation = -Duration × (ΔPremiums / Horizon)',
        description: 'Both term premium and credit spread mean reversion',
        inputs: ['duration', 'current_term_premium', 'fair_term_premium', 'credit_spread', 'fair_credit_spread'],
        color: '#f59e0b',
      },
      {
        key: 'credit_loss',
        name: 'Credit Loss',
        formula: 'Loss = Default Rate × (1 - Recovery Rate)',
        description: 'Annual expected loss from defaults',
        inputs: ['default_rate', 'recovery_rate'],
        color: '#ef4444',
        subtract: true,
      },
    ],
  },

  bonds_em: {
    mainFormula: 'E[Return] = Yield + Roll + Valuation - Credit Loss',
    description: 'EM USD-denominated sovereign bonds. Uses US T-Bill (not EM) since bonds are priced off US Treasury curve.',
    components: [
      {
        key: 'yield',
        name: 'Yield',
        formula: 'Avg Yield = E[US T-Bill] + Term Premium + EM Spread',
        description: 'USD-denominated; yield based on US T-Bill plus EM sovereign spread',
        inputs: ['current_yield', 'us_tbill_forecast', 'current_term_premium'],
        color: '#22c55e',
      },
      {
        key: 'roll_return',
        name: 'Roll Return',
        formula: 'Roll = (Term Premium / Maturity) × Duration',
        description: 'Similar roll mechanics to other bond classes',
        inputs: ['duration', 'term_premium'],
        color: '#3b82f6',
      },
      {
        key: 'valuation',
        name: 'Valuation',
        formula: 'Valuation = -Duration × (ΔTerm Premium / Horizon)',
        description: 'Term premium mean reversion in EM markets',
        inputs: ['duration', 'current_term_premium', 'fair_term_premium'],
        color: '#f59e0b',
      },
      {
        key: 'credit_loss',
        name: 'Credit Loss',
        formula: 'Loss = Default Rate × (1 - Recovery Rate)',
        description: 'EM hard currency sovereign default rate (~2.8% historical)',
        inputs: ['default_rate', 'recovery_rate'],
        color: '#ef4444',
        subtract: true,
      },
    ],
  },

  inflation_linked: {
    mainFormula: 'E[Nominal Return] = Real Carry + Real Roll + Real Valuation + Inflation Indexation - Lag Drag + Liquidity/Technical',
    description: 'Inflation-linked sovereign bond returns. Uses USD TIPS assumptions in USD mode and EUR inflation-linked assumptions in EUR mode.',
    components: [
      {
        key: 'real_yield_carry',
        name: 'Real Yield Carry',
        formula: 'Carry = Current Real Yield',
        description: 'Real income carry from linker real yield exposure',
        inputs: ['current_real_yield'],
        color: '#22c55e',
      },
      {
        key: 'real_roll_return',
        name: 'Real Roll',
        formula: 'Real Roll = (Real TP / Maturity) × Duration',
        description: 'Roll-down on the real yield curve',
        inputs: ['duration', 'current_real_term_premium'],
        color: '#3b82f6',
      },
      {
        key: 'real_valuation_return',
        name: 'Real Valuation',
        formula: 'Real Val = -Duration × (ΔReal TP / Horizon)',
        description: 'Price impact from real term premium mean reversion',
        inputs: ['duration', 'current_real_term_premium', 'fair_real_term_premium'],
        color: '#f59e0b',
      },
      {
        key: 'inflation_indexation',
        name: 'Inflation Indexation',
        formula: 'Indexation = Inflation × Beta',
        description: 'CPI/HICP pass-through into linker principal and coupons',
        inputs: ['inflation_forecast', 'inflation_beta'],
        color: '#14b8a6',
      },
      {
        key: 'index_lag_drag',
        name: 'Index Lag Drag',
        formula: 'Lag Drag = Indexation Lag/Seasonality Cost',
        description: 'Approximate drag from indexation lag mechanics',
        inputs: ['index_lag_drag'],
        color: '#ef4444',
        subtract: true,
      },
      {
        key: 'liquidity_technical',
        name: 'Liquidity/Technical',
        formula: 'Technical = Linker Rich/Cheap Premium',
        description: 'Optional technical valuation adjustment',
        inputs: ['liquidity_technical'],
        color: '#8b5cf6',
      },
    ],
  },

  equity_us: {
    mainFormula: 'E[Real Return] = Dividend Yield + EPS Growth + Valuation',
    description: 'US equity returns based on dividends, earnings growth, and CAEY mean reversion.',
    components: [
      {
        key: 'dividend_yield',
        name: 'Dividend Yield',
        formula: 'DY = Current Trailing 12-Month Yield',
        description: 'Taken as current market value, no mean reversion',
        inputs: ['dividend_yield'],
        color: '#22c55e',
      },
      {
        key: 'real_eps_growth',
        name: 'Real EPS Growth',
        formula: 'EPS = 50% × Country + 50% × Regional (DM)',
        description: 'Blended growth capped at Global GDP; 50-year log-linear trend',
        inputs: ['country_eps_growth', 'regional_eps_growth'],
        color: '#3b82f6',
      },
      {
        key: 'valuation_change',
        name: 'Valuation Change',
        formula: 'Val = Avg[(Fair CAEY / Current CAEY)^(\u03BB/20) - 1]',
        description: 'CAEY reverts to fair value over 20 years; \u03BB = reversion speed (default 100%)',
        inputs: ['current_caey', 'fair_caey', 'reversion_speed'],
        color: '#f59e0b',
      },
    ],
  },

  equity_europe: {
    mainFormula: 'E[Real Return] = Dividend Yield + EPS Growth + Valuation',
    description: 'European equity returns. Higher dividend yields than US, often closer to fair value.',
    components: [
      {
        key: 'dividend_yield',
        name: 'Dividend Yield',
        formula: 'DY = Current Trailing 12-Month Yield',
        description: 'European markets typically have higher dividends than US',
        inputs: ['dividend_yield'],
        color: '#22c55e',
      },
      {
        key: 'real_eps_growth',
        name: 'Real EPS Growth',
        formula: 'EPS = 50% × Country + 50% × Regional (DM)',
        description: 'Blended with Developed Markets regional average',
        inputs: ['country_eps_growth', 'regional_eps_growth'],
        color: '#3b82f6',
      },
      {
        key: 'valuation_change',
        name: 'Valuation Change',
        formula: 'Val = Avg[(Fair CAEY / Current CAEY)^(\u03BB/20) - 1]',
        description: 'CAEY reverts to fair value over 20 years; \u03BB = reversion speed (default 100%)',
        inputs: ['current_caey', 'fair_caey', 'reversion_speed'],
        color: '#f59e0b',
      },
    ],
  },

  equity_japan: {
    mainFormula: 'E[Real Return] = Dividend Yield + EPS Growth + Valuation',
    description: 'Japanese equity returns with Japan-specific growth assumptions.',
    components: [
      {
        key: 'dividend_yield',
        name: 'Dividend Yield',
        formula: 'DY = Current Trailing 12-Month Yield',
        description: 'Japan dividends increasing as payout ratios rise',
        inputs: ['dividend_yield'],
        color: '#22c55e',
      },
      {
        key: 'real_eps_growth',
        name: 'Real EPS Growth',
        formula: 'EPS = 50% × Country + 50% × Regional (DM)',
        description: 'Country growth lower due to demographics; blended with DM',
        inputs: ['country_eps_growth', 'regional_eps_growth'],
        color: '#3b82f6',
      },
      {
        key: 'valuation_change',
        name: 'Valuation Change',
        formula: 'Val = Avg[(Fair CAEY / Current CAEY)^(\u03BB/20) - 1]',
        description: 'CAEY reverts to fair value over 20 years; \u03BB = reversion speed (default 100%)',
        inputs: ['current_caey', 'fair_caey', 'reversion_speed'],
        color: '#f59e0b',
      },
    ],
  },

  equity_em: {
    mainFormula: 'E[Real Return] = Dividend Yield + EPS Growth + Valuation',
    description: 'Emerging market equity returns with EM-specific assumptions.',
    components: [
      {
        key: 'dividend_yield',
        name: 'Dividend Yield',
        formula: 'DY = Current Trailing 12-Month Yield',
        description: 'EM dividend yields vary widely across countries',
        inputs: ['dividend_yield'],
        color: '#22c55e',
      },
      {
        key: 'real_eps_growth',
        name: 'Real EPS Growth',
        formula: 'EPS = 50% × Country + 50% × Regional (EM)',
        description: 'Higher growth potential but capped at Global GDP',
        inputs: ['country_eps_growth', 'regional_eps_growth'],
        color: '#3b82f6',
      },
      {
        key: 'valuation_change',
        name: 'Valuation Change',
        formula: 'Val = Avg[(Fair CAEY / Current CAEY)^(\u03BB/20) - 1]',
        description: 'CAEY reverts to fair value over 20 years; \u03BB = reversion speed (default 100%)',
        inputs: ['current_caey', 'fair_caey', 'reversion_speed'],
        color: '#f59e0b',
      },
    ],
  },

  absolute_return: {
    mainFormula: 'E[Return] = T-Bill + Σ(β × Factor Premium) + Alpha',
    description: 'Factor-based model using Fama-French factors plus manager alpha.',
    components: [
      {
        key: 'tbill',
        name: 'T-Bill (Risk-Free)',
        formula: 'T-Bill = E[US T-Bill Rate]',
        description: 'Risk-free rate foundation for all returns',
        inputs: ['tbill_forecast'],
        color: '#94a3b8',
      },
      {
        key: 'factor_return',
        name: 'Factor Returns',
        formula: 'Factors = Σ(βᵢ × E[Factor Premiumᵢ])',
        description: 'Market, Size, Value, Profitability, Investment, Momentum',
        inputs: ['beta_market', 'beta_size', 'beta_value', 'beta_profitability', 'beta_investment', 'beta_momentum'],
        color: '#3b82f6',
      },
      {
        key: 'trading_alpha',
        name: 'Trading Alpha',
        formula: 'Alpha = 50% × Historical Alpha',
        description: 'Manager skill beyond factors; discounted for alpha decay',
        inputs: ['trading_alpha'],
        color: '#22c55e',
      },
    ],
  },
};

// Grinold-Kroner equity formula components (shared across all 4 regions)
const GK_EQUITY_COMPONENTS: FormulaComponent[] = [
  {
    key: 'dividend_yield',
    name: 'Dividend Yield',
    formula: 'DY = Current Trailing 12-Month Yield',
    description: 'Income from dividends, taken at current market value',
    inputs: ['dividend_yield'],
    color: '#22c55e',
  },
  {
    key: 'net_buyback_yield',
    name: 'Net Buyback Yield',
    formula: 'Buyback = Gross Buybacks - New Issuance',
    description: 'Net shareholder yield from buybacks minus dilution',
    inputs: ['net_buyback_yield'],
    color: '#10b981',
  },
  {
    key: 'revenue_growth',
    name: 'Revenue Growth',
    formula: 'RevGrowth = Inflation + Real GDP + Wedge',
    description: 'Nominal revenue growth, auto-computed from macro or directly overridden',
    inputs: ['revenue_growth', 'revenue_gdp_wedge'],
    color: '#3b82f6',
  },
  {
    key: 'margin_change',
    name: 'Margin Change',
    formula: 'Margin = Annual profit margin change',
    description: 'Positive = expansion (e.g., reform), negative = compression from peak',
    inputs: ['margin_change'],
    color: '#6366f1',
  },
  {
    key: 'valuation_change',
    name: 'Valuation Change',
    formula: 'Val = (Target P/E / Current P/E)^(1/10) - 1',
    description: 'P/E convergence to equilibrium over 10-year horizon',
    inputs: ['current_pe', 'target_pe'],
    color: '#f59e0b',
  },
];

// GK formula definitions for each equity region
export const ASSET_FORMULAS_GK_EQUITY: Record<string, AssetFormula> = {
  equity_us: {
    mainFormula: 'E[Nominal Return] = DY + Buyback + RevGrowth + Margin + Valuation',
    description: 'Grinold-Kroner decomposition: income, growth, and repricing.',
    components: GK_EQUITY_COMPONENTS,
  },
  equity_europe: {
    mainFormula: 'E[Nominal Return] = DY + Buyback + RevGrowth + Margin + Valuation',
    description: 'Grinold-Kroner model for European equities.',
    components: GK_EQUITY_COMPONENTS,
  },
  equity_japan: {
    mainFormula: 'E[Nominal Return] = DY + Buyback + RevGrowth + Margin + Valuation',
    description: 'Grinold-Kroner model for Japanese equities.',
    components: GK_EQUITY_COMPONENTS,
  },
  equity_em: {
    mainFormula: 'E[Nominal Return] = DY + Buyback + RevGrowth + Margin + Valuation',
    description: 'Grinold-Kroner model for Emerging Market equities.',
    components: GK_EQUITY_COMPONENTS,
  },
};

/**
 * Get the correct formula definitions based on equity model type.
 * Non-equity formulas are always from the RA set.
 */
export function getAssetFormulas(equityModelType: 'ra' | 'gk' = 'ra'): Record<AssetClass, AssetFormula> {
  if (equityModelType === 'gk') {
    return {
      ...ASSET_FORMULAS,
      equity_us: ASSET_FORMULAS_GK_EQUITY.equity_us,
      equity_europe: ASSET_FORMULAS_GK_EQUITY.equity_europe,
      equity_japan: ASSET_FORMULAS_GK_EQUITY.equity_japan,
      equity_em: ASSET_FORMULAS_GK_EQUITY.equity_em,
    };
  }
  return ASSET_FORMULAS;
}

// Human-readable input names
export const INPUT_DISPLAY_NAMES: Record<string, string> = {
  current_yield: 'Current Yield',
  duration: 'Duration',
  current_term_premium: 'Current Term Premium',
  fair_term_premium: 'Fair Term Premium',
  current_real_yield: 'Current Real Yield',
  current_real_term_premium: 'Current Real Term Premium',
  fair_real_term_premium: 'Fair Real Term Premium',
  inflation_beta: 'Inflation Beta',
  index_lag_drag: 'Index Lag Drag',
  liquidity_technical: 'Liquidity/Technical',
  credit_spread: 'Credit Spread',
  fair_credit_spread: 'Fair Credit Spread',
  default_rate: 'Default Rate',
  recovery_rate: 'Recovery Rate',
  tbill_forecast: 'E[T-Bill]',
  us_tbill_forecast: 'E[US T-Bill]',
  current_tbill: 'Current T-Bill',
  country_factor: 'Country Factor',
  rgdp_forecast: 'E[GDP Growth]',
  inflation_forecast: 'E[Inflation]',
  dividend_yield: 'Dividend Yield',
  current_caey: 'Current CAEY',
  fair_caey: 'Fair CAEY',
  country_eps_growth: 'Country EPS Growth',
  regional_eps_growth: 'Regional EPS Growth',
  beta_market: 'Market β',
  beta_size: 'Size β',
  beta_value: 'Value β',
  beta_profitability: 'Profitability β',
  beta_investment: 'Investment β',
  beta_momentum: 'Momentum β',
  trading_alpha: 'Trading Alpha',
  // RA equity-specific input names
  real_eps_growth: 'Real EPS Growth',
  regional_eps_growth: 'Regional EPS Growth',
  reversion_speed: 'Reversion Speed',
  // Macro building-block input names
  population_growth: 'Population Growth',
  productivity_growth: 'Productivity Growth',
  my_ratio: 'MY Ratio',
  current_headline_inflation: 'Current Headline Inflation',
  long_term_inflation: 'Long-Term Inflation Target',
  rgdp_growth: 'E[Real GDP Growth]',
  // GK-specific input names
  net_buyback_yield: 'Net Buyback Yield',
  revenue_growth: 'Revenue Growth',
  revenue_gdp_wedge: 'Revenue-GDP Wedge',
  margin_change: 'Margin Change',
  current_pe: 'Current P/E',
  target_pe: 'Target P/E',
  // FX-related input names
  fx_carry_component: 'FX Carry',
  fx_ppp_component: 'FX PPP',
  fx_return: 'FX Return',
  fx_home_tbill: 'EUR T-Bill',
  fx_foreign_tbill: 'Foreign T-Bill',
  fx_home_inflation: 'EUR Inflation',
  fx_foreign_inflation: 'Foreign Inflation',
};
