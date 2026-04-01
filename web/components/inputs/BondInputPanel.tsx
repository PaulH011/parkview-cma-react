'use client';

import { useInputStore } from '@/stores/inputStore';
import { DEFAULT_INPUTS } from '@/lib/constants';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { Info } from 'lucide-react';
import { HoverCard, HoverCardTrigger, HoverCardContent } from '@/components/ui/hover-card';
import type { BondType, BondInputs } from '@/lib/types';

const BOND_TYPES: { key: BondType; label: string; description: string }[] = [
  { key: 'global', label: 'Global Gov', description: 'Developed market government bonds' },
  { key: 'hy', label: 'High Yield', description: 'US high yield corporate bonds' },
  { key: 'em', label: 'EM Hard', description: 'EM USD-denominated sovereign bonds' },
  { key: 'inflation_linked', label: 'Bonds Inflation Linked', description: 'USD TIPS or EUR inflation-linked sovereigns (by base currency)' },
];

function BondTypeInputs({ bondType }: { bondType: Exclude<BondType, 'inflation_linked'> }) {
  const { bonds, setBondValue, advancedMode } = useInputStore();
  const inputs = bonds[bondType];
  const defaults = DEFAULT_INPUTS.bonds[bondType];

  const handleChange = (key: keyof BondInputs, value: string) => {
    const numValue = parseFloat(value);
    if (!isNaN(numValue)) {
      setBondValue(bondType, key, numValue);
    }
  };

  return (
    <div className="space-y-4">
      {/* Primary Inputs */}
      <div className="space-y-3">
        <h4 className="text-sm font-medium text-slate-700">Primary Inputs</h4>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label className="text-xs">Current Yield (%)</Label>
            <Input
              type="number"
              step="0.1"
              value={inputs.current_yield}
              onChange={(e) => handleChange('current_yield', e.target.value)}
              className="h-8 text-sm"
            />
            <p className="text-xs text-slate-400">Default: {defaults.current_yield}%</p>
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs">Duration (years)</Label>
            <Input
              type="number"
              step="0.5"
              value={inputs.duration}
              onChange={(e) => handleChange('duration', e.target.value)}
              className="h-8 text-sm"
            />
            <p className="text-xs text-slate-400">Default: {defaults.duration} yrs</p>
          </div>
        </div>

        {/* Credit-specific inputs for HY and EM */}
        {(bondType === 'hy' || bondType === 'em') && (
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Default Rate (%)</Label>
              <Input
                type="number"
                step="0.1"
                value={inputs.default_rate ?? defaults.default_rate}
                onChange={(e) => handleChange('default_rate', e.target.value)}
                className="h-8 text-sm"
              />
              <p className="text-xs text-slate-400">Default: {defaults.default_rate}%</p>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs">Recovery Rate (%)</Label>
              <Input
                type="number"
                step="1"
                value={inputs.recovery_rate ?? defaults.recovery_rate}
                onChange={(e) => handleChange('recovery_rate', e.target.value)}
                className="h-8 text-sm"
              />
              <p className="text-xs text-slate-400">Default: {defaults.recovery_rate}%</p>
            </div>
          </div>
        )}
      </div>

      {/* Advanced Building Blocks */}
      {advancedMode && (
        <>
          <Separator />

          <div className="space-y-3">
            <h4 className="text-sm font-medium text-slate-700">Building Blocks</h4>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs">Current Term Premium (%)</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={inputs.current_term_premium ?? defaults.current_term_premium}
                  onChange={(e) => handleChange('current_term_premium', e.target.value)}
                  className="h-8 text-sm"
                />
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs">Fair Term Premium (%)</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={inputs.fair_term_premium ?? defaults.fair_term_premium}
                  onChange={(e) => handleChange('fair_term_premium', e.target.value)}
                  className="h-8 text-sm"
                />
              </div>
            </div>

            {/* Credit spread inputs for HY */}
            {bondType === 'hy' && (
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label className="text-xs">Credit Spread (%)</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={inputs.credit_spread ?? defaults.credit_spread}
                    onChange={(e) => handleChange('credit_spread', e.target.value)}
                    className="h-8 text-sm"
                  />
                </div>

                <div className="space-y-1.5">
                  <Label className="text-xs flex items-center gap-1">
                    Fair Credit Spread (%)
                    <HoverCard openDelay={200}>
                      <HoverCardTrigger asChild>
                        <Info className="h-3 w-3 text-slate-400 cursor-help" />
                      </HoverCardTrigger>
                      <HoverCardContent className="text-xs w-64">
                        <p>If fair spread &gt; current spread, spreads are expected to <strong>widen</strong>, reducing bond prices.</p>
                        <p className="mt-1 text-slate-500">Higher fair spread = more negative valuation return.</p>
                      </HoverCardContent>
                    </HoverCard>
                  </Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={inputs.fair_credit_spread ?? defaults.fair_credit_spread}
                    onChange={(e) => handleChange('fair_credit_spread', e.target.value)}
                    className="h-8 text-sm"
                  />
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function InflationLinkedInputs() {
  const { bonds, setInflationLinkedValue, advancedMode, baseCurrency } = useInputStore();
  const activeRegime = baseCurrency === 'eur' ? 'eur' : 'usd';
  const inputs = bonds.inflation_linked[activeRegime];
  const defaults = DEFAULT_INPUTS.bonds.inflation_linked[activeRegime];

  const handleChange = (key: keyof typeof inputs, value: string) => {
    const numValue = parseFloat(value);
    if (!isNaN(numValue)) {
      setInflationLinkedValue(activeRegime, key, numValue);
    }
  };

  return (
    <div className="space-y-4">
      <div className="rounded-md border bg-blue-50 border-blue-200 px-3 py-2 text-xs text-blue-800">
        {activeRegime === 'usd' ? 'USD mode: using TIPS assumptions' : 'EUR mode: using EUR inflation-linked assumptions'}
      </div>

      <div className="space-y-3">
        <h4 className="text-sm font-medium text-slate-700">Primary Inputs</h4>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label className="text-xs">Current Real Yield (%)</Label>
            <Input
              type="number"
              step="0.1"
              value={inputs.current_real_yield}
              onChange={(e) => handleChange('current_real_yield', e.target.value)}
              className="h-8 text-sm"
            />
            <p className="text-xs text-slate-400">Default: {defaults.current_real_yield}%</p>
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs">Duration (years)</Label>
            <Input
              type="number"
              step="0.1"
              value={inputs.duration}
              onChange={(e) => handleChange('duration', e.target.value)}
              className="h-8 text-sm"
            />
            <p className="text-xs text-slate-400">Default: {defaults.duration} yrs</p>
          </div>
        </div>
      </div>

      {advancedMode && (
        <>
          <Separator />
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-slate-700">Building Blocks</h4>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs">Current Real Term Premium (%)</Label>
                <Input
                  type="number"
                  step="0.05"
                  value={inputs.current_real_term_premium}
                  onChange={(e) => handleChange('current_real_term_premium', e.target.value)}
                  className="h-8 text-sm"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Fair Real Term Premium (%)</Label>
                <Input
                  type="number"
                  step="0.05"
                  value={inputs.fair_real_term_premium}
                  onChange={(e) => handleChange('fair_real_term_premium', e.target.value)}
                  className="h-8 text-sm"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Inflation Beta (x)</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={inputs.inflation_beta}
                  onChange={(e) => handleChange('inflation_beta', e.target.value)}
                  className="h-8 text-sm"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Index Lag Drag (%)</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={inputs.index_lag_drag}
                  onChange={(e) => handleChange('index_lag_drag', e.target.value)}
                  className="h-8 text-sm"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Liquidity/Technical (%)</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={inputs.liquidity_technical}
                  onChange={(e) => handleChange('liquidity_technical', e.target.value)}
                  className="h-8 text-sm"
                />
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export function BondInputPanel() {
  return (
    <div className="space-y-4">
      <Tabs defaultValue="global" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          {BOND_TYPES.map(({ key, label }) => (
            <TabsTrigger key={key} value={key} className="text-xs">
              {label}
            </TabsTrigger>
          ))}
        </TabsList>

        {BOND_TYPES.map(({ key, description }) => (
          <TabsContent key={key} value={key} className="mt-4">
            <p className="text-xs text-slate-500 mb-3">{description}</p>
            {key === 'inflation_linked' ? (
              <InflationLinkedInputs />
            ) : (
              <BondTypeInputs bondType={key} />
            )}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
