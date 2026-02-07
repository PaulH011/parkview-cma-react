'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { MacroInputPanel } from '@/components/inputs/MacroInputPanel';
import { BondInputPanel } from '@/components/inputs/BondInputPanel';
import { EquityInputPanel } from '@/components/inputs/EquityInputPanel';
import { AlternativesInputPanel } from '@/components/inputs/AlternativesInputPanel';
import { ResultsTable } from '@/components/results/ResultsTable';
import { RiskReturnChart } from '@/components/results/RiskReturnChart';
import { ExportButton } from '@/components/results/ExportButton';
import { ActiveOverridesSummary } from '@/components/results/ActiveOverridesSummary';
import { ScenarioManager } from '@/components/scenarios/ScenarioManager';
import { useCalculation } from '@/hooks/useCalculation';
import { useInputStore } from '@/stores/inputStore';
import { useAuthStore } from '@/stores/authStore';
import { getLastRefresh } from '@/lib/api';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { RefreshCw, AlertTriangle, X } from 'lucide-react';

/**
 * Determine the most recent calendar quarter-end relative to a given date.
 * Quarter-end dates: March 31, June 30, September 30, December 31
 */
function getMostRecentQuarterEnd(date: Date): Date {
  const year = date.getFullYear();
  const month = date.getMonth(); // 0-based

  // Quarter end months: 2 (Mar), 5 (Jun), 8 (Sep), 11 (Dec)
  const quarterEndMonths = [2, 5, 8, 11];
  const quarterEndDays = [31, 30, 30, 31];

  for (let i = quarterEndMonths.length - 1; i >= 0; i--) {
    const qMonth = quarterEndMonths[i];
    const qDay = quarterEndDays[i];
    const qEnd = new Date(year, qMonth, qDay, 23, 59, 59);
    if (date >= qEnd) {
      return qEnd;
    }
  }

  // If before March 31 of current year, the most recent quarter-end is Dec 31 of previous year
  return new Date(year - 1, 11, 31, 23, 59, 59);
}

/**
 * Get the quarter label (e.g., "Q4 2025") for a given quarter-end date.
 */
function getQuarterLabel(quarterEnd: Date): string {
  const month = quarterEnd.getMonth();
  const year = quarterEnd.getFullYear();
  if (month === 2) return `Q1 ${year}`;
  if (month === 5) return `Q2 ${year}`;
  if (month === 8) return `Q3 ${year}`;
  return `Q4 ${year}`;
}

