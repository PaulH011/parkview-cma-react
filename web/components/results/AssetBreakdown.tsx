'use client';

import { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Cell,
  ResponsiveContainer,
  LabelList,
  ReferenceLine,
} from 'recharts';
import { Badge } from '@/components/ui/badge';
import { ASSET_FORMULAS, getAssetFormulas, INPUT_DISPLAY_NAMES } from '@/lib/formulas';
import { useInputStore } from '@/stores/inputStore';
import type { AssetClass, AssetResult, MacroDependency } from '@/lib/types';

interface AssetBreakdownProps {
  assetKey: AssetClass;
  result: AssetResult;
  isOpen: boolean;
}

// Waterfall chart component for visualizing return attribution
function WaterfallChart({ components }: { components: { name: string; value: number; color: string }[] }) {
  // Calculate cumulative values for waterfall effect
  let cumulative = 0;
  const data = components.map((comp, index) => {
    const start = cumulative;
    cumulative += comp.value;
    return {
      name: comp.name,
      value: comp.value,
      start,
      end: cumulative,
      color: comp.color,
      // For the bar chart, we need the actual bar height
      barValue: Math.abs(comp.value),
      isNegative: comp.value < 0,
    };
  });

  // Add total bar
  const total = cumulative;
  data.push({
    name: 'Total',
    value: total,
    start: 0,
    end: total,
    color: total >= 0 ? '#22c55e' : '#ef4444',
    barValue: Math.abs(total),
    isNegative: total < 0,
  });

  return (
    <div className="h-48 w-full mt-4">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 5, right: 50, left: 80, bottom: 5 }}
        >
          <XAxis
            type="number"
            domain={['auto', 'auto']}
            tickFormatter={(value) => `${(value * 100).toFixed(1)}%`}
            fontSize={11}
          />
          <YAxis
            type="category"
            dataKey="name"
            fontSize={11}
            width={70}
          />
          <ReferenceLine x={0} stroke="#64748b" strokeDasharray="3 3" />
          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
            <LabelList
              dataKey="value"
              position="right"
              formatter={(value) => typeof value === 'number' ? `${(value * 100).toFixed(2)}%` : ''}
              fontSize={10}
              fill="#374151"
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// Known key aliases where the backend key doesn't match the suffix pattern
const KEY_ALIASES: Record<string, string[]> = {
  credit_spread: ['credit_spread_current_spread'],
  fair_credit_spread: ['credit_spread_fair_spread'],
  us_tbill_forecast: ['yield_tbill_forecast', 'tbill_forecast'],
  duration: ['roll_duration', 'valuation_duration'],
  term_premium: ['roll_term_premium', 'yield_current_term_premium'],
  current_term_premium: ['yield_current_term_premium'],
  fair_term_premium: ['yield_fair_term_premium'],
  beta_market: ['factor_market'],
  beta_size: ['factor_size'],
  beta_value: ['factor_value'],
  beta_profitability: ['factor_profitability'],
  beta_investment: ['factor_investment'],
  beta_momentum: ['factor_momentum'],
  fx_carry_component: ['fx_carry'],
  fx_ppp_component: ['fx_ppp'],
};

// Find input data from inputsUsed - handles prefixed keys from API
// API returns keys like "dividend_dividend_yield" but we look for "dividend_yield"
function findInputData(
  inputKey: string,
  inputsUsed: Record<string, { value: any; source: string }>
): { value: any; source: string } | undefined {
  // Direct match
  if (inputsUsed[inputKey]) {
    return inputsUsed[inputKey];
  }

  // Check explicit aliases
  const aliases = KEY_ALIASES[inputKey];
  if (aliases) {
    for (const alias of aliases) {
      if (inputsUsed[alias]) {
        return inputsUsed[alias];
      }
    }
  }

  // Look for prefixed key (e.g., "dividend_dividend_yield" for "dividend_yield")
  for (const [key, data] of Object.entries(inputsUsed)) {
    if (key.endsWith(`_${inputKey}`) || key === inputKey) {
      return data;
    }
  }

  return undefined;
}

