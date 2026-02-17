/**
 * Scenarios service
 *
 * Saves scenarios to Supabase when authenticated, localStorage when not.
 * Uses react_scenarios table (separate from Streamlit app).
 */

import {
  getSupabaseClient,
  type ReactScenario,
  type ShareRecipient,
  type ShareScenarioResult,
} from './supabase';

const LOCAL_STORAGE_KEY = 'react-cma-scenarios';

export interface SavedScenario {
  id: string;
  name: string;
  description?: string;
  overrides: Record<string, unknown>;
  base_currency: string;
  is_shared_copy?: boolean;
  shared_from_scenario_id?: string | null;
  shared_by_user_id?: string | null;
  shared_by_email?: string | null;
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

/**
 * Search authenticated users by email for sharing.
 */
export async function searchShareRecipients(
  userId: string | null,
  query: string
): Promise<ShareRecipient[]> {
  const supabase = getSupabaseClient();
  const normalized = query.trim();

  if (!userId || !supabase || normalized.length < 2) {
    return [];
  }

  const { data, error } = await supabase.rpc('react_search_users_by_email', {
    query_text: normalized,
  });

  if (error) {
    console.error('Error searching recipients:', error);
    return [];
  }

  return (data || []) as ShareRecipient[];
}

/**
 * Share an owned cloud scenario to another user by email.
 */
export async function shareScenario(
  userId: string | null,
  sourceScenarioId: string,
  recipientEmail: string
): Promise<ShareScenarioResult | null> {
  const supabase = getSupabaseClient();

  if (!userId || !supabase) {
    return null;
  }

  const { data, error } = await supabase.rpc('react_share_scenario', {
    source_scenario_id: sourceScenarioId,
    recipient_email_input: recipientEmail.trim().toLowerCase(),
  });

  if (error) {
    console.error('Error sharing scenario:', error);
    throw new Error(error.message || 'Failed to share scenario');
  }

  const rows = (data || []) as ShareScenarioResult[];
  return rows.length > 0 ? rows[0] : null;
}

// ============= Local Storage Helpers =============

function getLocalScenarios(): SavedScenario[] {
  if (typeof window === 'undefined') return [];

  try {
    const stored = localStorage.getItem(LOCAL_STORAGE_KEY);
    if (!stored) return [];

    const parsed = JSON.parse(stored) as Record<string, SavedScenario>;
    return Object.values(parsed).map((s) => ({
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
