/**
 * Zustand store for managing input state
 *
 * Supports dynamic defaults loaded from API (Supabase-backed)
 * with fallback to hardcoded constants.
 */

import { create } from 'zustand';
import { DEFAULT_INPUTS, DEFAULT_INPUTS_GK_EQUITY, DIRECT_FORECAST_KEYS } from '@/lib/constants';
import { getDefaults } from '@/lib/api';
import type {
  MacroInputs,
  MacroRegion,
  BondInputs,
  BondType,
  InflationLinkedInputs,
  InflationLinkedRegimeInputs,
  EquityInputs,
  EquityInputsGK,
  EquityRegion,
  EquityModelType,
  AbsoluteReturnInputs,
  BaseCurrency,
  Overrides,
  AllInputs,
} from '@/lib/types';

interface InputState {
  // Current input values
  macro: Record<MacroRegion, MacroInputs>;
  bonds: AllInputs['bonds'];
  equity: Record<EquityRegion, EquityInputs>;
  equityGK: Record<EquityRegion, EquityInputsGK>;
  absoluteReturn: AbsoluteReturnInputs;
  baseCurrency: BaseCurrency;

  // Equity model toggle
  equityModelType: EquityModelType;

  // Dynamic defaults fetched from API (null until loaded)
  fetchedDefaults: AllInputs | null;

  // UI state
  advancedMode: boolean;

  // Track which direct forecast fields the user has explicitly set
  // Key format: "region.field" e.g. "us.tbill_forecast"
  _dirtyMacroFields: Record<string, boolean>;

  // Actions
  fetchDefaultsFromAPI: () => Promise<void>;
  getActiveDefaults: () => AllInputs;
  setMacroValue: (region: MacroRegion, key: keyof MacroInputs, value: number) => void;
  syncMacroComputed: (region: MacroRegion, computedValues: Partial<Record<string, number>>) => void;
  isMacroDirty: (region: MacroRegion, key: keyof MacroInputs) => boolean;
  setBondValue: (type: Exclude<BondType, 'inflation_linked'>, key: keyof BondInputs, value: number) => void;
  setInflationLinkedValue: (
    regime: keyof InflationLinkedInputs,
    key: keyof InflationLinkedRegimeInputs,
    value: number
  ) => void;
  setEquityValue: (region: EquityRegion, key: keyof EquityInputs, value: number) => void;
  setEquityGKValue: (region: EquityRegion, key: keyof EquityInputsGK, value: number) => void;
  setEquityModelType: (type: EquityModelType) => void;
  setAbsoluteReturnValue: (key: keyof AbsoluteReturnInputs, value: number) => void;
  setBaseCurrency: (currency: BaseCurrency) => void;
  setAdvancedMode: (enabled: boolean) => void;
  resetToDefaults: () => void;
  loadScenario: (overrides: Overrides) => void;
  getOverrides: () => Overrides;
}

/**
 * Check if a value differs from its default
 */
function isDifferent(value: number, defaultValue: number, tolerance = 0.001): boolean {
  return Math.abs(value - defaultValue) > tolerance;
}

