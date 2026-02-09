'use client';

import { useInputStore } from '@/stores/inputStore';
import { DEFAULT_INPUTS } from '@/lib/constants';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import type { EquityRegion, EquityInputs } from '@/lib/types';

const EQUITY_REGIONS: { key: EquityRegion; label: string; flag: string }[] = [
  { key: 'us', label: 'US', flag: '🇺🇸' },
  { key: 'europe', label: 'Europe', flag: '🇪🇺' },
  { key: 'japan', label: 'Japan', flag: '🇯🇵' },
  { key: 'em', label: 'EM', flag: '🌏' },
];

function EquityRegionInputs({ region }: { region: EquityRegion }) {
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
      {/* Primary Inputs */}
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
              <Label className="text-xs">Fair CAEY (%)</Label>
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

      {/* Advanced Building Blocks */}
      {advancedMode && (
        <>
          <Separator />

          <div className="space-y-3">
            <h4 className="text-sm font-medium text-slate-700">Building Blocks (EPS Growth)</h4>
            <p className="text-xs text-slate-500">
              Final EPS = 50% Country + 50% Regional, capped at Global GDP
            </p>

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

export function EquityInputPanel() {
  return (
    <div className="space-y-4">
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
            <EquityRegionInputs region={key} />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
