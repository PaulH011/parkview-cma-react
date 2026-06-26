'use client';

import { useMemo } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { HoverCard, HoverCardTrigger, HoverCardContent } from '@/components/ui/hover-card';
import { Info, ArrowUp, ArrowDown } from 'lucide-react';
import { ASSET_DISPLAY_INFO } from '@/lib/types';
import type { AssetClass, CalculateResponse, BaseCurrency } from '@/lib/types';
import {
  BENCHMARKS,
  BENCHMARK_PROVIDER_IDS,
  getBenchmark,
  type BenchmarkProviderId,
} from '@/lib/benchmarks';

interface BenchmarkComparisonProps {
  results: CalculateResponse | null;
  baseCurrency: BaseCurrency;
  isLoading: boolean;
}

// Short column labels (full name lives in the header hover-card)
const PROVIDER_LABEL: Record<BenchmarkProviderId, string> = {
  blackrock: 'BlackRock',
  jpmorgan: 'J.P. Morgan',
  ssga: 'State Street',
};

function fmtPct(v: number | null | undefined, dp = 1): string {
  return v === null || v === undefined ? '—' : `${v.toFixed(dp)}%`;
}

export function BenchmarkComparison({
  results,
  baseCurrency,
  isLoading,
}: BenchmarkComparisonProps) {
  // Per-bucket consensus = mean of available provider values for this currency.
  const rows = useMemo(() => {
    return ASSET_DISPLAY_INFO.map((asset) => {
      const result = results?.results[asset.key];
      const yourNominal = result ? result.expected_return_nominal * 100 : null;

      const providerValues: Record<BenchmarkProviderId, number | null> =
        BENCHMARK_PROVIDER_IDS.reduce(
          (acc, id) => {
            acc[id] = getBenchmark(id, baseCurrency, asset.key)?.value ?? null;
            return acc;
          },
          {} as Record<BenchmarkProviderId, number | null>,
        );

      const available = BENCHMARK_PROVIDER_IDS.map((id) => providerValues[id]).filter(
        (v): v is number => v !== null,
      );
      const consensus =
        available.length > 0
          ? available.reduce((a, b) => a + b, 0) / available.length
          : null;
      const delta =
        yourNominal !== null && consensus !== null ? yourNominal - consensus : null;

      return { asset, yourNominal, providerValues, consensus, delta };
    });
  }, [results, baseCurrency]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-800" />
      </div>
    );
  }

  if (!results) {
    return <div className="text-center py-8 text-slate-500">No results available</div>;
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-slate-500">
        Your computed 10-year <span className="font-medium">nominal</span> returns vs. the latest
        public CMAs, {baseCurrency.toUpperCase()} base. Bases differ — hover each provider for
        method, horizon and as-of date.
      </p>

      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[190px]">Asset Class</TableHead>
              <TableHead className="text-right whitespace-nowrap">Your Tool</TableHead>
              {BENCHMARK_PROVIDER_IDS.map((id) => {
                const p = BENCHMARKS.providers[id];
                return (
                  <TableHead key={id} className="text-right whitespace-nowrap">
                    <HoverCard openDelay={150}>
                      <HoverCardTrigger asChild>
                        <span className="cursor-help border-b border-dotted border-slate-400 inline-flex items-center gap-1">
                          {PROVIDER_LABEL[id]}
                          <Info className="h-3 w-3 text-slate-400" />
                        </span>
                      </HoverCardTrigger>
                      <HoverCardContent className="text-xs w-72 font-normal text-left space-y-1">
                        <p className="font-semibold">{p.name}</p>
                        <p className="text-slate-500">{p.publication}</p>
                        <p>
                          <span className="text-slate-500">As of:</span> {p.as_of}
                          {'  ·  '}
                          <span className="text-slate-500">Horizon:</span> {p.horizon}
                          {'  ·  '}
                          <span className="text-slate-500">Basis:</span> {p.return_basis}
                        </p>
                        <p className="text-slate-600">{p.notes}</p>
                      </HoverCardContent>
                    </HoverCard>
                  </TableHead>
                );
              })}
              <TableHead className="text-right whitespace-nowrap">
                <HoverCard openDelay={150}>
                  <HoverCardTrigger asChild>
                    <span className="cursor-help border-b border-dotted border-slate-400 inline-flex items-center gap-1">
                      vs Consensus
                      <Info className="h-3 w-3 text-slate-400" />
                    </span>
                  </HoverCardTrigger>
                  <HoverCardContent className="text-xs w-60 font-normal text-left">
                    Your tool minus the average of the available providers for this asset. Higher
                    (↑) or lower (↓) than the industry mean — not a judgment of correctness.
                  </HoverCardContent>
                </HoverCard>
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map(({ asset, yourNominal, providerValues, delta }) => (
              <TableRow key={asset.key} className="hover:bg-slate-50">
                <TableCell className="font-medium">
                  <div className="flex items-center">
                    <span className="mr-2">{asset.icon}</span>
                    {asset.name}
                  </div>
                </TableCell>
                <TableCell className="text-right font-semibold">
                  {fmtPct(yourNominal, 2)}
                </TableCell>
                {BENCHMARK_PROVIDER_IDS.map((id) => {
                  const cell = getBenchmark(id, baseCurrency, asset.key);
                  const v = providerValues[id];
                  return (
                    <TableCell key={id} className="text-right text-slate-600">
                      {v === null && cell ? (
                        <HoverCard openDelay={150}>
                          <HoverCardTrigger asChild>
                            <span className="cursor-help text-slate-300">—</span>
                          </HoverCardTrigger>
                          <HoverCardContent className="text-xs w-52 font-normal text-left">
                            No comparable {PROVIDER_LABEL[id]} line for this bucket
                            {cell.proxy ? ` (${cell.proxy})` : ''}.
                          </HoverCardContent>
                        </HoverCard>
                      ) : (
                        fmtPct(v)
                      )}
                    </TableCell>
                  );
                })}
                <TableCell className="text-right">
                  {delta === null ? (
                    <span className="text-slate-400">—</span>
                  ) : (
                    <span
                      className={`inline-flex items-center gap-0.5 text-xs font-medium ${
                        delta >= 0 ? 'text-sky-700' : 'text-amber-700'
                      }`}
                    >
                      {delta >= 0 ? (
                        <ArrowUp className="h-3 w-3" />
                      ) : (
                        <ArrowDown className="h-3 w-3" />
                      )}
                      {Math.abs(delta).toFixed(1)}%
                    </span>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Caveats */}
      <div className="text-[11px] leading-relaxed text-slate-400 border-t border-slate-100 pt-2 space-y-1">
        <p>
          <span className="font-medium text-slate-500">Read before comparing:</span>{' '}
          BlackRock &amp; J.P. Morgan returns are geometric; State Street is arithmetic (~0.5·σ²
          higher for equities). J.P. Morgan&apos;s horizon is 10–15y vs the tool&apos;s 10y.
          Figures are nominal; non-base-currency bonds are currency-hedged, and State Street
          equities are local-currency (no FX) with no standalone Japan line.
        </p>
        <p>
          Each cell maps to the closest provider proxy. Mapped via{' '}
          <span className="font-mono">scripts/refresh_benchmarks.py</span> · snapshot{' '}
          {BENCHMARKS.generated}.
        </p>
      </div>
    </div>
  );
}
