-- =============================================================================
-- Supabase Migration: Scenario Sharing (Snapshot Copy)
-- =============================================================================

-- Add metadata fields to identify shared copies
ALTER TABLE react_scenarios
  ADD COLUMN IF NOT EXISTS is_shared_copy BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS shared_from_scenario_id UUID NULL REFERENCES react_scenarios(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS shared_by_user_id UUID NULL REFERENCES auth.users(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS shared_by_email TEXT NULL;

CREATE INDEX IF NOT EXISTS idx_react_scenarios_shared_from_id
  ON react_scenarios(shared_from_scenario_id);

CREATE INDEX IF NOT EXISTS idx_react_scenarios_shared_by_user
  ON react_scenarios(shared_by_user_id);

-- Audit table for share actions
CREATE TABLE IF NOT EXISTS react_scenario_shares (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  source_scenario_id UUID NOT NULL REFERENCES react_scenarios(id) ON DELETE CASCADE,
  shared_by_user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  recipient_user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  recipient_email TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_react_scenario_shares_source
  ON react_scenario_shares(source_scenario_id);

CREATE INDEX IF NOT EXISTS idx_react_scenario_shares_recipient
  ON react_scenario_shares(recipient_user_id);

-- Prevent duplicate shares of the same source by the same sender to same recipient
CREATE UNIQUE INDEX IF NOT EXISTS uniq_react_scenario_share_sender_source_recipient
  ON react_scenario_shares(source_scenario_id, shared_by_user_id, recipient_user_id);

ALTER TABLE react_scenario_shares ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view shares they sent or received"
  ON react_scenario_shares FOR SELECT
  USING (auth.uid() = shared_by_user_id OR auth.uid() = recipient_user_id);

-- Share operation is performed by RPC with explicit checks, not direct insert
CREATE POLICY "No direct insert into scenario shares"
  ON react_scenario_shares FOR INSERT
  WITH CHECK (FALSE);

CREATE POLICY "No direct update on scenario shares"
  ON react_scenario_shares FOR UPDATE
  USING (FALSE);

CREATE POLICY "No direct delete on scenario shares"
  ON react_scenario_shares FOR DELETE
  USING (FALSE);

-- Search for recipients by email (authenticated users only)
CREATE OR REPLACE FUNCTION react_search_users_by_email(query_text TEXT)
RETURNS TABLE (
  user_id UUID,
  email TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  normalized_query TEXT;
BEGIN
  IF auth.uid() IS NULL THEN
    RAISE EXCEPTION 'Authentication required';
  END IF;

  normalized_query := lower(trim(coalesce(query_text, '')));
  IF length(normalized_query) < 2 THEN
    RETURN;
  END IF;

  RETURN QUERY
  SELECT u.id, u.email::TEXT
  FROM auth.users u
  WHERE u.email IS NOT NULL
    AND lower(u.email::TEXT) LIKE normalized_query || '%'
    AND u.id <> auth.uid()
  ORDER BY u.email
  LIMIT 10;
END;
$$;

-- Share a scenario as a snapshot copy to recipient
CREATE OR REPLACE FUNCTION react_share_scenario(
  source_scenario_id UUID,
  recipient_email_input TEXT
)
RETURNS TABLE (
  shared_scenario_id UUID,
  shared_scenario_name TEXT,
  recipient_user_id UUID,
  recipient_email TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  sender_id UUID := auth.uid();
  sender_email TEXT;
  recipient_id UUID;
  recipient_email TEXT;
  source_record react_scenarios%ROWTYPE;
  inserted_id UUID;
BEGIN
  IF sender_id IS NULL THEN
    RAISE EXCEPTION 'Authentication required';
  END IF;

  SELECT s.*
  INTO source_record
  FROM react_scenarios s
  WHERE s.id = source_scenario_id
    AND s.user_id = sender_id
  LIMIT 1;

  IF source_record.id IS NULL THEN
    RAISE EXCEPTION 'Scenario not found or not owned by user';
  END IF;

  SELECT u.id, u.email::TEXT
  INTO recipient_id, recipient_email
  FROM auth.users u
  WHERE lower(u.email::TEXT) = lower(trim(recipient_email_input))
  LIMIT 1;

  IF recipient_id IS NULL THEN
    RAISE EXCEPTION 'Recipient not found';
  END IF;

  IF recipient_id = sender_id THEN
    RAISE EXCEPTION 'Cannot share scenario to yourself';
  END IF;

  SELECT u.email::TEXT
  INTO sender_email
  FROM auth.users u
  WHERE u.id = sender_id
  LIMIT 1;

  IF EXISTS (
    SELECT 1
    FROM react_scenario_shares rs
    WHERE rs.source_scenario_id = source_record.id
      AND rs.shared_by_user_id = sender_id
      AND rs.recipient_user_id = recipient_id
  ) THEN
    RAISE EXCEPTION 'Scenario already shared with this recipient';
  END IF;

  INSERT INTO react_scenarios (
    user_id,
    name,
    description,
    overrides,
    base_currency,
    is_shared_copy,
    shared_from_scenario_id,
    shared_by_user_id,
    shared_by_email
  )
  VALUES (
    recipient_id,
    source_record.name,
    source_record.description,
    source_record.overrides,
    source_record.base_currency,
    TRUE,
    source_record.id,
    sender_id,
    sender_email
  )
  RETURNING id INTO inserted_id;

  INSERT INTO react_scenario_shares (
    source_scenario_id,
    shared_by_user_id,
    recipient_user_id,
    recipient_email
  )
  VALUES (
    source_record.id,
    sender_id,
    recipient_id,
    recipient_email
  );

  RETURN QUERY
  SELECT inserted_id, source_record.name, recipient_id, recipient_email;
END;
$$;

REVOKE ALL ON FUNCTION react_search_users_by_email(TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION react_search_users_by_email(TEXT) TO authenticated;

REVOKE ALL ON FUNCTION react_share_scenario(UUID, TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION react_share_scenario(UUID, TEXT) TO authenticated;
