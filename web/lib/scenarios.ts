/**
 * Scenarios service
 *
 * Saves scenarios to Supabase when authenticated, localStorage when not.
 * Uses react_scenarios table (separate from Streamlit app).
 */

import { getSupabaseClient, type ReactScenario } from './supabase';

const LOCAL_STORAGE_KEY = 'react-cma-scenarios';

export interface SavedScenario {
  id: string;
  name: string;
  description?: string;
  overrides: Record<string, any>;
  base_currency: string;
  created_at: string;
  updated_at: string;
  is_local?: boolean; // True if saved to localStorage (not synced)
}

/**
 * Get all saved scenarios for the current user
 */
export async function getScenarios(userId: string | null): Promise<SavedScenario[]> {
  const supabase = getSupabaseClient();

  // If authenticated, fetch from Supabase
  if (userId && supabase) {
    try {
      const { data, error } = await supabase
        .from('react_scenarios')
        .select('*')
        .eq('user_id', userId)
        .order('updated_at', { ascending: false });

      if (error) {
        console.error('Error fetching scenarios:', error);
        // Fall back to localStorage
        return getLocalScenarios();
      }

      return (data || []).map((s: ReactScenario) => ({
        ...s,
        is_local: false,
      }));
    } catch (err) {
      console.error('Supabase error:', err);
      return getLocalScenarios();
    }
  }

  // Not authenticated - use localStorage
  return getLocalScenarios();
}

/**
 * Save a scenario
 */
export async function saveScenario(
  userId: string | null,
  scenario: Omit<SavedScenario, 'id' | 'created_at' | 'updated_at'>
): Promise<SavedScenario | null> {
  const supabase = getSupabaseClient();
  const now = new Date().toISOString();

  // If authenticated, save to Supabase
  if (userId && supabase) {
    try {
      const { data, error } = await supabase
        .from('react_scenarios')
        .insert({
          user_id: userId,
          name: scenario.name,
          description: scenario.description || null,
          overrides: scenario.overrides,
          base_currency: scenario.base_currency,
        })
        .select()
        .single();

      if (error) {
        console.error('Error saving scenario:', error);
        // Fall back to localStorage
        return saveLocalScenario(scenario);
      }

      return { ...data, is_local: false };
    } catch (err) {
      console.error('Supabase error:', err);
      return saveLocalScenario(scenario);
    }
  }

  // Not authenticated - use localStorage
  return saveLocalScenario(scenario);
}

/**
 * Delete a scenario
 */
export async function deleteScenario(userId: string | null, id: string): Promise<boolean> {
  const supabase = getSupabaseClient();

  if (userId && supabase) {
    try {
      const { error } = await supabase
        .from('react_scenarios')
        .delete()
        .eq('id', id)
        .eq('user_id', userId);

      if (error) {
        console.error('Error deleting scenario:', error);
        return false;
      }

      return true;
    } catch (err) {
      console.error('Supabase error:', err);
      return false;
    }
  }

  // Local delete
  return deleteLocalScenario(id);
}

// ============= Local Storage Helpers =============

function getLocalScenarios(): SavedScenario[] {
  if (typeof window === 'undefined') return [];

  try {
    const stored = localStorage.getItem(LOCAL_STORAGE_KEY);
    if (!stored) return [];

    const parsed = JSON.parse(stored);
    return Object.values(parsed).map((s: any) => ({
      ...s,
      is_local: true,
    }));
  } catch {
    return [];
  }
}

function saveLocalScenario(
  scenario: Omit<SavedScenario, 'id' | 'created_at' | 'updated_at'>
): SavedScenario {
  const now = new Date().toISOString();
  const id = `local-${Date.now()}`;

  const newScenario: SavedScenario = {
    id,
    ...scenario,
    created_at: now,
    updated_at: now,
    is_local: true,
  };

  const scenarios = getLocalScenariosMap();
  scenarios[id] = newScenario;
  localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(scenarios));

  return newScenario;
}

function deleteLocalScenario(id: string): boolean {
  const scenarios = getLocalScenariosMap();

  if (!scenarios[id]) return false;

  delete scenarios[id];
  localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(scenarios));
  return true;
}

function getLocalScenariosMap(): Record<string, SavedScenario> {
  if (typeof window === 'undefined') return {};

  try {
    const stored = localStorage.getItem(LOCAL_STORAGE_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch {
    return {};
  }
}
