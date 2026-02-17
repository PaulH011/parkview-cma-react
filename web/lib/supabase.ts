/**
 * Supabase client configuration for the React CMA Tool
 *
 * This uses a SEPARATE Supabase project from the Streamlit app.
 * Tables: react_scenarios, react_user_preferences
 */

import { createBrowserClient } from '@supabase/ssr';

// These should be set in .env.local
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

// Create a singleton client for browser usage
let client: ReturnType<typeof createBrowserClient> | null = null;

export function getSupabaseClient() {
  if (!client) {
    if (!supabaseUrl || !supabaseAnonKey) {
      console.warn('Supabase not configured. Auth features disabled.');
      return null;
    }
    client = createBrowserClient(supabaseUrl, supabaseAnonKey);
  }
  return client;
}

// Type definitions for our tables (separate from Streamlit app)
export interface ReactScenario {
  id: string;
  user_id: string;
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
}

export interface ReactUserPreferences {
  user_id: string;
  default_currency: string;
  theme: 'light' | 'dark' | 'system';
  created_at: string;
  updated_at: string;
}

export interface ShareRecipient {
  user_id: string;
  email: string;
}

export interface ShareScenarioResult {
  shared_scenario_id: string;
  shared_scenario_name: string;
  recipient_user_id: string;
  recipient_email: string;
}
