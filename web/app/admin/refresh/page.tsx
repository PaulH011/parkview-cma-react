'use client';

import { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertTriangle,
  ArrowLeft,
  Search,
  Download,
  History,
  RotateCcw,
  Beaker,
} from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import {
  researchDefaults,
  applyDefaults,
  revertDefaults,
  getRefreshHistory,
} from '@/lib/api';
import type { ResearchComparison, RefreshHistoryEntry } from '@/lib/api';

type CategoryFilter = 'all' | 'Macro' | 'Bonds' | 'Equity' | 'Alternatives';

export default function AdminRefreshPage() {
  const router = useRouter();
  const { user, isSuperUser } = useAuthStore();

  // Research state
  const [isResearching, setIsResearching] = useState(false);
  const [comparisons, setComparisons] = useState<ResearchComparison[]>([]);
  const [logId, setLogId] = useState<string | null>(null);
  const [researchedAt, setResearchedAt] = useState<string | null>(null);
  const [isTestMode, setIsTestMode] = useState(false);

  // Selection state
  const [accepted, setAccepted] = useState<Record<string, boolean>>({});

  // Filter state
  const [categoryFilter, setCategoryFilter] = useState<CategoryFilter>('all');

  // Apply state
  const [isApplying, setIsApplying] = useState(false);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [applyResult, setApplyResult] = useState<string | null>(null);

  // Revert state
  const [isReverting, setIsReverting] = useState(false);
  const [showRevertDialog, setShowRevertDialog] = useState(false);

  // History state
  const [history, setHistory] = useState<RefreshHistoryEntry[]>([]);
  const [showHistory, setShowHistory] = useState(false);

  // Error state
  const [error, setError] = useState<string | null>(null);

  // Check access
  useEffect(() => {
    if (!isSuperUser && user !== null) {
      router.push('/');
    }
  }, [isSuperUser, user, router]);

  // Load history on mount
  useEffect(() => {
    if (user?.email && isSuperUser) {
      loadHistory();
    }
  }, [user, isSuperUser]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadHistory = async () => {
    if (!user?.email) return;
    try {
      const data = await getRefreshHistory(user.email);
      setHistory(data.history);
    } catch {
      // History load failure is non-critical
    }
  };

  // Filtered comparisons
  const filteredComparisons = useMemo(() => {
    if (categoryFilter === 'all') return comparisons;
    return comparisons.filter((c) => c.category === categoryFilter);
  }, [comparisons, categoryFilter]);

  // Count accepted
  const acceptedCount = Object.values(accepted).filter(Boolean).length;
  const filteredAcceptedCount = filteredComparisons.filter((c) => accepted[c.key]).length;

  // Research handler
  const handleResearch = async (testMode: boolean) => {
    if (!user?.email) return;
    setError(null);
    setIsResearching(true);
    setIsTestMode(testMode);
    setComparisons([]);
    setAccepted({});
    setApplyResult(null);

    try {
      const result = await researchDefaults(user.email, testMode);
      setComparisons(result.comparisons);
      setLogId(result.log_id);
      setResearchedAt(result.researched_at);

      // Pre-select top 5 biggest changes
      const preSelected: Record<string, boolean> = {};
      result.comparisons.forEach((c, i) => {
        preSelected[c.key] = i < 5;
      });
      setAccepted(preSelected);
    } catch (err: any) {
      setError(err.message || 'Research failed');
    } finally {
      setIsResearching(false);
    }
  };

  // Toggle individual acceptance
  const toggleAccepted = (key: string) => {
    setAccepted((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  // Select all / deselect all
  const selectAll = () => {
    const newAccepted: Record<string, boolean> = { ...accepted };
    filteredComparisons.forEach((c) => {
      newAccepted[c.key] = true;
    });
    setAccepted(newAccepted);
  };

  const deselectAll = () => {
    const newAccepted: Record<string, boolean> = { ...accepted };
    filteredComparisons.forEach((c) => {
      newAccepted[c.key] = false;
    });
    setAccepted(newAccepted);
  };

  // Apply handler
  const handleApply = async () => {
    if (!user?.email) return;
    setShowConfirmDialog(false);
    setIsApplying(true);
    setError(null);

    const changes = comparisons
      .filter((c) => accepted[c.key] && c.suggested_value !== null)
      .map((c) => ({
        key: c.key,
        new_value: c.suggested_value!,
      }));

    try {
      const result = await applyDefaults(user.email, changes, isTestMode);
      setApplyResult(
        `Successfully applied ${result.changes_applied} changes${isTestMode ? ' (Test Mode)' : ''}.`
      );
      loadHistory();
    } catch (err: any) {
      setError(err.message || 'Failed to apply changes');
    } finally {
      setIsApplying(false);
    }
  };

  // Revert handler
  const handleRevert = async () => {
    if (!user?.email) return;
    setShowRevertDialog(false);
    setIsReverting(true);
    setError(null);

    try {
      await revertDefaults(user.email);
      setApplyResult('Reverted to original hardcoded defaults.');
      loadHistory();
    } catch (err: any) {
      setError(err.message || 'Failed to revert');
    } finally {
      setIsReverting(false);
    }
  };

  // Format value with unit
  const formatValue = (value: number | null, unit: string) => {
    if (value === null) return 'N/A';
    if (unit === '%') return `${value.toFixed(2)}%`;
    if (unit === 'x') return `${value.toFixed(1)}x`;
    if (unit === 'years') return `${value.toFixed(1)}y`;
    return value.toFixed(2);
  };

  // Confidence badge color
  const confidenceColor = (conf: string) => {
    if (conf === 'high') return 'default';
    if (conf === 'medium') return 'secondary';
    return 'destructive';
  };

  if (!isSuperUser) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Card className="p-8">
          <p className="text-slate-500">Access restricted to super users.</p>
          <Button variant="outline" className="mt-4" onClick={() => router.push('/')}>
            <ArrowLeft className="h-4 w-4 mr-2" /> Back to Dashboard
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-[1400px] mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" onClick={() => router.push('/')}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <h1 className="text-2xl font-bold text-slate-800">
              Quarterly Assumption Refresh
            </h1>
          </div>
          {researchedAt && (
            <p className="text-sm text-slate-500 mt-1 ml-12">
              Last researched: {new Date(researchedAt).toLocaleString()}
              {isTestMode && (
                <Badge variant="outline" className="ml-2 text-amber-600 border-amber-300">
                  Test Mode
                </Badge>
              )}
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowHistory(!showHistory)}
          >
            <History className="h-4 w-4 mr-1" />
            History
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowRevertDialog(true)}
            disabled={isReverting}
          >
            <RotateCcw className="h-4 w-4 mr-1" />
            Revert to Original
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="py-4 flex items-center gap-2">
            <XCircle className="h-5 w-5 text-red-500" />
            <p className="text-red-700 text-sm">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Success Display */}
      {applyResult && (
        <Card className="border-green-200 bg-green-50">
          <CardContent className="py-4 flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-green-500" />
            <p className="text-green-700 text-sm">{applyResult}</p>
          </CardContent>
        </Card>
      )}

      {/* Research Buttons */}
      {comparisons.length === 0 && !isResearching && (
        <Card>
          <CardContent className="py-12 text-center">
            <Search className="h-12 w-12 text-slate-300 mx-auto mb-4" />
            <h2 className="text-lg font-semibold text-slate-700 mb-2">
              Research Current Market Data
            </h2>
            <p className="text-sm text-slate-500 mb-6 max-w-md mx-auto">
              Use AI to research the latest market values for all {71} default assumptions.
              The results will be compared against current defaults so you can review
              and selectively apply changes.
            </p>
            <div className="flex gap-3 justify-center">
              <Button onClick={() => handleResearch(false)} size="lg">
                <RefreshCw className="h-4 w-4 mr-2" />
                Research Current Market Data
              </Button>
              <Button variant="outline" onClick={() => handleResearch(true)} size="lg">
                <Beaker className="h-4 w-4 mr-2" />
                Simulate Refresh (Test Mode)
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Loading State */}
      {isResearching && (
        <Card>
          <CardContent className="py-16 text-center">
            <RefreshCw className="h-10 w-10 text-blue-500 mx-auto mb-4 animate-spin" />
            <h2 className="text-lg font-semibold text-slate-700 mb-2">
              Researching Market Data...
            </h2>
            <p className="text-sm text-slate-500">
              AI is looking up current values for all assumptions. This may take 30-60 seconds.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Comparison Grid */}
      {comparisons.length > 0 && !isResearching && (
        <>
          {/* Controls Bar */}
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-3">
              {/* Category Filter */}
              <Select
                value={categoryFilter}
                onValueChange={(v) => setCategoryFilter(v as CategoryFilter)}
              >
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Filter by category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  <SelectItem value="Macro">Macro</SelectItem>
                  <SelectItem value="Bonds">Bonds</SelectItem>
                  <SelectItem value="Equity">Equity</SelectItem>
                  <SelectItem value="Alternatives">Alternatives</SelectItem>
                </SelectContent>
              </Select>

              <Separator orientation="vertical" className="h-6" />

              {/* Select All / Deselect All */}
              <Button variant="outline" size="sm" onClick={selectAll}>
                Select All
              </Button>
              <Button variant="outline" size="sm" onClick={deselectAll}>
                Deselect All
              </Button>

              <span className="text-sm text-slate-500">
                {filteredAcceptedCount} of {filteredComparisons.length} selected
              </span>
            </div>

            <div className="flex items-center gap-3">
              {/* Re-research */}
              <Button variant="outline" size="sm" onClick={() => handleResearch(isTestMode)}>
                <RefreshCw className="h-3 w-3 mr-1" />
                Re-research
              </Button>

              {/* Apply Button */}
              <Button
                onClick={() => setShowConfirmDialog(true)}
                disabled={acceptedCount === 0 || isApplying}
              >
                {isApplying ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <CheckCircle className="h-4 w-4 mr-2" />
                )}
                {isTestMode ? 'Apply (Test)' : 'Apply'} {acceptedCount} Changes
              </Button>
            </div>
          </div>

          {/* Table */}
          <Card>
            <ScrollArea className="max-h-[70vh]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-8">#</TableHead>
                    <TableHead className="min-w-[200px]">Assumption</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead className="text-right">Current</TableHead>
                    <TableHead className="text-right">Suggested</TableHead>
                    <TableHead className="text-right">Diff</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead>Conf.</TableHead>
                    <TableHead className="text-center w-16">Accept</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredComparisons.map((c, i) => {
                    const isTopChange = i < 5 && categoryFilter === 'all';
                    return (
                      <TableRow
                        key={c.key}
                        className={isTopChange ? 'bg-amber-50/50' : ''}
                      >
                        <TableCell className="text-xs text-slate-400">{i + 1}</TableCell>
                        <TableCell>
                          <div>
                            <span className="font-medium text-sm">{c.display_name}</span>
                            {c.notes && (
                              <p className="text-xs text-slate-500 mt-0.5 max-w-[250px] truncate" title={c.notes}>
                                {c.notes}
                              </p>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="text-xs">
                            {c.subcategory}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right font-mono text-sm">
                          {formatValue(c.current_value, c.unit)}
                        </TableCell>
                        <TableCell className="text-right font-mono text-sm font-medium">
                          {formatValue(c.suggested_value, c.unit)}
                        </TableCell>
                        <TableCell className="text-right">
                          <span
                            className={`font-mono text-sm font-medium ${
                              c.abs_diff > 0
                                ? 'text-red-600'
                                : c.abs_diff < 0
                                ? 'text-green-600'
                                : 'text-slate-400'
                            }`}
                          >
                            {c.abs_diff > 0 ? '+' : ''}
                            {c.abs_diff.toFixed(2)}
                          </span>
                        </TableCell>
                        <TableCell>
                          <p className="text-xs text-slate-500 max-w-[200px] truncate" title={c.source}>
                            {c.source}
                          </p>
                        </TableCell>
                        <TableCell>
                          <Badge variant={confidenceColor(c.confidence)} className="text-xs">
                            {c.confidence}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center">
                          <Switch
                            checked={!!accepted[c.key]}
                            onCheckedChange={() => toggleAccepted(c.key)}
                          />
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </ScrollArea>
          </Card>
        </>
      )}

      {/* History Panel */}
      {showHistory && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <History className="h-5 w-5" />
              Refresh History
            </CardTitle>
          </CardHeader>
          <CardContent>
            {history.length === 0 ? (
              <p className="text-sm text-slate-500">No refresh history found.</p>
            ) : (
              <div className="space-y-3">
                {history.map((entry) => (
                  <div
                    key={entry.id}
                    className="flex items-center justify-between p-3 rounded-lg bg-slate-50"
                  >
                    <div>
                      <p className="text-sm font-medium">
                        {new Date(entry.initiated_at).toLocaleString()}
                      </p>
                      <p className="text-xs text-slate-500">
                        by {entry.initiated_by}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={
                          entry.status === 'applied'
                            ? 'default'
                            : entry.status === 'test'
                            ? 'secondary'
                            : entry.status === 'pending'
                            ? 'outline'
                            : 'destructive'
                        }
                      >
                        {entry.status}
                      </Badge>
                      {entry.applied_changes_json && !('action' in entry.applied_changes_json) && (
                        <span className="text-xs text-slate-500">
                          {Array.isArray(entry.applied_changes_json)
                            ? `${entry.applied_changes_json.length} changes`
                            : ''}
                        </span>
                      )}
                      {entry.applied_changes_json && 'action' in entry.applied_changes_json && (
                        <span className="text-xs text-slate-500">Reverted</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Confirm Apply Dialog */}
      <Dialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {isTestMode ? 'Apply Changes (Test Mode)' : 'Apply Selected Changes'}
            </DialogTitle>
            <DialogDescription>
              You are about to update {acceptedCount} default assumption
              {acceptedCount !== 1 ? 's' : ''}.
              {isTestMode
                ? ' This is in test mode - you can revert to original defaults at any time.'
                : ' This will affect all users who see the default values.'}
            </DialogDescription>
          </DialogHeader>
          <div className="max-h-[300px] overflow-y-auto space-y-1 py-2">
            {comparisons
              .filter((c) => accepted[c.key])
              .map((c) => (
                <div key={c.key} className="flex justify-between text-sm px-2 py-1 rounded hover:bg-slate-50">
                  <span className="text-slate-600">{c.display_name}</span>
                  <span className="font-mono">
                    {formatValue(c.current_value, c.unit)} {' \u2192 '}
                    <span className="font-medium">{formatValue(c.suggested_value, c.unit)}</span>
                  </span>
                </div>
              ))}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConfirmDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleApply}>
              {isTestMode ? 'Apply (Test)' : 'Apply Changes'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Confirm Revert Dialog */}
      <Dialog open={showRevertDialog} onOpenChange={setShowRevertDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Revert to Original Defaults</DialogTitle>
            <DialogDescription>
              This will remove all custom default values and revert to the original
              hardcoded defaults. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRevertDialog(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleRevert}>
              <RotateCcw className="h-4 w-4 mr-2" />
              Revert to Original
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