export default function Dashboard() {
  const { results, baseResults, isLoading, error, calculate } = useCalculation();
  const baseCurrency = useInputStore((state) => state.baseCurrency);
  const macro = useInputStore((state) => state.macro);
  const bonds = useInputStore((state) => state.bonds);
  const equity = useInputStore((state) => state.equity);
  const absoluteReturn = useInputStore((state) => state.absoluteReturn);
  const advancedMode = useInputStore((state) => state.advancedMode);
  const setAdvancedMode = useInputStore((state) => state.setAdvancedMode);
  const fetchDefaultsFromAPI = useInputStore((state) => state.fetchDefaultsFromAPI);
  const isSuperUser = useAuthStore((state) => state.isSuperUser);

  // Quarterly refresh banner state
  const [showRefreshBanner, setShowRefreshBanner] = useState(false);
  const [bannerQuarter, setBannerQuarter] = useState('');
  const [lastRefreshDate, setLastRefreshDate] = useState<string | null>(null);

  // Fetch dynamic defaults from API on mount
  useEffect(() => {
    fetchDefaultsFromAPI();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Check quarterly refresh banner (super user only)
  useEffect(() => {
    if (!isSuperUser) {
      setShowRefreshBanner(false);
      return;
    }

    const checkQuarterlyRefresh = async () => {
      try {
        const { last_refresh } = await getLastRefresh();
        setLastRefreshDate(last_refresh);

        const now = new Date();
        const mostRecentQEnd = getMostRecentQuarterEnd(now);
        const quarterLabel = getQuarterLabel(mostRecentQEnd);

        if (!last_refresh) {
          // No refresh has ever been done
          setShowRefreshBanner(true);
          setBannerQuarter(quarterLabel);
          return;
        }

        const lastRefreshDt = new Date(last_refresh);
        if (lastRefreshDt < mostRecentQEnd) {
          // Last refresh was before the most recent quarter-end
          setShowRefreshBanner(true);
          setBannerQuarter(quarterLabel);
        }
      } catch {
        // Non-critical - just don't show the banner
      }
    };

    checkQuarterlyRefresh();
  }, [isSuperUser]);

  // Recalculate when inputs change (debounced)
  useEffect(() => {
    const timeout = setTimeout(() => {
      calculate();
    }, 500);
    return () => clearTimeout(timeout);
  }, [macro, bonds, equity, absoluteReturn, baseCurrency]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="space-y-6">
      {/* Quarterly Refresh Banner (super user only) */}
      {showRefreshBanner && (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 text-amber-500 shrink-0" />
              <div>
                <p className="text-sm font-medium text-amber-800">
                  {bannerQuarter} has ended. Default assumptions were last refreshed
                  {lastRefreshDate
                    ? ` on ${new Date(lastRefreshDate).toLocaleDateString()}`
                    : ' never'}
                  . Time to review for quarterly updates.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Link href="/admin/refresh">
                <Button size="sm" variant="default">
                  Review Now
                </Button>
              </Link>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setShowRefreshBanner(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-12 gap-6">
      {/* Left Panel: Inputs */}
      <div className="col-span-12 lg:col-span-4">
        <Card className="sticky top-20">
          <CardHeader className="pb-3">
            <div className="flex flex-col gap-2">
              <CardTitle className="text-lg">Input Assumptions</CardTitle>
              <ScenarioManager />
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[calc(100vh-220px)]">
              <div className="px-6 pb-6">
                {/* Advanced Mode Toggle */}
                <div className="flex items-center justify-between mb-4">
                  <Label htmlFor="advanced-mode" className="text-sm font-medium">
                    Advanced Mode
                  </Label>
                  <Switch
                    id="advanced-mode"
                    checked={advancedMode}
                    onCheckedChange={setAdvancedMode}
                  />
                </div>

                <Tabs defaultValue="macro" className="w-full">
                  <TabsList className="grid w-full grid-cols-4">
                    <TabsTrigger value="macro" className="text-xs">Macro</TabsTrigger>
                    <TabsTrigger value="bonds" className="text-xs">Bonds</TabsTrigger>
                    <TabsTrigger value="equity" className="text-xs">Equity</TabsTrigger>
                    <TabsTrigger value="alt" className="text-xs">Alt</TabsTrigger>
                  </TabsList>

                  <TabsContent value="macro" className="mt-4">
                    <MacroInputPanel />
                  </TabsContent>

                  <TabsContent value="bonds" className="mt-4">
                    <BondInputPanel />
                  </TabsContent>

                  <TabsContent value="equity" className="mt-4">
                    <EquityInputPanel />
                  </TabsContent>

                  <TabsContent value="alt" className="mt-4">
                    <AlternativesInputPanel />
                  </TabsContent>
                </Tabs>
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {/* Right Panel: Results */}
      <div className="col-span-12 lg:col-span-8 space-y-6">
        {/* Error Display */}
        {error && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="py-4">
              <p className="text-red-700 text-sm">{error}</p>
              <Button
                variant="outline"
                size="sm"
                onClick={calculate}
                className="mt-2"
              >
                <RefreshCw className="h-3 w-3 mr-1" />
                Retry
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Active Macro Overrides Summary */}
        {results?.results && (
          <ActiveOverridesSummary results={results.results} />
        )}

        {/* Results Table */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">
                Expected Returns (10-Year, {baseCurrency.toUpperCase()} Base)
              </CardTitle>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={calculate}
                  disabled={isLoading}
                >
                  <RefreshCw className={`h-3 w-3 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
                <ExportButton results={results} baseResults={baseResults} />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <ResultsTable
              results={results}
              baseResults={baseResults}
              isLoading={isLoading}
            />
          </CardContent>
        </Card>

        {/* Risk-Return Chart */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">Risk-Return Profile</CardTitle>
          </CardHeader>
          <CardContent>
            <RiskReturnChart results={results} baseResults={baseResults} isLoading={isLoading} />
          </CardContent>
        </Card>

        {/* Macro Forecasts Summary */}
        {results?.macro_forecasts && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Macro Forecasts</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(results.macro_forecasts).map(([region, data]) => (
                  <div key={region} className="text-center p-3 bg-slate-50 rounded-lg">
                    <h4 className="font-medium text-slate-700 capitalize mb-2">
                      {region === 'em' ? 'EM' : region === 'eurozone' ? 'Eurozone' : region.charAt(0).toUpperCase() + region.slice(1)}
                    </h4>
                    <div className="space-y-1 text-sm">
                      <p>
                        <span className="text-slate-500">GDP:</span>{' '}
                        <span className="font-medium">{(data.rgdp_growth * 100).toFixed(2)}%</span>
                      </p>
                      <p>
                        <span className="text-slate-500">Infl:</span>{' '}
                        <span className="font-medium">{(data.inflation * 100).toFixed(2)}%</span>
                      </p>
                      <p>
                        <span className="text-slate-500">T-Bill:</span>{' '}
                        <span className="font-medium">{(data.tbill_rate * 100).toFixed(2)}%</span>
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
    </div>
  );
}
