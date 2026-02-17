'use client';

import { useState, useEffect } from 'react';
import { useInputStore } from '@/stores/inputStore';
import { useAuthStore } from '@/stores/authStore';
import type { Overrides, MacroRegion, MacroInputs, InflationLinkedRegimeInputs } from '@/lib/types';
import {
  getScenarios,
  saveScenario,
  deleteScenario,
  searchShareRecipients,
  shareScenario,
  type SavedScenario,
} from '@/lib/scenarios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
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
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Save, FolderOpen, Trash2, Cloud, HardDrive, Loader2, Share2 } from 'lucide-react';
import { toast } from 'sonner';

const ABSOLUTE_RETURN_RAW_KEYS = new Set([
  'beta_market',
  'beta_size',
  'beta_value',
  'beta_profitability',
  'beta_investment',
  'beta_momentum',
]);

const INFLATION_LINKED_RAW_KEYS = new Set(['duration', 'inflation_beta']);
const BOND_RAW_KEYS = new Set(['duration']);
const MACRO_RAW_KEYS = new Set(['my_ratio']);
const GK_RAW_KEYS = new Set(['current_pe', 'target_pe']);

function convertNumberForUi(
  key: string,
  value: number,
  rawKeys: Set<string>
): number {
  return rawKeys.has(key) ? value : value * 100;
}

function convertSavedOverridesToUiUnits(overrides: Overrides): Overrides {
  const converted: Overrides = {};

  if (overrides.macro) {
    converted.macro = {};
    for (const [region, values] of Object.entries(overrides.macro)) {
      if (!values) continue;
      const out: Record<string, number> = {};
      for (const [key, value] of Object.entries(values)) {
        if (typeof value !== 'number') continue;
        out[key] = convertNumberForUi(key, value, MACRO_RAW_KEYS);
      }
      converted.macro[region as MacroRegion] = out as Partial<MacroInputs>;
    }
  }

  const convertBondGroup = (group?: Record<string, unknown>) => {
    if (!group) return undefined;
    const out: Record<string, number> = {};
    for (const [key, value] of Object.entries(group)) {
      if (typeof value !== 'number') continue;
      out[key] = convertNumberForUi(key, value, BOND_RAW_KEYS);
    }
    return out;
  };

  converted.bonds_global = convertBondGroup(overrides.bonds_global) as Overrides['bonds_global'];
  converted.bonds_hy = convertBondGroup(overrides.bonds_hy) as Overrides['bonds_hy'];
  converted.bonds_em = convertBondGroup(overrides.bonds_em) as Overrides['bonds_em'];

  if (overrides.inflation_linked) {
    converted.inflation_linked = {};
    for (const regime of ['usd', 'eur'] as const) {
      const regimeValues = overrides.inflation_linked[regime];
      if (!regimeValues) continue;
      const out: Record<string, number> = {};
      for (const [key, value] of Object.entries(regimeValues)) {
        if (typeof value !== 'number') continue;
        out[key] = convertNumberForUi(key, value, INFLATION_LINKED_RAW_KEYS);
      }
      converted.inflation_linked[regime] = out as Partial<InflationLinkedRegimeInputs>;
    }
  }

  const convertEquityGroup = (group?: Record<string, unknown>) => {
    if (!group) return undefined;
    const out: Record<string, number> = {};
    const isGk = Object.keys(group).some((k) => k === 'current_pe' || k === 'target_pe');
    for (const [key, value] of Object.entries(group)) {
      if (typeof value !== 'number') continue;
      if (isGk) {
        out[key] = convertNumberForUi(key, value, GK_RAW_KEYS);
      } else {
        out[key] = value * 100;
      }
    }
    return out;
  };

  converted.equity_us = convertEquityGroup(overrides.equity_us as Record<string, unknown>) as Overrides['equity_us'];
  converted.equity_europe = convertEquityGroup(overrides.equity_europe as Record<string, unknown>) as Overrides['equity_europe'];
  converted.equity_japan = convertEquityGroup(overrides.equity_japan as Record<string, unknown>) as Overrides['equity_japan'];
  converted.equity_em = convertEquityGroup(overrides.equity_em as Record<string, unknown>) as Overrides['equity_em'];

  if (overrides.absolute_return) {
    const out: Record<string, number> = {};
    for (const [key, value] of Object.entries(overrides.absolute_return)) {
      if (typeof value !== 'number') continue;
      if (key === 'trading_alpha') {
        out[key] = value * 100;
      } else if (ABSOLUTE_RETURN_RAW_KEYS.has(key)) {
        out[key] = value;
      } else {
        out[key] = value;
      }
    }
    converted.absolute_return = out as Overrides['absolute_return'];
  }

  return converted;
}

