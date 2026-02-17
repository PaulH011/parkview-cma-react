'use client';

import { useMemo, useState } from 'react';
import { ChevronDown, ChevronUp, ListChecks } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useInputStore } from '@/stores/inputStore';
import { INPUT_DISPLAY_NAMES } from '@/lib/formulas';
import { MACRO_FIELD_NAMES } from '@/lib/constants';
import type { Overrides } from '@/lib/types';

// Keys that stay as raw numbers (not multiplied by 100 for display)
const RAW_KEYS = new Set([
  'duration',
  'my_ratio',
  'current_pe',
  'target_pe',
  'inflation_beta',
  'beta_market',
  'beta_size',
  'beta_value',
  'beta_profitability',
  'beta_investment',
  'beta_momentum',
  'reversion_speed',
]);

// Section display names
const SECTION_NAMES: Record<string, string> = {
  'macro.us': 'Macro - US',
  'macro.eurozone': 'Macro - Eurozone',
  'macro.japan': 'Macro - Japan',
  'macro.em': 'Macro - EM',
  bonds_global: 'Bonds Global',
  bonds_hy: 'Bonds HY',
  bonds_em: 'Bonds EM',
  'inflation_linked.usd': 'Bonds Inflation Linked (USD)',
  'inflation_linked.eur': 'Bonds Inflation Linked (EUR)',
  equity_us: 'Equity US',
  equity_europe: 'Equity Europe',
  equity_japan: 'Equity Japan',
  equity_em: 'Equity EM',
  absolute_return: 'Absolute Return',
};

// Section badge colour classes
const SECTION_COLORS: Record<string, string> = {
  macro: 'bg-violet-100 text-violet-700 border-violet-300',
  bonds: 'bg-blue-100 text-blue-700 border-blue-300',
  inflation: 'bg-teal-100 text-teal-700 border-teal-300',
  equity: 'bg-emerald-100 text-emerald-700 border-emerald-300',
  absolute: 'bg-amber-100 text-amber-700 border-amber-300',
};

function sectionColor(sectionKey: string): string {
  if (sectionKey.startsWith('macro')) return SECTION_COLORS.macro;
  if (sectionKey.startsWith('inflation')) return SECTION_COLORS.inflation;
  if (sectionKey.startsWith('bonds')) return SECTION_COLORS.bonds;
  if (sectionKey.startsWith('equity')) return SECTION_COLORS.equity;
  if (sectionKey.startsWith('absolute')) return SECTION_COLORS.absolute;
  return 'bg-slate-100 text-slate-700 border-slate-300';
}