export const useInputStore = create<InputState>((set, get) => ({
  // Initialize with hardcoded defaults (will be replaced by fetched defaults)
  macro: { ...DEFAULT_INPUTS.macro },
  bonds: { ...DEFAULT_INPUTS.bonds },
  equity: { ...DEFAULT_INPUTS.equity },
  equityGK: { ...DEFAULT_INPUTS_GK_EQUITY },
  absoluteReturn: { ...DEFAULT_INPUTS.absolute_return },
  baseCurrency: 'usd',
  equityModelType: 'gk' as EquityModelType,  // Default to GK on this branch for testing
  fetchedDefaults: null,
  advancedMode: false,
  _dirtyMacroFields: {},

  fetchDefaultsFromAPI: async () => {
    try {
      const defaults = await getDefaults();
      set({
        fetchedDefaults: defaults,
        // Also update current values to the fetched defaults (only if user hasn't customized)
        macro: { ...defaults.macro },
        bonds: { ...defaults.bonds },
        equity: { ...defaults.equity },
        absoluteReturn: { ...defaults.absolute_return },
        _dirtyMacroFields: {},
      });
    } catch (err) {
      if (process.env.NODE_ENV === 'development') console.warn('[inputStore] Could not fetch defaults from API, using hardcoded:', err);
      // Keep using DEFAULT_INPUTS as fallback
    }
  },

  getActiveDefaults: () => {
    const state = get();
    return state.fetchedDefaults ?? DEFAULT_INPUTS;
  },

  setMacroValue: (region, key, value) => {
    const isDirect = (DIRECT_FORECAST_KEYS as readonly string[]).includes(key as string);
    set((state) => ({
      macro: {
        ...state.macro,
        [region]: {
          ...state.macro[region],
          [key]: value,
        },
      },
      // Mark direct forecast fields as dirty when user explicitly sets them
      ...(isDirect
        ? {
            _dirtyMacroFields: {
              ...state._dirtyMacroFields,
              [`${region}.${key}`]: true,
            },
          }
        : {}),
    }));
  },

  syncMacroComputed: (region, computedValues) =>
    set((state) => {
      const newRegionMacro = { ...state.macro[region] };
      let changed = false;

      for (const [key, value] of Object.entries(computedValues)) {
        // Only sync non-dirty direct forecast fields
        if (!state._dirtyMacroFields[`${region}.${key}`]) {
          const currentVal = newRegionMacro[key as keyof MacroInputs];
          if (typeof value === 'number' && Math.abs(currentVal - value) > 0.001) {
            newRegionMacro[key as keyof MacroInputs] = value;
            changed = true;
          }
        }
      }

      if (!changed) return state;

      return {
        macro: {
          ...state.macro,
          [region]: newRegionMacro,
        },
      };
    }),

  isMacroDirty: (region, key) => {
    return !!get()._dirtyMacroFields[`${region}.${key}`];
  },

  setBondValue: (type, key, value) =>
    set((state) => ({
      bonds: {
        ...state.bonds,
        [type]: {
          ...state.bonds[type],
          [key]: value,
        },
      },
    })),

  setInflationLinkedValue: (regime, key, value) =>
    set((state) => ({
      bonds: {
        ...state.bonds,
        inflation_linked: {
          ...state.bonds.inflation_linked,
          [regime]: {
            ...state.bonds.inflation_linked[regime],
            [key]: value,
          },
        },
      },
    })),

  setEquityValue: (region, key, value) =>
    set((state) => ({
      equity: {
        ...state.equity,
        [region]: {
          ...state.equity[region],
          [key]: value,
        },
      },
    })),

  setEquityGKValue: (region, key, value) =>
    set((state) => ({
      equityGK: {
        ...state.equityGK,
        [region]: {
          ...state.equityGK[region],
          [key]: value,
        },
      },
    })),

  setEquityModelType: (type) => set({ equityModelType: type }),

  setAbsoluteReturnValue: (key, value) =>
    set((state) => ({
      absoluteReturn: {
        ...state.absoluteReturn,
        [key]: value,
      },
    })),

  setBaseCurrency: (currency) => set({ baseCurrency: currency }),

  setAdvancedMode: (enabled) => set({ advancedMode: enabled }),

  resetToDefaults: () => {
    const defaults = get().getActiveDefaults();
    set({
      macro: { ...defaults.macro },
      bonds: { ...defaults.bonds },
      equity: { ...defaults.equity },
      equityGK: { ...DEFAULT_INPUTS_GK_EQUITY },
      absoluteReturn: { ...defaults.absolute_return },
      _dirtyMacroFields: {},
    });
  },

  loadScenario: (overrides) => {
    const state = get();
    const directKeys = DIRECT_FORECAST_KEYS as readonly string[];

    // Start with current state and apply overrides
    const newMacro = { ...state.macro };
    const newBonds = { ...state.bonds };
    const newEquity = { ...state.equity };
    let newAbsoluteReturn = { ...state.absoluteReturn };
    const newDirtyFields = { ...state._dirtyMacroFields };

    // Apply macro overrides
    if (overrides.macro) {
      for (const [region, values] of Object.entries(overrides.macro)) {
        if (values && region in newMacro) {
          newMacro[region as MacroRegion] = {
            ...newMacro[region as MacroRegion],
            ...values,
          };
          // Mark loaded direct forecast fields as dirty
          for (const key of Object.keys(values)) {
            if (directKeys.includes(key)) {
              newDirtyFields[`${region}.${key}`] = true;
            }
          }
        }
      }
    }

    // Apply bond overrides
    for (const type of ['global', 'hy', 'em'] as Exclude<BondType, 'inflation_linked'>[]) {
      const key = `bonds_${type}` as keyof Overrides;
      if (overrides[key]) {
        newBonds[type] = {
          ...newBonds[type],
          ...overrides[key],
        };
      }
    }

    if (overrides.inflation_linked) {
      newBonds.inflation_linked = {
        ...newBonds.inflation_linked,
        usd: {
          ...newBonds.inflation_linked.usd,
          ...(overrides.inflation_linked.usd || {}),
        },
        eur: {
          ...newBonds.inflation_linked.eur,
          ...(overrides.inflation_linked.eur || {}),
        },
      };
    }

    // Apply equity overrides (to both RA and GK stores)
    const newEquityGK = { ...state.equityGK };
    for (const region of ['us', 'europe', 'japan', 'em'] as EquityRegion[]) {
      const key = `equity_${region}` as keyof Overrides;
      if (overrides[key]) {
        newEquity[region] = {
          ...newEquity[region],
          ...overrides[key],
        };
        newEquityGK[region] = {
          ...newEquityGK[region],
          ...overrides[key],
        };
      }
    }

    // Apply absolute return overrides
    if (overrides.absolute_return) {
      newAbsoluteReturn = {
        ...newAbsoluteReturn,
        ...overrides.absolute_return,
      };
    }

    set({
      macro: newMacro,
      bonds: newBonds,
      equity: newEquity,
      equityGK: newEquityGK,
      absoluteReturn: newAbsoluteReturn,
      _dirtyMacroFields: newDirtyFields,
    });
  },

  getOverrides: () => {
    const state = get();
    const defaults = state.getActiveDefaults();
    const overrides: Overrides = {};

    // Check macro differences
    const directKeys = DIRECT_FORECAST_KEYS as readonly string[];

    for (const region of ['us', 'eurozone', 'japan', 'em'] as MacroRegion[]) {
      const current = state.macro[region];
      const regionDefaults = defaults.macro[region];
      const regionOverrides: Partial<MacroInputs> = {};

      for (const [key, value] of Object.entries(current)) {
        const isDirect = directKeys.includes(key);

        if (isDirect) {
          // Direct forecast fields: only send if user explicitly set them
          const isDirty = state._dirtyMacroFields[`${region}.${key}`];
          if (isDirty) {
            if (key === 'my_ratio') {
              regionOverrides[key as keyof MacroInputs] = value as number;
            } else {
              regionOverrides[key as keyof MacroInputs] = (value as number) / 100;
            }
          }
        } else {
          // Building block fields: use difference-from-default logic
          const defaultValue = regionDefaults[key as keyof MacroInputs];
          if (isDifferent(value as number, defaultValue as number)) {
            if (key === 'my_ratio') {
              regionOverrides[key as keyof MacroInputs] = value as number;
            } else {
              regionOverrides[key as keyof MacroInputs] = (value as number) / 100;
            }
          }
        }
      }

      if (Object.keys(regionOverrides).length > 0) {
        if (!overrides.macro) overrides.macro = {};
        overrides.macro[region] = regionOverrides;
      }
    }

    // Check bond differences
    for (const type of ['global', 'hy', 'em'] as Exclude<BondType, 'inflation_linked'>[]) {
      const current = state.bonds[type];
      const bondDefaults = defaults.bonds[type];
      const bondOverrides: Partial<BondInputs> = {};

      for (const [key, value] of Object.entries(current)) {
        if (value === undefined) continue;
        const defaultValue = bondDefaults[key as keyof BondInputs];
        if (defaultValue !== undefined && isDifferent(value as number, defaultValue as number)) {
          // Duration stays as-is, others convert to decimal
          if (key === 'duration') {
            bondOverrides[key as keyof BondInputs] = value as number;
          } else {
            bondOverrides[key as keyof BondInputs] = (value as number) / 100;
          }
        }
      }

      if (Object.keys(bondOverrides).length > 0) {
        if (type === 'global') overrides.bonds_global = bondOverrides;
        if (type === 'hy') overrides.bonds_hy = bondOverrides;
        if (type === 'em') overrides.bonds_em = bondOverrides;
      }
    }

    // Inflation-linked nested overrides
    const ilOverrides: Overrides['inflation_linked'] = {};
    for (const regime of ['usd', 'eur'] as const) {
      const currentRegime = state.bonds.inflation_linked[regime];
      const defaultRegime = defaults.bonds.inflation_linked[regime];
      const regimeOverrides: Partial<InflationLinkedRegimeInputs> = {};

      for (const [key, value] of Object.entries(currentRegime)) {
        const defaultValue = defaultRegime[key as keyof InflationLinkedRegimeInputs];
        if (isDifferent(value as number, defaultValue as number)) {
          if (key === 'duration' || key === 'inflation_beta') {
            regimeOverrides[key as keyof InflationLinkedRegimeInputs] = value as number;
          } else {
            regimeOverrides[key as keyof InflationLinkedRegimeInputs] = (value as number) / 100;
          }
        }
      }

      if (Object.keys(regimeOverrides).length > 0) {
        ilOverrides[regime] = regimeOverrides;
      }
    }
    if (Object.keys(ilOverrides).length > 0) {
      overrides.inflation_linked = ilOverrides;
    }

    // Check equity differences (RA or GK depending on model type)
    if (state.equityModelType === 'gk') {
      // GK model overrides
      const gkDefaults = DEFAULT_INPUTS_GK_EQUITY;
      // Keys that are ratios (not percentage points) — send as-is, no /100
      const gkRatioKeys = new Set(['current_pe', 'target_pe']);

      for (const region of ['us', 'europe', 'japan', 'em'] as EquityRegion[]) {
        const current = state.equityGK[region];
        const regionDefaults = gkDefaults[region];
        const equityOverrides: Record<string, number> = {};

        for (const [key, value] of Object.entries(current)) {
          const defaultValue = regionDefaults[key as keyof EquityInputsGK];
          if (isDifferent(value as number, defaultValue as number)) {
            if (gkRatioKeys.has(key)) {
              equityOverrides[key] = value as number;
            } else {
              equityOverrides[key] = (value as number) / 100;
            }
          }
        }

        if (Object.keys(equityOverrides).length > 0) {
          if (region === 'us') overrides.equity_us = equityOverrides;
          if (region === 'europe') overrides.equity_europe = equityOverrides;
          if (region === 'japan') overrides.equity_japan = equityOverrides;
          if (region === 'em') overrides.equity_em = equityOverrides;
        }
      }
    } else {
      // RA model overrides (original logic)
      for (const region of ['us', 'europe', 'japan', 'em'] as EquityRegion[]) {
        const current = state.equity[region];
        const eqDefaults = defaults.equity[region];
        const equityOverrides: Partial<EquityInputs> = {};

        for (const [key, value] of Object.entries(current)) {
          const defaultValue = eqDefaults[key as keyof EquityInputs];
          if (isDifferent(value as number, defaultValue as number)) {
            equityOverrides[key as keyof EquityInputs] = (value as number) / 100;
          }
        }

        if (Object.keys(equityOverrides).length > 0) {
          if (region === 'us') overrides.equity_us = equityOverrides;
          if (region === 'europe') overrides.equity_europe = equityOverrides;
          if (region === 'japan') overrides.equity_japan = equityOverrides;
          if (region === 'em') overrides.equity_em = equityOverrides;
        }
      }
    }

    // Check absolute return differences
    const arOverrides: Partial<AbsoluteReturnInputs> = {};
    for (const [key, value] of Object.entries(state.absoluteReturn)) {
      const defaultValue = defaults.absolute_return[key as keyof AbsoluteReturnInputs];
      if (isDifferent(value, defaultValue)) {
        if (key === 'trading_alpha') {
          arOverrides[key as keyof AbsoluteReturnInputs] = value / 100;
        } else {
          arOverrides[key as keyof AbsoluteReturnInputs] = value;
        }
      }
    }

    if (Object.keys(arOverrides).length > 0) {
      overrides.absolute_return = arOverrides;
    }

    return overrides;
  },
}));