// Component detail row
function ComponentDetail({
  name,
  formula,
  description,
  value,
  inputs,
  inputsUsed,
}: {
  name: string;
  formula: string;
  description: string;
  value: number;
  inputs: string[];
  inputsUsed: Record<string, { value: any; source: string }>;
}) {
  return (
    <div className="bg-slate-50 rounded-lg p-3 space-y-2">
      <div className="flex items-center justify-between">
        <h5 className="font-medium text-slate-800">{name}</h5>
        <span className="font-semibold text-lg">
          {value >= 0 ? '+' : ''}{(value * 100).toFixed(2)}%
        </span>
      </div>

      <p className="text-sm text-slate-600 font-mono bg-white px-2 py-1 rounded border">
        {formula}
      </p>

      <p className="text-xs text-slate-500">{description}</p>

      {name === 'FX Return' && (
        <p className="text-xs text-slate-500 italic">
          Reflects expected currency movement from inflation and rate differentials between regions.
        </p>
      )}

      {inputs.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-2">
          {inputs.map((inputKey) => {
            const inputData = findInputData(inputKey, inputsUsed);
            const displayName = INPUT_DISPLAY_NAMES[inputKey] || inputKey;
            const isOverridden = inputData?.source === 'override';

            return (
              <Badge
                key={inputKey}
                variant="outline"
                className={`text-xs ${
                  isOverridden
                    ? 'bg-blue-50 text-blue-700 border-blue-200'
                    : 'bg-slate-100 text-slate-600'
                }`}
              >
                {displayName}: {formatInputValue(inputData?.value)}
                {isOverridden && <span className="ml-1 text-blue-500">*</span>}
              </Badge>
            );
          })}
        </div>
      )}
    </div>
  );
}

// Format input values nicely
function formatInputValue(value: any): string {
  if (value === undefined || value === null) return '—';
  if (typeof value === 'number') {
    // Detect if it's a percentage (small decimal) or a ratio
    if (Math.abs(value) < 1) {
      return `${(value * 100).toFixed(2)}%`;
    }
    return value.toFixed(2);
  }
  return String(value);
}

// Format macro input key for display
function formatMacroInputKey(key: string): string {
  const parts = key.split('.');
  if (parts.length === 2) {
    const region = parts[0].toUpperCase();
    const field = parts[1]
      .replace(/_/g, ' ')
      .replace(/\b\w/g, c => c.toUpperCase())
      .replace('Rgdp', 'GDP')
      .replace('Tbill', 'T-Bill');
    return `${region} ${field}`;
  }
  return key;
}

