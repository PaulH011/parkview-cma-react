-- ============================================================================
-- Quarterly Default Assumption Refresh - Supabase Migration
-- ============================================================================

-- 1. default_assumptions table - stores the current approved defaults as JSONB
-- Singleton row (id = 1) containing the full defaults structure
CREATE TABLE IF NOT EXISTS default_assumptions (
    id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    defaults_json JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by TEXT NOT NULL
);

-- 2. assumption_refresh_log table - audit trail of all refresh operations
CREATE TABLE IF NOT EXISTS assumption_refresh_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    initiated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    initiated_by TEXT NOT NULL,
    suggestions_json JSONB,
    applied_changes_json JSONB,
    status TEXT NOT NULL CHECK (status IN ('pending', 'applied', 'dismissed', 'test'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_refresh_log_initiated_at
    ON assumption_refresh_log(initiated_at DESC);

CREATE INDEX IF NOT EXISTS idx_refresh_log_status
    ON assumption_refresh_log(status);

-- Row Level Security (RLS)
-- default_assumptions: readable by all authenticated users, writable only via service role
ALTER TABLE default_assumptions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "default_assumptions_read" ON default_assumptions
    FOR SELECT TO authenticated
    USING (true);

CREATE POLICY "default_assumptions_anon_read" ON default_assumptions
    FOR SELECT TO anon
    USING (true);

-- assumption_refresh_log: readable by all authenticated, insertable by all authenticated
ALTER TABLE assumption_refresh_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "refresh_log_read" ON assumption_refresh_log
    FOR SELECT TO authenticated
    USING (true);

CREATE POLICY "refresh_log_insert" ON assumption_refresh_log
    FOR INSERT TO authenticated
    WITH CHECK (true);

CREATE POLICY "refresh_log_update" ON assumption_refresh_log
    FOR UPDATE TO authenticated
    USING (true);
