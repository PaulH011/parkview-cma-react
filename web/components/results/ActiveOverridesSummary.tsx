'use client';

import { useMemo } from 'react';
import { AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { AssetClass, AssetResult } from '@/lib/types';

interface ActiveOverridesSummaryProps {
  results: Partial<Record<AssetClass, AssetResult>>;
}

// Asset class display names
const ASSET_DISPLAY_NAMES: Record<string, string> = {
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

export function ActiveOverridesSummary({ results }: ActiveOverridesSummaryProps) {
  // Collect all macro overrides and which assets they affect
  const overrideImpacts = useMemo(() => {
    const impacts: Map<string, { 
      value: number; 
      affectedAssets: string[];
      isDirectOverride: boolean;
    }> = new Map();
    
    for (const [assetKey, result] of Object.entries(results)) {
      if (!result.macro_dependencies) continue;
      
      for (const [depKey, dep] of Object.entries(result.macro_dependencies)) {
        if (dep.source === 'override' || dep.source === 'affected_by_override') {
          const existing = impacts.get(dep.macro_input);
          if (existing) {
            existing.affectedAssets.push(assetKey);
            if (dep.source === 'override') {
              existing.isDirectOverride = true;
            }
          } else {
            impacts.set(dep.macro_input, {
              value: dep.value_used,
              affectedAssets: [assetKey],
              isDirectOverride: dep.source === 'override',
            });
          }
        }
      }
    }
    
    return impacts;
  }, [results]);
  
  if (overrideImpacts.size === 0) return null;
  
  return (
    <Card className="mb-4 border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50">
      <CardHeader className="pb-2">
        <CardTitle className="text-amber-800 flex items-center gap-2 text-base">
          <AlertCircle className="h-5 w-5" />
          Active Macro Overrides Affecting Returns
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {Array.from(overrideImpacts.entries()).map(([input, data]) => (
            <div 
              key={input} 
              className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 bg-white rounded-lg border border-amber-100"
            >
              <div className="flex items-center gap-2">
                <Badge 
                  className={data.isDirectOverride 
                    ? "bg-blue-100 text-blue-700 border-blue-300" 
                    : "bg-amber-100 text-amber-700 border-amber-300"
                  }
                >
                  {data.isDirectOverride ? 'Override' : 'Computed'}
                </Badge>
                <span className="font-medium text-slate-800">
                  {formatMacroInputKey(input)}
                </span>
                <span className="font-mono text-sm text-slate-600">
                  = {(data.value * 100).toFixed(2)}%
                </span>
              </div>
              <div className="flex flex-wrap gap-1">
                <span className="text-xs text-slate-500 mr-1">Affects:</span>
                {data.affectedAssets.map(asset => (
                  <Badge 
                    key={asset} 
                    variant="outline" 
                    className="text-xs bg-slate-50"
                  >
                    {ASSET_DISPLAY_NAMES[asset] || asset}
                  </Badge>
                ))}
              </div>
            </div>
          ))}
        </div>
        <p className="text-xs text-amber-700 mt-3">
          Macro overrides propagate through calculations to affect multiple asset class returns.
          Click on any asset row to see detailed macro dependencies.
        </p>
      </CardContent>
    </Card>
  );
}
