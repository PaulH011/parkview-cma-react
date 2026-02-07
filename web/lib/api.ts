/**
 * API client for the Parkview CMA backend
 */

import type {
  CalculateResponse,
  MacroPreviewResponse,
  Overrides,
  BaseCurrency,
  AllInputs,
  Scenario,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Generic fetch wrapper with error handling
 */
async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API error: ${response.status}`);
  }

  return response.json();
}

/**
 * Health check
 */
export async function checkHealth(): Promise<{ status: string; version: string }> {
  return fetchAPI('/health');
}

/**
 * Get all default values
 */
export async function getDefaults(): Promise<AllInputs> {
  return fetchAPI('/api/defaults/all');
}

/**
 * Get macro defaults for a specific region
 */
export async function getMacroDefaults(region: string): Promise<Record<string, number>> {
  return fetchAPI(`/api/defaults/macro/${region}`);
}

/**
 * Run full CME calculation
 */
export async function calculateFull(
  overrides?: Overrides,
  baseCurrency: BaseCurrency = 'usd',
  scenarioName: string = 'Current Scenario'
): Promise<CalculateResponse> {
  return fetchAPI('/api/calculate/full', {
    method: 'POST',
    body: JSON.stringify({
      overrides,
      base_currency: baseCurrency,
      scenario_name: scenarioName,
    }),
  });
}

/**
 * Calculate macro preview from building blocks
 */
export async function calculateMacroPreview(
  region: string,
  buildingBlocks: Record<string, number>
): Promise<MacroPreviewResponse> {
  return fetchAPI('/api/calculate/macro-preview', {
    method: 'POST',
    body: JSON.stringify({
      region,
      building_blocks: buildingBlocks,
    }),
  });
}

/**
 * Compare multiple scenarios
 */
export async function compareScenarios(
  scenarios: Array<{
    overrides?: Overrides;
    base_currency: BaseCurrency;
    scenario_name: string;
  }>
): Promise<{ scenarios: CalculateResponse[] }> {
  return fetchAPI('/api/calculate/compare', {
    method: 'POST',
    body: JSON.stringify(scenarios),
  });
}

/**
 * List user's scenarios
 */
export async function listScenarios(userId: string): Promise<{ scenarios: Scenario[] }> {
  return fetchAPI(`/api/scenarios?user_id=${userId}`);
}

/**
 * Create a new scenario
 */
export async function createScenario(
  userId: string,
  name: string,
  overrides: Overrides,
  baseCurrency: BaseCurrency
): Promise<{ success: boolean; scenario: Scenario }> {
  return fetchAPI(`/api/scenarios?user_id=${userId}`, {
    method: 'POST',
    body: JSON.stringify({
      name,
      overrides,
      base_currency: baseCurrency,
    }),
  });
}

/**
 * Delete a scenario
 */
export async function deleteScenario(
  scenarioId: string,
  userId: string
): Promise<{ success: boolean }> {
  return fetchAPI(`/api/scenarios/${scenarioId}?user_id=${userId}`, {
    method: 'DELETE',
  });
}

// ---- Admin Endpoints ----

export interface ResearchComparison {
  key: string;
  display_name: string;
  category: string;
  subcategory: string;
  unit: string;
  current_value: number | null;
  suggested_value: number | null;
  abs_diff: number;
  rel_diff: number;
  source: string;
  confidence: 'high' | 'medium' | 'low';
  notes: string;
}

export interface ResearchResult {
  log_id: string;
  researched_at: string;
  comparisons: ResearchComparison[];
  total_assumptions: number;
  is_test: boolean;
}

export interface RefreshHistoryEntry {
  id: string;
  initiated_at: string;
  initiated_by: string;
  suggestions_json: Record<string, any> | null;
  applied_changes_json: Record<string, any> | null;
  status: string;
}

/**
 * Trigger AI research of current market assumptions (super user only)
 */
export async function researchDefaults(
  userEmail: string,
  isTest: boolean = false
): Promise<ResearchResult> {
  return fetchAPI('/api/admin/research-defaults', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Email': userEmail,
    },
    body: JSON.stringify({ is_test: isTest }),
  });
}

/**
 * Apply accepted changes to defaults (super user only)
 */
export async function applyDefaults(
  userEmail: string,
  acceptedChanges: Array<{ key: string; new_value: number }>,
  isTest: boolean = false
): Promise<{ success: boolean; changes_applied: number; updated_at: string; is_test: boolean }> {
  return fetchAPI('/api/admin/apply-defaults', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Email': userEmail,
    },
    body: JSON.stringify({
      accepted_changes: acceptedChanges,
      is_test: isTest,
    }),
  });
}

/**
 * Revert to original hardcoded defaults (super user only)
 */
export async function revertDefaults(
  userEmail: string
): Promise<{ success: boolean; message: string }> {
  return fetchAPI('/api/admin/revert-defaults', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Email': userEmail,
    },
  });
}

/**
 * Get refresh history (super user only)
 */
export async function getRefreshHistory(
  userEmail: string
): Promise<{ history: RefreshHistoryEntry[] }> {
  return fetchAPI('/api/admin/refresh-history', {
    headers: {
      'X-User-Email': userEmail,
    },
  });
}

/**
 * Get the date of the last successful refresh (public)
 */
export async function getLastRefresh(): Promise<{ last_refresh: string | null }> {
  return fetchAPI('/api/admin/last-refresh');
}