// Macro Dependencies display component
function MacroDependencies({ 
  dependencies 
}: { 
  dependencies: Record<string, MacroDependency> 
}) {
  if (!dependencies || Object.keys(dependencies).length === 0) return null;
  
  const hasOverrides = Object.values(dependencies).some(
    d => d.source === 'override' || d.source === 'affected_by_override'
  );
  
  return (
    <div className="mt-4 pt-4 border-t border-slate-200">
      <h4 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
        <span>Macro Dependencies</span>
        {hasOverrides && (
          <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200 text-xs">
            Affected by Override
          </Badge>
        )}
      </h4>
      
      <div className="space-y-2">
        {Object.entries(dependencies).map(([key, dep]) => {
          const isOverride = dep.source === 'override';
          const isAffected = dep.source === 'affected_by_override';
          const hasChange = isOverride || isAffected;
          
          return (
            <div 
              key={key}
              className={`flex items-start justify-between p-3 rounded-lg ${
                isOverride 
                  ? 'bg-blue-50 border border-blue-200' 
                  : isAffected
                  ? 'bg-amber-50 border border-amber-200'
                  : 'bg-slate-50'
              }`}
            >
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-slate-800">
                    {formatMacroInputKey(dep.macro_input)}
                  </span>
                  {isOverride && (
                    <Badge className="bg-blue-100 text-blue-700 border-blue-300 text-xs">
                      Override
                    </Badge>
                  )}
                  {isAffected && (
                    <Badge className="bg-amber-100 text-amber-700 border-amber-300 text-xs">
                      Affected
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-slate-500 mt-1">{dep.impact_description}</p>
              </div>
              <div className="text-right ml-4">
                <span className={`text-sm font-mono ${hasChange ? 'font-semibold' : ''}`}>
                  {formatInputValue(dep.value_used)}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function AssetBreakdown({ assetKey, result, isOpen }: AssetBreakdownProps) {
  const { equityModelType } = useInputStore();
  const formulas = getAssetFormulas(equityModelType);
  const formula = formulas[assetKey];

  // Build component data with actual values from result
  const componentData = useMemo(() => {
    if (!formula || !result.components) return [];

    const data = formula.components.map((comp) => {
      const rawValue = result.components[comp.key] || 0;
      // Negate subtracted components (e.g., credit_loss is returned as positive but subtracted in the formula)
      const chartValue = comp.subtract ? -Math.abs(rawValue) : rawValue;
      return {
        name: comp.name,
        value: chartValue,
        color: comp.color,
        formula: comp.formula,
        description: comp.description,
        inputs: comp.inputs,
        rawValue, // Keep original for display in Component Breakdown
      };
    });

    // Append FX Return component if present (EUR base currency adjustments)
    const fxReturn = result.components['fx_return'];
    if (fxReturn !== undefined && Math.abs(fxReturn) > 0.0001) {
      data.push({
        name: 'FX Return',
        value: fxReturn,
        color: '#8b5cf6', // Purple for FX
        formula: 'FX = 30% × (EUR T-Bill − Foreign T-Bill) + 70% × (EUR Infl − Foreign Infl)',
        description: 'Currency adjustment using RA PPP-based methodology (EUR base)',
        inputs: ['fx_carry_component', 'fx_ppp_component'],
        rawValue: fxReturn,
      });
    }

    return data;
  }, [formula, result.components]);

  if (!isOpen || !formula) return null;

  return (
    <div className="bg-gradient-to-r from-slate-50 to-slate-100 border-t border-slate-200 px-6 py-5 animate-in slide-in-from-top-2 duration-200">
      {/* Main Formula */}
      <div className="mb-4">
        <h4 className="text-sm font-semibold text-slate-700 mb-1">Return Formula</h4>
        <p className="text-base font-mono text-slate-800 bg-white px-3 py-2 rounded-lg border border-slate-200 inline-block">
          {formula.mainFormula}
        </p>
        <p className="text-xs text-slate-500 mt-1">{formula.description}</p>
      </div>

      {/* Waterfall Chart */}
      <div className="mb-4">
        <h4 className="text-sm font-semibold text-slate-700 mb-1">Return Attribution</h4>
        <WaterfallChart components={componentData} />
      </div>

      {/* Component Details */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-slate-700">Component Breakdown</h4>
        <div className="grid gap-3 md:grid-cols-2">
          {componentData.map((comp) => (
            <ComponentDetail
              key={comp.name}
              name={comp.name}
              formula={comp.formula}
              description={comp.description}
              value={comp.value}
              inputs={comp.inputs}
              inputsUsed={result.inputs_used || {}}
            />
          ))}
        </div>
      </div>

      {/* Macro Dependencies */}
      <MacroDependencies dependencies={result.macro_dependencies || {}} />

      {/* Override Legend */}
      <div className="mt-4 pt-3 border-t border-slate-200 flex flex-wrap items-center gap-4 text-xs text-slate-500">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-blue-500" />
          <span className="text-blue-600">*</span> = User override (asset input)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-amber-500" />
          Affected by macro override
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-slate-400" />
          Default value
        </span>
      </div>
    </div>
  );
}