function displayName(key: string): string {
  return INPUT_DISPLAY_NAMES[key] || MACRO_FIELD_NAMES[key] || key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatValue(key: string, decimal: number): string {
  if (RAW_KEYS.has(key)) {
    // Display with appropriate precision
    return Number.isInteger(decimal) ? String(decimal) : decimal.toFixed(2);
  }
  return `${(decimal * 100).toFixed(2)}%`;
}

interface OverrideEntry {
  key: string;
  displayName: string;
  formattedValue: string;
}

interface Section {
  sectionKey: string;
  label: string;
  entries: OverrideEntry[];
}

function buildSections(overrides: Overrides): Section[] {
  const sections: Section[] = [];

  // Macro overrides
  if (overrides.macro) {
    for (const region of ['us', 'eurozone', 'japan', 'em'] as const) {
      const regionValues = overrides.macro[region];
      if (!regionValues) continue;
      const entries: OverrideEntry[] = [];
      for (const [key, value] of Object.entries(regionValues)) {
        if (typeof value !== 'number') continue;
        entries.push({
          key,
          displayName: displayName(key),
          formattedValue: formatValue(key, value),
        });
      }
      if (entries.length > 0) {
        sections.push({
          sectionKey: `macro.${region}`,
          label: SECTION_NAMES[`macro.${region}`] || `Macro - ${region}`,
          entries,
        });
      }
    }
  }

  // Bond overrides (global, hy, em)
  for (const type of ['bonds_global', 'bonds_hy', 'bonds_em'] as const) {
    const group = overrides[type];
    if (!group) continue;
    const entries: OverrideEntry[] = [];
    for (const [key, value] of Object.entries(group)) {
      if (typeof value !== 'number') continue;
      entries.push({
        key,
        displayName: displayName(key),
        formattedValue: formatValue(key, value),
      });
    }
    if (entries.length > 0) {
      sections.push({
        sectionKey: type,
        label: SECTION_NAMES[type],
        entries,
      });
    }
  }

  // Inflation-linked overrides
  if (overrides.inflation_linked) {
    for (const regime of ['usd', 'eur'] as const) {
      const regimeValues = overrides.inflation_linked[regime];
      if (!regimeValues) continue;
      const entries: OverrideEntry[] = [];
      for (const [key, value] of Object.entries(regimeValues)) {
        if (typeof value !== 'number') continue;
        entries.push({
          key,
          displayName: displayName(key),
          formattedValue: formatValue(key, value),
        });
      }
      if (entries.length > 0) {
        sections.push({
          sectionKey: `inflation_linked.${regime}`,
          label: SECTION_NAMES[`inflation_linked.${regime}`],
          entries,
        });
      }
    }
  }

  // Equity overrides
  for (const region of ['equity_us', 'equity_europe', 'equity_japan', 'equity_em'] as const) {
    const group = overrides[region];
    if (!group) continue;
    const entries: OverrideEntry[] = [];
    for (const [key, value] of Object.entries(group)) {
      if (typeof value !== 'number') continue;
      entries.push({
        key,
        displayName: displayName(key),
        formattedValue: formatValue(key, value),
      });
    }
    if (entries.length > 0) {
      sections.push({
        sectionKey: region,
        label: SECTION_NAMES[region],
        entries,
      });
    }
  }

  // Absolute return overrides
  if (overrides.absolute_return) {
    const entries: OverrideEntry[] = [];
    for (const [key, value] of Object.entries(overrides.absolute_return)) {
      if (typeof value !== 'number') continue;
      entries.push({
        key,
        displayName: displayName(key),
        formattedValue: formatValue(key, value),
      });
    }
    if (entries.length > 0) {
      sections.push({
        sectionKey: 'absolute_return',
        label: SECTION_NAMES.absolute_return,
        entries,
      });
    }
  }

  return sections;
}

export function InputChangeSummary() {
  const [expanded, setExpanded] = useState(true);

  const macro = useInputStore((s) => s.macro);
  const bonds = useInputStore((s) => s.bonds);
  const equity = useInputStore((s) => s.equity);
  const equityGK = useInputStore((s) => s.equityGK);
  const equityModelType = useInputStore((s) => s.equityModelType);
  const absoluteReturn = useInputStore((s) => s.absoluteReturn);
  const getOverrides = useInputStore((s) => s.getOverrides);

  const sections = useMemo(() => {
    const overrides = getOverrides();
    return buildSections(overrides);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [macro, bonds, equity, equityGK, equityModelType, absoluteReturn, getOverrides]);

  const totalCount = sections.reduce((sum, s) => sum + s.entries.length, 0);

  if (totalCount === 0) return null;

  return (
    <Card className="border-slate-200">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2 text-slate-800">
            <ListChecks className="h-5 w-5 text-slate-500" />
            Active Input Changes
            <Badge variant="secondary" className="ml-1 text-xs">
              {totalCount}
            </Badge>
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded((prev) => !prev)}
            className="h-8 w-8 p-0"
          >
            {expanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardHeader>
      {expanded && (
        <CardContent className="pt-0">
          <div className="space-y-4">
            {sections.map((section) => (
              <div key={section.sectionKey}>
                <div className="flex items-center gap-2 mb-2">
                  <Badge className={sectionColor(section.sectionKey)}>
                    {section.label}
                  </Badge>
                  <span className="text-xs text-slate-400">
                    {section.entries.length} change{section.entries.length !== 1 ? 's' : ''}
                  </span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                  {section.entries.map((entry) => (
                    <div
                      key={`${section.sectionKey}.${entry.key}`}
                      className="flex items-center justify-between px-3 py-2 bg-slate-50 rounded-md border border-slate-100"
                    >
                      <span className="text-sm text-slate-700 truncate mr-2">
                        {entry.displayName}
                      </span>
                      <span className="text-sm font-mono font-medium text-slate-900 whitespace-nowrap">
                        {entry.formattedValue}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-400 mt-3">
            Showing all inputs that differ from default assumptions.
            These changes affect the expected return calculations above.
          </p>
        </CardContent>
      )}
    </Card>
  );
}
