'use client';

import { useEffect, useRef } from 'react';
import { useInputStore } from '@/stores/inputStore';
import { useMacroPreview } from '@/hooks/useMacroPreview';
import { DEFAULT_INPUTS, MACRO_FIELD_NAMES } from '@/lib/constants';
import { BUILDING_BLOCK_CASCADE } from '@/lib/formulas';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { ComputedPreviewTooltip } from './ComputedPreviewTooltip';
import type { MacroRegion, MacroInputs } from '@/lib/types';

function CascadeNote({ fields, inputs, defaults }: { fields: string[]; inputs: MacroInputs; defaults: MacroInputs }) {
  const changedFields = fields.filter(f => {
    const val = inputs[f as keyof MacroInputs] as number;
    const def = defaults[f as keyof MacroInputs] as number;
    return Math.abs(val - def) > 0.001;
  });
  if (changedFields.length === 0) return null;
  const cascade = BUILDING_BLOCK_CASCADE[changedFields[0]];
  if (!cascade) return null;
  return (
    <p className="text-xs text-blue-600 mt-2">
      Cascades to: {cascade.affects.join(' \u2192 ')}
    </p>
  );
}

const REGIONS: { key: MacroRegion; label: string }[] = [
  { key: 'us', label: 'US' },
  { key: 'eurozone', label: 'Europe' },
  { key: 'japan', label: 'Japan' },
  { key: 'em', label: 'EM' },
];

