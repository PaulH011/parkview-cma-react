'use client';

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { ArrowRightLeft, Info } from 'lucide-react';
import type { CalculateResponse, AssetClass } from '@/lib/types';

interface FxExplanationProps {
  results: CalculateResponse;
}

// Which assets carry each foreign-currency FX adjustment (regime/base assets
// like Liquidity, Bonds Global, and Absolute Return never get an FX term)
const FX_AFFECTED_ASSETS: Record<string, string[]> = {
  usd: ['Bonds HY', 'Bonds EM', 'Equity US'],
  eur: ['Equity Europe'],
  jpy: ['Equity Japan'],
  em: ['Equity EM'],
};

function formatPct(value: number): string {
  const pct = value * 100;
  const sign = pct >= 0 ? '+' : '';
  return `${sign}${pct.toFixed(2)}%`;
}

export function FxExplanation({ results }: FxExplanationProps) {
  const fxData = results.fx_forecasts;
  if (!fxData || Object.keys(fxData).length === 0) return null;

  const base = (results.base_currency || 'eur').toUpperCase();

  // Check which individual assets actually have an fx_return component
  const assetsWithFx: { name: string; fxReturn: number }[] = [];
  const ASSET_NAMES: Record<string, string> = {
    liquidity: 'Liquidity',
    bonds_global: 'Bonds Global',
    bonds_hy: 'Bonds HY',
    bonds_em: 'Bonds EM',
    inflation_linked: 'Bonds Inflation Linked',
    equity_us: 'Equity US',
    equity_europe: 'Equity Europe',
    equity_japan: 'Equity Japan',
    equity_em: 'Equity EM',
    absolute_return: 'Absolute Return',
  };

  for (const [key, result] of Object.entries(results.results)) {
    if (!result) continue;
    const fxComponent = result.components?.fx_return;
    if (fxComponent && Math.abs(fxComponent) > 0.0001) {
      assetsWithFx.push({
        name: ASSET_NAMES[key] || key,
        fxReturn: fxComponent,
      });
    }
  }

  return (
    <div className="space-y-4">
      {/* Methodology explanation */}
      <div className="flex items-start gap-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <Info className="h-4 w-4 text-blue-600 mt-0.5 shrink-0" />
        <div className="space-y-2 text-sm">
          <p className="text-blue-900 font-medium">
            {base} Base Currency — FX-Adjusted Returns
          </p>
          <p className="text-blue-800">
            All non-{base} asset returns include an FX adjustment using RA&apos;s PPP-based methodology.
            The expected FX change is a weighted combination of:
          </p>
          <div className="font-mono text-xs bg-white px-3 py-2 rounded border border-blue-200 text-blue-900">
            E[FX] = 30% &times; ({base} T-Bill &minus; Foreign T-Bill) + 70% &times; ({base} Inflation &minus; Foreign Inflation)
          </div>
          <p className="text-blue-700 text-xs">
            Positive FX change = {base} expected to depreciate vs. that currency, which <strong>adds</strong> to foreign asset returns in {base} terms.
          </p>
        </div>
      </div>

      {/* FX Forecasts table */}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[120px]">Currency Pair</TableHead>
            <TableHead className="text-right">Carry (30%)</TableHead>
            <TableHead className="text-right">PPP (70%)</TableHead>
            <TableHead className="text-right">Total FX</TableHead>
            <TableHead>Affected Assets</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {Object.entries(fxData).map(([ccy, data]) => {
            const total = data.fx_change;
            return (
              <TableRow key={ccy}>
                <TableCell className="font-medium">
                  <div className="flex items-center gap-1.5">
                    <ArrowRightLeft className="h-3 w-3 text-slate-400" />
                    {`${base} / ${ccy.toUpperCase()}`}
                  </div>
                </TableCell>
                <TableCell className="text-right font-mono text-sm">
                  <span className={data.carry_component >= 0 ? 'text-green-700' : 'text-red-700'}>
                    {formatPct(data.carry_component)}
                  </span>
                </TableCell>
                <TableCell className="text-right font-mono text-sm">
                  <span className={data.ppp_component >= 0 ? 'text-green-700' : 'text-red-700'}>
                    {formatPct(data.ppp_component)}
                  </span>
                </TableCell>
                <TableCell className="text-right font-mono text-sm font-semibold">
                  <span className={total >= 0 ? 'text-green-700' : 'text-red-700'}>
                    {formatPct(total)}
                  </span>
                </TableCell>
                <TableCell>
                  <div className="flex flex-wrap gap-1">
                    {(FX_AFFECTED_ASSETS[ccy] || []).map((asset) => (
                      <Badge
                        key={asset}
                        variant="outline"
                        className="text-xs bg-slate-50 text-slate-600"
                      >
                        {asset}
                      </Badge>
                    ))}
                  </div>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>

      {/* Per-asset FX impact summary */}
      {assetsWithFx.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {assetsWithFx.map((asset) => (
            <div
              key={asset.name}
              className="flex items-center justify-between p-2 bg-slate-50 rounded-lg border text-sm"
            >
              <span className="text-slate-700">{asset.name}</span>
              <span
                className={`font-mono font-medium ${
                  asset.fxReturn >= 0 ? 'text-green-700' : 'text-red-700'
                }`}
              >
                {formatPct(asset.fxReturn)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
