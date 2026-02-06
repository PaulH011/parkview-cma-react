/**
 * Hook for real-time macro preview calculations
 */

'use client';

import { useState, useEffect, useMemo } from 'react';
import { useInputStore } from '@/stores/inputStore';
import { calculateMacroPreview } from '@/lib/api';
import { DEFAULT_INPUTS, BUILDING_BLOCK_KEYS } from '@/lib/constants';
import type { MacroRegion, MacroPreviewResponse } from '@/lib/types';

interface MacroPreviewState {
  computed: MacroPreviewResponse | null;
  isLoading: boolean;
  error: string | null;
  hasChanges: boolean;
  conflicts: {
    rgdp_growth: boolean;
    inflation_forecast: boolean;
    tbill_forecast: boolean;
  };
}

export function useMacroPreview(region: MacroRegion): MacroPreviewState {
  const [computed, setComputed] = useState<MacroPreviewResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const macroInputs = useInputStore((state) => state.macro[region]);
  const defaults = DEFAULT_INPUTS.macro[region];

  // Check if any building blocks have changed
  const hasChanges = useMemo(() => {
    return BUILDING_BLOCK_KEYS.some((key) => {
      const current = macroInputs[key];
      const defaultVal = defaults[key];
      return Math.abs(current - defaultVal) > 0.001;
    });
  }, [macroInputs, defaults]);

  // Calculate preview when building blocks change
  useEffect(() => {
    if (!hasChanges) {
      setComputed(null);
      return;
    }

    const fetchPreview = async () => {
      setIsLoading(true);
      try {
        // Convert from percentage to decimal for API
        const buildingBlocks = {
          population_growth: macroInputs.population_growth / 100,
          productivity_growth: macroInputs.productivity_growth / 100,
          my_ratio: macroInputs.my_ratio,
          current_headline_inflation: macroInputs.current_headline_inflation / 100,
          long_term_inflation: macroInputs.long_term_inflation / 100,
          current_tbill: macroInputs.current_tbill / 100,
          country_factor: macroInputs.country_factor / 100,
        };

        const result = await calculateMacroPreview(region, buildingBlocks);
        setComputed(result);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Preview calculation failed');
      } finally {
        setIsLoading(false);
      }
    };

    // Debounce the API call
    const timeout = setTimeout(fetchPreview, 300);
    return () => clearTimeout(timeout);
  }, [region, macroInputs, hasChanges]);

  // Check for conflicts between computed values and direct overrides
  // A conflict exists when building blocks have changed AND the user has
  // manually overridden the direct forecast field (dirty field).
  // This ensures the user always sees that building blocks affect their override,
  // even if the computed value happens to match.
  const isMacroDirty = useInputStore((state) => state.isMacroDirty);

  const conflicts = useMemo(() => {
    if (!computed || !hasChanges) {
      return {
        rgdp_growth: false,
        inflation_forecast: false,
        tbill_forecast: false,
      };
    }

    // Show conflict if user has explicitly overridden the direct forecast field
    // and building blocks have changed (hasChanges is already true at this point)
    return {
      rgdp_growth: isMacroDirty(region, 'rgdp_growth'),
      inflation_forecast: isMacroDirty(region, 'inflation_forecast'),
      tbill_forecast: isMacroDirty(region, 'tbill_forecast'),
    };
  }, [computed, hasChanges, region, isMacroDirty]);

  return {
    computed,
    isLoading,
    error,
    hasChanges,
    conflicts,
  };
}