// Predefined scenario templates
const SCENARIO_TEMPLATES = {
  'bull-market': {
    name: 'Bull Market',
    description: 'Higher growth (+0.5%), lower inflation (-0.3%)',
    overrides: {
      macro: {
        us: { rgdp_growth: 1.70, inflation_forecast: 1.99 },
        eurozone: { rgdp_growth: 1.30, inflation_forecast: 1.76 },
        japan: { rgdp_growth: 0.80, inflation_forecast: 1.35 },
        em: { rgdp_growth: 3.50, inflation_forecast: 3.50 },
      },
    },
  },
  'bear-market': {
    name: 'Bear Market',
    description: 'Lower growth (-1%), higher credit spreads',
    overrides: {
      macro: {
        us: { rgdp_growth: 0.20 },
        eurozone: { rgdp_growth: -0.20 },
        japan: { rgdp_growth: -0.70 },
        em: { rgdp_growth: 2.00 },
      },
    },
  },
  'stagflation': {
    name: 'Stagflation',
    description: 'High inflation (+2%), low growth (-0.5%)',
    overrides: {
      macro: {
        us: { inflation_forecast: 4.29, rgdp_growth: 0.70 },
        eurozone: { inflation_forecast: 4.06, rgdp_growth: 0.30 },
        japan: { inflation_forecast: 3.65, rgdp_growth: -0.20 },
        em: { inflation_forecast: 5.80, rgdp_growth: 2.50 },
      },
    },
  },
  'rising-rates': {
    name: 'Rising Rates',
    description: 'Higher T-Bill (+1.5%), duration impact',
    overrides: {
      macro: {
        us: { tbill_forecast: 5.29 },
        eurozone: { tbill_forecast: 4.20 },
        japan: { tbill_forecast: 2.50 },
        em: { tbill_forecast: 7.00 },
      },
    },
  },
};

