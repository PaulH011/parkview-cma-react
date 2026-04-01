'use client';

import { useInputStore } from '@/stores/inputStore';
import { DEFAULT_INPUTS, DEFAULT_INPUTS_GK_EQUITY } from '@/lib/constants';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { Info } from 'lucide-react';
import { HoverCard, HoverCardTrigger, HoverCardContent } from '@/components/ui/hover-card';
import type { EquityRegion, EquityInputs, EquityInputsGK, EquityModelType } from '@/lib/types';

const EQUITY_REGIONS: { key: EquityRegion; label: string; flag: string }[] = [
  { key: 'us', label: 'US', flag: '🇺🇸' },
  { key: 'europe', label: 'Europe', flag: '🇪🇺' },
  { key: 'japan', label: 'Japan', flag: '🇯🇵' },
  { key: 'em', label: 'EM', flag: '🌏' },
];

// RA model equity inputs (existing)
function EquityRegionInputsRA({ region }: { region: EquityRegion }) {
  const { equity, setEquityValue, advancedMode } = useInputStore();
  const inputs = equity[region];
  const defaults = DEFAULT_INPUTS.equity[region];

  const handleChange = (key: keyof EquityInputs, value: string) => {
    const numValue = parseFloat(value);
    if (!isNaN(numValue)) {
      setEquityValue(region, key, numValue);
    }
  };

  return (
    <div className="space-y-4">
      <div className="space-y-3">
        <h4 className="text-sm font-medium text-slate-700">Primary Inputs</h4>

        <div className="space-y-3">
          <div className="space-y-1.5">
            <Label className="text-xs">Dividend Yield (%)</Label>
            <Input
              type="number"
              step="0.1"
              value={inputs.dividend_yield}
              onChange={(e) => handleChange('dividend_yield', e.target.value)}
              className="h-8 text-sm"
            />
            <p className="text-xs text-slate-400">Default: {defaults.dividend_yield}%</p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Current CAEY (%)</Label>
              <Input
                type="number"
                step="0.1"
                value={inputs.current_caey}
                onChange={(e) => handleChange('current_caey', e.target.value)}
                className="h-8 text-sm"
              />
              <p className="text-xs text-slate-400">1/CAPE = {defaults.current_caey}%</p>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs flex items-center gap-1">
                Fair CAEY (%)
                <HoverCard openDelay={200}>
                  <HoverCardTrigger asChild>
                    <Info className="h-3 w-3 text-slate-400 cursor-help" />
                  </HoverCardTrigger>
                  <HoverCardContent className="text-xs w-64">
                    <p>Higher fair CAEY means the market is <strong>more overvalued</strong> relative to fair value.</p>
                    <p className="mt-1 text-slate-500">Valuation drag increases as prices need to fall further to reach fair value.</p>
                  </HoverCardContent>
                </HoverCard>
              </Label>
              <Input
                type="number"
                step="0.1"
                value={inputs.fair_caey}
                onChange={(e) => handleChange('fair_caey', e.target.value)}
                className="h-8 text-sm"
              />
              <p className="text-xs text-slate-400">Default: {defaults.fair_caey}%</p>
            </div>
          </div>
        </div>
      </div>

      {advancedMode && (
        <>
          <Separator />

          <div className="space-y-3">
            <h4 className="text-sm font-medium text-slate-700">Building Blocks (EPS Growth)</h4>
            <div className="rounded-md bg-amber-50 border border-amber-200 px-3 py-2 text-xs text-amber-700">
              Final EPS = 50% Country + 50% Regional, capped at Global GDP growth. If your blended EPS exceeds global GDP, it will be silently capped.
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs">Country EPS Growth (%)</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={inputs.real_eps_growth}
                  onChange={(e) => handleChange('real_eps_growth', e.target.value)}
                  className="h-8 text-sm"
                />
                <p className="text-xs text-slate-400">Default: {defaults.real_eps_growth}%</p>
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs">Regional EPS Growth (%)</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={inputs.regional_eps_growth}
                  onChange={(e) => handleChange('regional_eps_growth', e.target.value)}
                  className="h-8 text-sm"
                />
                <p className="text-xs text-slate-400">Default: {defaults.regional_eps_growth}%</p>
              </div>
            </div>
          </div>

          <Separator />

          <div className="space-y-3">
            <h4 className="text-sm font-medium text-slate-700">Valuation Reversion</h4>
            <p className="text-xs text-slate-500">
              Controls how much CAEY reverts to fair value. 100% = full reversion, lower = dampened.
            </p>

            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <Label className="text-xs whitespace-nowrap">Reversion Speed</Label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  value={inputs.reversion_speed}
                  onChange={(e) => handleChange('reversion_speed', e.target.value)}
                  className="flex-1 h-2 accent-slate-700 cursor-pointer"
                />
                <Input
                  type="number"
                  min="0"
                  max="100"
                  step="5"
                  value={inputs.reversion_speed}
                  onChange={(e) => handleChange('reversion_speed', e.target.value)}
                  className="h-8 text-sm w-20"
                />
                <span className="text-xs text-slate-500">%</span>
              </div>
              <p className="text-xs text-slate-400">
                Default: {defaults.reversion_speed}% (full mean reversion)
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// Grinold-Kroner model equity inputs (new)
function EquityRegionInputsGK({ region }: { region: EquityRegion }) {
  const { equityGK, setEquityGKValue, advancedMode, macro } = useInputStore();
  const inputs = equityGK[region];
  const defaults = DEFAULT_INPUTS_GK_EQUITY[region];

  // Map equity region to macro region for revenue growth computation
  const macroRegionMap: Record<EquityRegion, 'us' | 'eurozone' | 'japan' | 'em'> = {
    us: 'us',
    europe: 'eurozone',
    japan: 'japan',
    em: 'em',
  };

  const macroRegion = macroRegionMap[region];
  const macroData = macro[macroRegion];

  // Compute revenue growth from macro (inflation + GDP + wedge)
  const computedRevGrowth =
    macroData.inflation_forecast + macroData.rgdp_growth + inputs.revenue_gdp_wedge;

  // Compute valuation change from P/E
  const valuationChange =
    inputs.current_pe > 0 && inputs.target_pe > 0
      ? ((inputs.target_pe / inputs.current_pe) ** (1 / 10) - 1) * 100
      : 0;

  // Compute total expected return
  const totalReturn =
    inputs.dividend_yield +
    inputs.net_buyback_yield +
    inputs.revenue_growth +
    inputs.margin_change +
    valuationChange;

  const handleChange = (key: keyof EquityInputsGK, value: string) => {
    const numValue = parseFloat(value);
    if (!isNaN(numValue)) {
      setEquityGKValue(region, key, numValue);
    }
  };

  return (
    <div className="space-y-4">
      {/* Income Return Section */}
      <div className="space-y-3">
        <h4 className="text-sm font-medium text-slate-700">Income Return</h4>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label className="text-xs">Dividend Yield (%)</Label>
            <Input
              type="number"
              step="0.1"
              value={inputs.dividend_yield}
              onChange={(e) => handleChange('dividend_yield', e.target.value)}
              className="h-8 text-sm"
            />
            <p className="text-xs text-slate-400">Default: {defaults.dividend_yield}%</p>
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs">Net Buyback Yield (%)</Label>
            <Input
              type="number"
              step="0.1"
              value={inputs.net_buyback_yield}
              onChange={(e) => handleChange('net_buyback_yield', e.target.value)}
              className="h-8 text-sm"
            />
            <p className="text-xs text-slate-400">Default: {defaults.net_buyback_yield}%</p>
          </div>
        </div>
      </div>

      <Separator />

      {/* Growth Section */}
      <div className="space-y-3">
        <h4 className="text-sm font-medium text-slate-700">Growth</h4>

        <div className="space-y-1.5">
          <Label className="text-xs">Revenue Growth (%)</Label>
          <Input
            type="number"
            step="0.1"
            value={inputs.revenue_growth}
            onChange={(e) => handleChange('revenue_growth', e.target.value)}
            className="h-8 text-sm"
          />
          <p className="text-xs text-slate-400">
            Computed: {macroData.inflation_forecast.toFixed(1)}% infl + {macroData.rgdp_growth.toFixed(1)}% GDP + {inputs.revenue_gdp_wedge.toFixed(1)}% wedge = {computedRevGrowth.toFixed(1)}%
          </p>
        </div>

        {advancedMode && (
          <div className="space-y-1.5">
            <Label className="text-xs">Revenue-GDP Wedge (%)</Label>
            <div className="flex items-center gap-3">
              <input
                type="range"
                min="-2"
                max="5"
                step="0.1"
                value={inputs.revenue_gdp_wedge}
                onChange={(e) => handleChange('revenue_gdp_wedge', e.target.value)}
                className="flex-1 h-2 accent-slate-700 cursor-pointer"
              />
              <Input
                type="number"
                step="0.1"
                value={inputs.revenue_gdp_wedge}
                onChange={(e) => handleChange('revenue_gdp_wedge', e.target.value)}
                className="h-8 text-sm w-20"
              />
            </div>
            <p className="text-xs text-slate-400">
              Default: {defaults.revenue_gdp_wedge}% (revenue premium over nominal GDP)
            </p>
          </div>
        )}

        <div className="space-y-1.5">
          <Label className="text-xs">Margin Change (%)</Label>
          <Input
            type="number"
            step="0.1"
            value={inputs.margin_change}
            onChange={(e) => handleChange('margin_change', e.target.value)}
            className="h-8 text-sm"
          />
          <p className="text-xs text-slate-400">Default: {defaults.margin_change}%</p>
        </div>
      </div>

      <Separator />

      {/* Valuation Section */}
      <div className="space-y-3">
        <h4 className="text-sm font-medium text-slate-700">Valuation</h4>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label className="text-xs">Current Forward P/E (x)</Label>
            <Input
              type="number"
              step="0.5"
              value={inputs.current_pe}
              onChange={(e) => handleChange('current_pe', e.target.value)}
              className="h-8 text-sm"
            />
            <p className="text-xs text-slate-400">Default: {defaults.current_pe}x</p>
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs">Target P/E (x)</Label>
            <Input
              type="number"
              step="0.5"
              value={inputs.target_pe}
              onChange={(e) => handleChange('target_pe', e.target.value)}
              className="h-8 text-sm"
            />
            <p className="text-xs text-slate-400">Default: {defaults.target_pe}x</p>
          </div>
        </div>

        <p className="text-xs text-slate-500">
          Valuation Change: {valuationChange >= 0 ? '+' : ''}{valuationChange.toFixed(2)}% p.a.
          ({inputs.current_pe}x &rarr; {inputs.target_pe}x over 10 years)
        </p>
      </div>

      {/* Total Summary */}
      <Separator />
      <div className="rounded-md bg-slate-50 p-3">
        <div className="flex justify-between items-center">
          <span className="text-sm font-medium text-slate-700">Expected Nominal Return</span>
          <span className="text-sm font-bold text-slate-900">{totalReturn.toFixed(2)}%</span>
        </div>
        <div className="mt-2 text-xs text-slate-500 space-y-0.5">
          <div className="flex justify-between">
            <span>Dividend Yield</span>
            <span>{inputs.dividend_yield.toFixed(2)}%</span>
          </div>
          <div className="flex justify-between">
            <span>+ Net Buyback Yield</span>
            <span>{inputs.net_buyback_yield >= 0 ? '+' : ''}{inputs.net_buyback_yield.toFixed(2)}%</span>
          </div>
          <div className="flex justify-between">
            <span>+ Revenue Growth</span>
            <span>+{inputs.revenue_growth.toFixed(2)}%</span>
          </div>
          <div className="flex justify-between">
            <span>+ Margin Change</span>
            <span>{inputs.margin_change >= 0 ? '+' : ''}{inputs.margin_change.toFixed(2)}%</span>
          </div>
          <div className="flex justify-between">
            <span>+ Valuation Change</span>
            <span>{valuationChange >= 0 ? '+' : ''}{valuationChange.toFixed(2)}%</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export function EquityInputPanel() {
  const { equityModelType, setEquityModelType } = useInputStore();

  return (
    <div className="space-y-4">
      {/* Model Toggle */}
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium text-slate-600">Model:</span>
        <div className="flex rounded-md border border-slate-200 overflow-hidden">
          <button
            onClick={() => setEquityModelType('ra')}
            className={`px-3 py-1.5 text-xs font-medium transition-colors ${
              equityModelType === 'ra'
                ? 'bg-slate-800 text-white'
                : 'bg-white text-slate-600 hover:bg-slate-50'
            }`}
          >
            RA Model
          </button>
          <button
            onClick={() => setEquityModelType('gk')}
            className={`px-3 py-1.5 text-xs font-medium transition-colors ${
              equityModelType === 'gk'
                ? 'bg-slate-800 text-white'
                : 'bg-white text-slate-600 hover:bg-slate-50'
            }`}
          >
            Grinold-Kroner
          </button>
        </div>
      </div>

      {equityModelType === 'gk' && (
        <p className="text-xs text-amber-600 bg-amber-50 rounded-md px-3 py-2">
          E[R] = Dividend Yield + Net Buyback + Revenue Growth + Margin + Valuation (P/E)
        </p>
      )}

      <Tabs defaultValue="us" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          {EQUITY_REGIONS.map(({ key, label, flag }) => (
            <TabsTrigger key={key} value={key} className="text-xs">
              {flag} {label}
            </TabsTrigger>
          ))}
        </TabsList>

        {EQUITY_REGIONS.map(({ key }) => (
          <TabsContent key={key} value={key} className="mt-4">
            {equityModelType === 'gk' ? (
              <EquityRegionInputsGK region={key} />
            ) : (
              <EquityRegionInputsRA region={key} />
            )}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
