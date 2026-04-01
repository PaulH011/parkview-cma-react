'use client';

import { useState, Fragment } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { ChevronDown, ChevronRight, Info } from 'lucide-react';
import { HoverCard, HoverCardTrigger, HoverCardContent } from '@/components/ui/hover-card';
import { ASSET_DISPLAY_INFO } from '@/lib/types';
import type { AssetClass, CalculateResponse } from '@/lib/types';
import { AssetBreakdown } from './AssetBreakdown';

interface ResultsTableProps {
  results: CalculateResponse | null;
  baseResults: CalculateResponse | null;
  isLoading: boolean;
}

export function ResultsTable({ results, baseResults, isLoading }: ResultsTableProps) {
  const [expandedAsset, setExpandedAsset] = useState<AssetClass | null>(null);

  const toggleAsset = (key: AssetClass) => {
    setExpandedAsset(expandedAsset === key ? null : key);
  };
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-800" />
      </div>
    );
  }

  if (!results) {
    return (
      <div className="text-center py-8 text-slate-500">
        No results available
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-slate-500 flex items-center gap-1">
        <ChevronRight className="h-3 w-3" />
        Click any row to see formula breakdown and attribution
      </p>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[200px]">Asset Class</TableHead>
            <TableHead className="text-right">Nominal Return</TableHead>
            <TableHead className="text-right">
              <HoverCard openDelay={200}>
                <HoverCardTrigger asChild>
                  <span className="cursor-help border-b border-dotted border-slate-400 inline-flex items-center gap-1">
                    Real Return
                    <Info className="h-3 w-3 text-slate-400" />
                  </span>
                </HoverCardTrigger>
                <HoverCardContent className="text-xs w-56 font-normal text-left">
                  Real returns use each region&apos;s local inflation rate, not base currency inflation.
                </HoverCardContent>
              </HoverCard>
            </TableHead>
            <TableHead className="text-right">Volatility</TableHead>
            <TableHead className="text-right">vs Default</TableHead>
          </TableRow>
        </TableHeader>
      <TableBody>
        {ASSET_DISPLAY_INFO.map((asset) => {
          const result = results.results[asset.key];
          const baseResult = baseResults?.results[asset.key];

          if (!result) return null;

          const nominalPct = result.expected_return_nominal * 100;
          const realPct = result.expected_return_real * 100;
          const volatilityPct = asset.volatility * 100;
          const isExpanded = expandedAsset === asset.key;

          const diff = baseResult
            ? (result.expected_return_nominal - baseResult.expected_return_nominal) * 100
            : 0;

          return (
            <Fragment key={asset.key}>
              <TableRow
                className={`cursor-pointer transition-colors hover:bg-slate-50 ${
                  isExpanded ? 'bg-slate-100 border-b-0' : ''
                }`}
                onClick={() => toggleAsset(asset.key)}
              >
                <TableCell className="font-medium">
                  <div className="flex items-center">
                    <span className="mr-2 text-slate-400 transition-transform duration-200">
                      {isExpanded ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )}
                    </span>
                    <span className="mr-2">{asset.icon}</span>
                    {asset.name}
                  </div>
                </TableCell>
                <TableCell className="text-right font-semibold">
                  {nominalPct.toFixed(2)}%
                </TableCell>
                <TableCell className="text-right text-slate-600">
                  {realPct.toFixed(2)}%
                </TableCell>
                <TableCell className="text-right text-slate-500">
                  {volatilityPct.toFixed(1)}%
                </TableCell>
                <TableCell className="text-right">
                  {Math.abs(diff) < 0.01 ? (
                    <span className="text-slate-400">—</span>
                  ) : diff > 0 ? (
                    <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                      +{diff.toFixed(2)}%
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
                      {diff.toFixed(2)}%
                    </Badge>
                  )}
                </TableCell>
              </TableRow>
              {/* Inline breakdown row */}
              {isExpanded && (
                <tr>
                  <td colSpan={5} className="p-0 border-b border-slate-200">
                    <AssetBreakdown
                      assetKey={asset.key}
                      result={result}
                      isOpen={true}
                    />
                  </td>
                </tr>
              )}
            </Fragment>
          );
        })}
      </TableBody>
      </Table>
    </div>
  );
}