function MacroRegionInputs({ region }: { region: MacroRegion }) {
  const { macro, setMacroValue, syncMacroComputed, isMacroDirty, advancedMode } = useInputStore();
  const { computed, hasChanges, conflicts } = useMacroPreview(region);

  const inputs = macro[region];
  const defaults = DEFAULT_INPUTS.macro[region];

  const handleChange = (key: keyof MacroInputs, value: string) => {
    const numValue = parseFloat(value);
    if (!isNaN(numValue)) {
      setMacroValue(region, key, numValue);
    }
  };

  // Auto-sync non-dirty direct forecast fields with computed values
  // When building blocks change, the computed preview updates, and we
  // reflect those new values in the direct forecast fields (unless the
  // user has explicitly overridden them)
  useEffect(() => {
    if (!computed) return;

    const computedValues: Partial<Record<string, number>> = {
      rgdp_growth: Math.round(computed.rgdp_growth * 10000) / 100,
      inflation_forecast: Math.round(computed.inflation * 10000) / 100,
      tbill_forecast: Math.round(computed.tbill * 10000) / 100,
    };

    syncMacroComputed(region, computedValues);
  }, [computed, region, syncMacroComputed]);

  // Build breakdown for GDP
  const gdpBreakdown = computed
    ? [
        {
          label: 'Productivity Growth',
          value: computed.intermediate.productivity_growth,
          isChanged: Math.abs(inputs.productivity_growth - defaults.productivity_growth) > 0.001,
        },
        {
          label: 'Demographic Effect',
          value: computed.intermediate.demographic_effect,
          isChanged: Math.abs(inputs.my_ratio - defaults.my_ratio) > 0.001,
        },
        {
          label: 'Adjustment',
          value: computed.intermediate.adjustment,
          isChanged: false,
        },
        {
          label: 'Population Growth',
          value: computed.intermediate.population_growth,
          isChanged: Math.abs(inputs.population_growth - defaults.population_growth) > 0.001,
        },
      ]
    : [];

  // Build breakdown for Inflation
  const inflationBreakdown = computed
    ? [
        {
          label: '30% × Current',
          value: 0.3 * computed.intermediate.current_headline_inflation,
          isChanged: Math.abs(inputs.current_headline_inflation - defaults.current_headline_inflation) > 0.001,
        },
        {
          label: '70% × Long-Term',
          value: 0.7 * computed.intermediate.long_term_inflation,
          isChanged: Math.abs(inputs.long_term_inflation - defaults.long_term_inflation) > 0.001,
        },
      ]
    : [];

  // Build breakdown for T-Bill
  const tbillBreakdown = computed
    ? [
        {
          label: '30% × Current',
          value: 0.3 * computed.intermediate.current_tbill,
          isChanged: Math.abs(inputs.current_tbill - defaults.current_tbill) > 0.001,
        },
        {
          label: '70% × Long-Term',
          value: 0.7 * computed.intermediate.long_term_tbill,
          isChanged: Math.abs(inputs.country_factor - defaults.country_factor) > 0.001,
        },
      ]
    : [];

  return (
    <div className="space-y-4">
      {/* Direct Forecast Overrides */}
      <div className="space-y-3">
        <h4 className="text-sm font-medium text-slate-700">Direct Forecast Overrides</h4>
        <p className="text-xs text-slate-500">
          Override the 10-year forecast directly
        </p>

        <div className="space-y-3">
          {/* E[Inflation] */}
          <div className="space-y-1.5">
            <Label className="text-xs">E[Inflation] — 10yr Avg (%)</Label>
            <ComputedPreviewTooltip
              forecastType="inflation"
              currentValue={inputs.inflation_forecast}
              computedValue={computed?.inflation ?? 0}
              breakdown={inflationBreakdown}
              hasConflict={conflicts.inflation_forecast}
              hasChanges={hasChanges}
              onApplyComputed={() =>
                setMacroValue(region, 'inflation_forecast', (computed?.inflation ?? 0) * 100)
              }
            >
              <Input
                type="number"
                step="0.1"
                value={inputs.inflation_forecast}
                onChange={(e) => handleChange('inflation_forecast', e.target.value)}
                className="h-8 text-sm"
              />
            </ComputedPreviewTooltip>
          </div>

          {/* E[Real GDP Growth] */}
          <div className="space-y-1.5">
            <Label className="text-xs">E[Real GDP Growth] — 10yr Avg (%)</Label>
            <ComputedPreviewTooltip
              forecastType="gdp"
              currentValue={inputs.rgdp_growth}
              computedValue={computed?.rgdp_growth ?? 0}
              breakdown={gdpBreakdown}
              hasConflict={conflicts.rgdp_growth}
              hasChanges={hasChanges}
              onApplyComputed={() =>
                setMacroValue(region, 'rgdp_growth', (computed?.rgdp_growth ?? 0) * 100)
              }
            >
              <Input
                type="number"
                step="0.1"
                value={inputs.rgdp_growth}
                onChange={(e) => handleChange('rgdp_growth', e.target.value)}
                className="h-8 text-sm"
              />
            </ComputedPreviewTooltip>
          </div>

          {/* E[T-Bill Rate] */}
          <div className="space-y-1.5">
            <Label className="text-xs">E[T-Bill Rate] — 10yr Avg (%)</Label>
            <ComputedPreviewTooltip
              forecastType="tbill"
              currentValue={inputs.tbill_forecast}
              computedValue={computed?.tbill ?? 0}
              breakdown={tbillBreakdown}
              hasConflict={conflicts.tbill_forecast}
              hasChanges={hasChanges}
              onApplyComputed={() =>
                setMacroValue(region, 'tbill_forecast', (computed?.tbill ?? 0) * 100)
              }
            >
              <Input
                type="number"
                step="0.1"
                value={inputs.tbill_forecast}
                onChange={(e) => handleChange('tbill_forecast', e.target.value)}
                className="h-8 text-sm"
              />
            </ComputedPreviewTooltip>
          </div>
        </div>
      </div>

      {/* Building Blocks (Advanced Mode) */}
      {advancedMode && (
        <>
          <Separator />

          {/* GDP Building Blocks */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-slate-700">
              Building Blocks (GDP)
            </h4>
            <p className="text-xs text-slate-500">
              GDP = Output-per-Capita + Population Growth
            </p>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs">Population Growth (%)</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={inputs.population_growth}
                  onChange={(e) => handleChange('population_growth', e.target.value)}
                  className="h-8 text-sm"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Productivity Growth (%)</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={inputs.productivity_growth}
                  onChange={(e) => handleChange('productivity_growth', e.target.value)}
                  className="h-8 text-sm"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">MY Ratio</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={inputs.my_ratio}
                  onChange={(e) => handleChange('my_ratio', e.target.value)}
                  className="h-8 text-sm"
                />
              </div>
            </div>
            <CascadeNote
              fields={['population_growth', 'productivity_growth', 'my_ratio']}
              inputs={inputs}
              defaults={defaults}
            />
          </div>

          <Separator />

          {/* Inflation Building Blocks */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-slate-700">
              Building Blocks (Inflation)
            </h4>
            <p className="text-xs text-slate-500">
              30% × Current + 70% × Long-Term
            </p>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs">Current Headline (%)</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={inputs.current_headline_inflation}
                  onChange={(e) => handleChange('current_headline_inflation', e.target.value)}
                  className="h-8 text-sm"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Long-Term Target (%)</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={inputs.long_term_inflation}
                  onChange={(e) => handleChange('long_term_inflation', e.target.value)}
                  className="h-8 text-sm"
                />
              </div>
            </div>
            <CascadeNote
              fields={['current_headline_inflation', 'long_term_inflation']}
              inputs={inputs}
              defaults={defaults}
            />
          </div>

          <Separator />

          {/* T-Bill Building Blocks */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-slate-700">
              Building Blocks (T-Bill)
            </h4>
            <p className="text-xs text-slate-500">
              30% × Current + 70% × Long-Term
            </p>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs">Current T-Bill (%)</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={inputs.current_tbill}
                  onChange={(e) => handleChange('current_tbill', e.target.value)}
                  className="h-8 text-sm"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Country Factor (%)</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={inputs.country_factor}
                  onChange={(e) => handleChange('country_factor', e.target.value)}
                  className="h-8 text-sm"
                />
              </div>
            </div>
            <CascadeNote
              fields={['current_tbill', 'country_factor']}
              inputs={inputs}
              defaults={defaults}
            />
          </div>
        </>
      )}
    </div>
  );
}

export function MacroInputPanel() {
  return (
    <div className="space-y-4">
      {/* Region Tabs */}
      <Tabs defaultValue="us" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          {REGIONS.map(({ key, label }) => (
            <TabsTrigger key={key} value={key} className="text-xs">
              {label}
            </TabsTrigger>
          ))}
        </TabsList>

        {REGIONS.map(({ key }) => (
          <TabsContent key={key} value={key} className="mt-4">
            <MacroRegionInputs region={key} />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