export function ScenarioManager() {
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [scenarioName, setScenarioName] = useState('');
  const [savedScenarios, setSavedScenarios] = useState<SavedScenario[]>([]);
  const [isLoadingScenarios, setIsLoadingScenarios] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [scenarioToShare, setScenarioToShare] = useState<SavedScenario | null>(null);
  const [shareQuery, setShareQuery] = useState('');
  const [recipientResults, setRecipientResults] = useState<Array<{ user_id: string; email: string }>>([]);
  const [selectedRecipientEmail, setSelectedRecipientEmail] = useState('');
  const [isSearchingRecipients, setIsSearchingRecipients] = useState(false);
  const [isSharing, setIsSharing] = useState(false);

  const { loadScenario, resetToDefaults, getOverrides, baseCurrency, setBaseCurrency } = useInputStore();
  const { user } = useAuthStore();

  // Load saved scenarios
  useEffect(() => {
    async function loadSavedScenarios() {
      setIsLoadingScenarios(true);
      const scenarios = await getScenarios(user?.id || null);
      setSavedScenarios(scenarios);
      setIsLoadingScenarios(false);
    }
    loadSavedScenarios();
  }, [user?.id]);

  const refreshSavedScenarios = async () => {
    setIsLoadingScenarios(true);
    const scenarios = await getScenarios(user?.id || null);
    setSavedScenarios(scenarios);
    setIsLoadingScenarios(false);
  };

  useEffect(() => {
    if (!shareDialogOpen) return;

    const query = shareQuery.trim();
    if (query.length < 2) {
      setRecipientResults([]);
      return;
    }

    const timeout = setTimeout(async () => {
      setIsSearchingRecipients(true);
      const results = await searchShareRecipients(user?.id || null, query);
      setRecipientResults(results);
      setIsSearchingRecipients(false);
    }, 250);

    return () => clearTimeout(timeout);
  }, [shareQuery, shareDialogOpen, user?.id]);

  const handleLoadTemplate = (templateKey: string) => {
    if (templateKey === 'default') {
      resetToDefaults();
      toast.success('Reset to RA defaults');
      return;
    }

    const template = SCENARIO_TEMPLATES[templateKey as keyof typeof SCENARIO_TEMPLATES];
    if (template) {
      // Convert percentage values back to store format
      const convertedOverrides: { macro: Record<string, Record<string, number>> } = { macro: {} };
      if (template.overrides.macro) {
        for (const [region, values] of Object.entries(template.overrides.macro)) {
          convertedOverrides.macro[region] = {};
          for (const [key, value] of Object.entries(values as Record<string, number>)) {
            convertedOverrides.macro[region][key] = value;
          }
        }
      }

      resetToDefaults();
      loadScenario(convertedOverrides);
      toast.success(`Loaded ${template.name}`);
    }
  };

  const handleLoadSavedScenario = (scenario: SavedScenario) => {
    const normalizedBase = scenario.base_currency?.toLowerCase();
    if (normalizedBase === 'usd' || normalizedBase === 'eur') {
      setBaseCurrency(normalizedBase);
    }
    const overridesForUi = convertSavedOverridesToUiUnits(scenario.overrides as Overrides);
    resetToDefaults();
    loadScenario(overridesForUi);
    toast.success(`Loaded "${scenario.name}"`);
  };

  const handleDeleteScenario = async (scenario: SavedScenario) => {
    const success = await deleteScenario(user?.id || null, scenario.id);
    if (success) {
      setSavedScenarios((prev) => prev.filter((s) => s.id !== scenario.id));
      toast.success(`Deleted "${scenario.name}"`);
    } else {
      toast.error('Failed to delete scenario');
    }
  };

  const handleSaveScenario = async () => {
    if (!scenarioName.trim()) {
      toast.error('Please enter a scenario name');
      return;
    }

    setIsSaving(true);
    const overrides = getOverrides();

    const saved = await saveScenario(user?.id || null, {
      name: scenarioName,
      overrides,
      base_currency: baseCurrency,
    });

    setIsSaving(false);

    if (saved) {
      await refreshSavedScenarios();
      toast.success(
        saved.is_local
          ? `Saved "${scenarioName}" locally`
          : `Saved "${scenarioName}" to cloud`
      );
      setSaveDialogOpen(false);
      setScenarioName('');
    } else {
      toast.error('Failed to save scenario');
    }
  };

  const handleOpenShareDialog = (scenario: SavedScenario) => {
    setScenarioToShare(scenario);
    setShareQuery('');
    setRecipientResults([]);
    setSelectedRecipientEmail('');
    setShareDialogOpen(true);
  };

  const handleShareScenario = async () => {
    if (!scenarioToShare || !selectedRecipientEmail) {
      toast.error('Please select a recipient');
      return;
    }

    if (!user?.email) {
      toast.error('You must be logged in to share scenarios');
      return;
    }

    if (selectedRecipientEmail.toLowerCase() === user.email.toLowerCase()) {
      toast.error('You cannot share a scenario to yourself');
      return;
    }

    try {
      setIsSharing(true);
      const shared = await shareScenario(user.id, scenarioToShare.id, selectedRecipientEmail);
      if (shared) {
        toast.success(`Shared "${scenarioToShare.name}" with ${shared.recipient_email}`);
        setShareDialogOpen(false);
      } else {
        toast.error('Failed to share scenario');
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to share scenario';
      toast.error(message);
    } finally {
      setIsSharing(false);
    }
  };

  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      {/* Template Selector */}
      <Select onValueChange={handleLoadTemplate}>
        <SelectTrigger className="w-[150px] h-7 text-xs">
          <FolderOpen className="h-3 w-3 mr-1 shrink-0" />
          <SelectValue placeholder="Load Template" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="default">RA Defaults</SelectItem>
          {Object.entries(SCENARIO_TEMPLATES).map(([key, template]) => (
            <SelectItem key={key} value={key}>
              {template.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Saved Scenarios Dropdown */}
      {savedScenarios.length > 0 && (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="h-7 text-xs px-2">
              {isLoadingScenarios ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <>
                  {user ? (
                    <Cloud className="h-3 w-3 mr-1" />
                  ) : (
                    <HardDrive className="h-3 w-3 mr-1" />
                  )}
                  Saved ({savedScenarios.length})
                </>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-72">
            {savedScenarios.map((scenario) => (
              <DropdownMenuItem
                key={scenario.id}
                className="flex items-center gap-2 group"
                onSelect={() => handleLoadSavedScenario(scenario)}
              >
                <span className="flex-1 min-w-0 flex items-center flex-wrap gap-1">
                  {scenario.is_local && (
                    <HardDrive className="h-3 w-3 shrink-0 text-slate-400" />
                  )}
                  <span className="truncate">{scenario.name}</span>
                  <Badge variant="outline" className={`shrink-0 text-[10px] ${scenario.is_local ? 'bg-slate-100 text-slate-600 border-slate-200' : 'bg-green-50 text-green-700 border-green-200'}`}>
                    {scenario.is_local ? 'Local' : 'Cloud'}
                  </Badge>
                  {scenario.is_shared_copy && scenario.shared_by_email && (
                    <Badge variant="outline" className="shrink-0 text-[10px] bg-blue-50 text-blue-700 border-blue-200">
                      Shared by {scenario.shared_by_email}
                    </Badge>
                  )}
                </span>
                <div className="flex items-center gap-1 shrink-0">
                  {!!user && (
                    <div
                      role="button"
                      tabIndex={-1}
                      className={`h-6 w-6 flex items-center justify-center rounded opacity-0 group-hover:opacity-100 transition-opacity ${scenario.is_local ? 'hover:bg-slate-100' : 'hover:bg-blue-100'}`}
                      title={scenario.is_local ? 'Local scenarios are not shareable' : 'Share scenario'}
                      onPointerDown={(e) => e.stopPropagation()}
                      onClick={(e) => {
                        e.stopPropagation();
                        e.preventDefault();
                        if (scenario.is_local) {
                          toast.error('This scenario is local-only and cannot be shared. Save to cloud first.');
                          return;
                        }
                        handleOpenShareDialog(scenario);
                      }}
                    >
                      <Share2 className={`h-3.5 w-3.5 ${scenario.is_local ? 'text-slate-300' : 'text-slate-400 hover:text-blue-600'}`} />
                    </div>
                  )}
                  <div
                    role="button"
                    tabIndex={-1}
                    className="h-6 w-6 flex items-center justify-center rounded opacity-0 group-hover:opacity-100 hover:bg-red-100 transition-opacity"
                    onPointerDown={(e) => e.stopPropagation()}
                    onClick={(e) => {
                      e.stopPropagation();
                      e.preventDefault();
                      handleDeleteScenario(scenario);
                    }}
                  >
                    <Trash2 className="h-3.5 w-3.5 text-slate-400 hover:text-red-500" />
                  </div>
                </div>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      )}

      {/* Save Dialog */}
      <Dialog open={saveDialogOpen} onOpenChange={setSaveDialogOpen}>
        <DialogTrigger asChild>
          <Button variant="outline" size="sm" className="h-7 text-xs px-2">
            <Save className="h-3 w-3 mr-1" />
            Save
          </Button>
        </DialogTrigger>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle>Save Scenario</DialogTitle>
            <DialogDescription>
              {user ? (
                <span className="flex items-center gap-1">
                  <Cloud className="h-4 w-4" />
                  Saving to cloud (syncs across devices)
                </span>
              ) : (
                <span className="flex items-center gap-1">
                  <HardDrive className="h-4 w-4" />
                  Saving locally (sign in to sync)
                </span>
              )}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Input
              placeholder="Scenario name (e.g., Bull Case Q1)"
              value={scenarioName}
              onChange={(e) => setScenarioName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSaveScenario()}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSaveDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveScenario} disabled={isSaving}>
              {isSaving ? (
                <Loader2 className="h-4 w-4 animate-spin mr-1" />
              ) : (
                <Save className="h-4 w-4 mr-1" />
              )}
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Share Dialog */}
      <Dialog open={shareDialogOpen} onOpenChange={setShareDialogOpen}>
        <DialogContent className="sm:max-w-[460px]">
          <DialogHeader>
            <DialogTitle>Share Scenario</DialogTitle>
            <DialogDescription>
              {scenarioToShare
                ? `Share "${scenarioToShare.name}" with another user by email.`
                : 'Share this scenario with another user by email.'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <Input
              placeholder="Search user by email"
              value={shareQuery}
              onChange={(e) => setShareQuery(e.target.value)}
            />
            <div className="max-h-44 overflow-y-auto border rounded-md">
              {isSearchingRecipients ? (
                <div className="p-3 text-xs text-slate-500 flex items-center gap-2">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  Searching...
                </div>
              ) : recipientResults.length > 0 ? (
                recipientResults.map((recipient) => (
                  <button
                    key={recipient.user_id}
                    type="button"
                    className={`w-full text-left px-3 py-2 text-sm hover:bg-slate-50 ${
                      selectedRecipientEmail === recipient.email ? 'bg-blue-50' : ''
                    }`}
                    onClick={() => setSelectedRecipientEmail(recipient.email)}
                  >
                    {recipient.email}
                  </button>
                ))
              ) : (
                <div className="p-3 text-xs text-slate-500">
                  Type at least 2 characters to search by email.
                </div>
              )}
            </div>
            {selectedRecipientEmail && (
              <div className="text-xs text-slate-600">
                Recipient: <span className="font-medium">{selectedRecipientEmail}</span>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShareDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleShareScenario} disabled={!selectedRecipientEmail || isSharing}>
              {isSharing ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <Share2 className="h-4 w-4 mr-1" />}
              Share
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
