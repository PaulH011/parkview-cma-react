-- =============================================================================
-- Supabase Migration for React CMA Tool
-- SEPARATE from Streamlit app tables (uses react_ prefix)
-- =============================================================================

-- Table: react_scenarios
-- Stores user-saved scenarios with their input overrides
CREATE TABLE IF NOT EXISTS react_scenarios (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  overrides JSONB NOT NULL DEFAULT '{}',
  base_currency TEXT NOT NULL DEFAULT 'usd',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for faster user lookups
CREATE INDEX IF NOT EXISTS idx_react_scenarios_user_id ON react_scenarios(user_id);

-- Enable Row Level Security
ALTER TABLE react_scenarios ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Users can only access their own scenarios
CREATE POLICY "Users can view own scenarios"
  ON react_scenarios FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own scenarios"
  ON react_scenarios FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own scenarios"
  ON react_scenarios FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own scenarios"
  ON react_scenarios FOR DELETE
  USING (auth.uid() = user_id);

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_react_scenarios_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for auto-updating updated_at
DROP TRIGGER IF EXISTS trigger_react_scenarios_updated_at ON react_scenarios;
CREATE TRIGGER trigger_react_scenarios_updated_at
  BEFORE UPDATE ON react_scenarios
  FOR EACH ROW
  EXECUTE FUNCTION update_react_scenarios_updated_at();

-- =============================================================================
-- Table: react_user_preferences (optional - for future use)
-- =============================================================================

CREATE TABLE IF NOT EXISTS react_user_preferences (
  user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  default_currency TEXT DEFAULT 'usd',
  theme TEXT DEFAULT 'system',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE react_user_preferences ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own preferences"
  ON react_user_preferences FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own preferences"
  ON react_user_preferences FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own preferences"
  ON react_user_preferences FOR UPDATE
  USING (auth.uid() = user_id);
