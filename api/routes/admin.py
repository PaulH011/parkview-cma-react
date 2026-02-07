"""
Admin endpoints for quarterly assumption refresh.

Provides:
- POST /api/admin/research-defaults  (AI-powered market data research)
- POST /api/admin/apply-defaults     (apply accepted changes to Supabase)
- GET  /api/admin/refresh-history    (audit trail of past refreshes)
"""

import os
import re
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from api.config import SUPER_USER_EMAIL, ANTHROPIC_API_KEY

router = APIRouter()

# ---- Paths ----
DATA_SOURCES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_sources.json")


# ---- Pydantic models ----

class AcceptedChange(BaseModel):
    key: str
    new_value: float


class ApplyDefaultsRequest(BaseModel):
    accepted_changes: List[AcceptedChange]
    is_test: bool = False


class ResearchRequest(BaseModel):
    is_test: bool = False


# ---- Helpers ----

def _load_data_sources() -> Dict[str, Any]:
    """Load the data_sources.json config."""
    with open(DATA_SOURCES_PATH, "r") as f:
        return json.load(f)


def _get_supabase_client():
    """Get a Supabase client."""
    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        if url and key:
            return create_client(url, key)
    except Exception as e:
        print(f"[admin] Could not create Supabase client: {e}")
    return None


def _verify_super_user(x_user_email: Optional[str]) -> str:
    """Verify the request is from the super user. Returns email or raises 403."""
    if not SUPER_USER_EMAIL:
        raise HTTPException(status_code=503, detail="Super user not configured on server")

    if not x_user_email:
        raise HTTPException(status_code=401, detail="Missing X-User-Email header")

    if x_user_email.lower() != SUPER_USER_EMAIL.lower():
        raise HTTPException(status_code=403, detail="Not authorized as super user")

    return x_user_email


def _get_current_defaults_flat(defaults: Dict[str, Any]) -> Dict[str, float]:
    """Flatten the nested defaults dict into dot-notation keys."""
    flat = {}
    for category, subcategories in defaults.items():
        if isinstance(subcategories, dict):
            for subcategory, fields in subcategories.items():
                if isinstance(fields, dict):
                    for field, value in fields.items():
                        flat[f"{category}.{subcategory}.{field}"] = value
                else:
                    # Top-level field (e.g., absolute_return.trading_alpha)
                    flat[f"{category}.{subcategory}"] = fields
        else:
            flat[category] = subcategories
    return flat


def _unflatten_key(key: str, value: float, target: Dict[str, Any]):
    """Set a value in a nested dict using dot-notation key."""
    parts = key.split(".")
    current = target
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value


def _split_into_batches(data_sources: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Split data sources into small batches (~10 each) by subcategory.

    Web search results count as input tokens, so batches must be small
    enough that prompt + search results stay under the 30K token/min limit.

    Produces ~8 batches:
      1. Macro US          (10)
      2. Macro Eurozone     (10)
      3. Macro Japan        (10)
      4. Macro EM           (10)
      5. Bonds Global + HY  (10)
      6. Bonds EM           (6)
      7. Equity US + Europe  (10)
      8. Equity Japan + EM + Alternatives  (~12)
    """
    groups: Dict[str, Dict[str, Any]] = {}
    for key, info in data_sources.items():
        parts = key.split(".")
        if parts[0] == "macro":
            batch_key = f"macro_{parts[1]}"  # macro_us, macro_eurozone, etc.
        elif parts[0] == "bonds":
            if parts[1] in ("global", "hy"):
                batch_key = "bonds_dm"
            else:
                batch_key = "bonds_em"
        elif parts[0] == "equity":
            if parts[1] in ("us", "europe"):
                batch_key = "equity_dm"
            else:
                batch_key = "equity_em_alts"
        else:
            # absolute_return.*
            batch_key = "equity_em_alts"

        if batch_key not in groups:
            groups[batch_key] = {}
        groups[batch_key][key] = info

    # Return in a stable order
    order = [
        "macro_us", "macro_eurozone", "macro_japan", "macro_em",
        "bonds_dm", "bonds_em",
        "equity_dm", "equity_em_alts",
    ]
    return [groups[k] for k in order if k in groups]


def _research_single_batch(
    client,
    batch_sources: Dict[str, Any],
    current_flat: Dict[str, float],
    today: str,
    system_prompt: str,
    max_retries: int = 2,
) -> Dict[str, Any]:
    """
    Research a single batch of assumptions using Claude with web search.
    Returns the parsed JSON dict of suggestions.
    Retries on rate-limit (429) errors with a 60-second wait.
    """
    # Build the prompt for this batch
    assumptions_text = ""
    for key, source_info in batch_sources.items():
        current_val = current_flat.get(key, "N/A")
        assumptions_text += (
            f"\n- Key: \"{key}\"\n"
            f"  Display name: {source_info['display_name']}\n"
            f"  Unit: {source_info['unit']}\n"
            f"  Current model value: {current_val}\n"
            f"  Lookup hint: {source_info['lookup_hint']}\n"
            f"  Source: {source_info['source_description']}\n"
        )

    batch_count = len(batch_sources)
    prompt = f"""You are a market data research assistant for a capital market expectations (CME) model.
Today's date is {today}.

IMPORTANT: You have access to web search. Use it to look up the CURRENT values for these market assumptions.
Search financial data sources like FRED, BLS.gov, ECB, BOJ, IMF, multpl.com, Trading Economics, etc.
Do NOT rely solely on your training data — actually search for the latest numbers.

For each of the following {batch_count} market assumptions, provide the most current value based on your web research.
Return your response as a valid JSON object with the exact keys provided.

For each assumption key, return an object with:
- "suggested_value": the current value as a number (in the same unit as specified - percentage points for %, ratio for x, years for years)
- "source": where you found this data (specific publication, index, date of data)
- "source_url": a direct URL to the public data source where this value can be verified (e.g., FRED series page, official statistics page, index provider page). Use well-known stable URLs. If no reliable URL exists, return null.
- "confidence": "high" | "medium" | "low"
- "notes": brief explanation of any significant change from the current model value

IMPORTANT:
- For percentage values, return in percentage points (e.g., 2.5 means 2.5%, not 0.025)
- For ratio values (unit: x), return the ratio directly (e.g., 2.1)
- For year values, return in years (e.g., 7.0)
- Use the most recent available data
- If you cannot find a reliable current value, use the current model value and set confidence to "low"

Here are the assumptions to research:
{assumptions_text}

Return ONLY valid JSON (no markdown, no code fences, no explanation) with the structure:
{{
  "<key>": {{
    "suggested_value": <number>,
    "source": "<string>",
    "source_url": "<string or null>",
    "confidence": "<high|medium|low>",
    "notes": "<string>"
  }},
  ...
}}"""

    tool_def = {
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": 5,
    }

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            messages = [{"role": "user", "content": prompt}]
            all_text_parts: List[str] = []

            # Loop to handle pause_turn
            response = None
            for _cont in range(3):
                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=8000,
                    temperature=0.1,
                    system=system_prompt,
                    messages=messages,
                    tools=[tool_def],
                )

                # Collect text from this response
                for block in response.content:
                    if hasattr(block, "type") and block.type == "text" and hasattr(block, "text"):
                        all_text_parts.append(block.text)

                if response.stop_reason != "pause_turn":
                    break

                # Clean orphaned server_tool_use blocks for continuation
                tool_use_ids = set()
                result_ids = set()
                for block in response.content:
                    btype = getattr(block, "type", None)
                    if btype == "server_tool_use":
                        tool_use_ids.add(getattr(block, "id", None))
                    elif btype == "web_search_tool_result":
                        result_ids.add(getattr(block, "tool_use_id", None))

                unmatched_ids = tool_use_ids - result_ids
                if unmatched_ids:
                    cleaned_content = [
                        block for block in response.content
                        if not (
                            getattr(block, "type", None) == "server_tool_use"
                            and getattr(block, "id", None) in unmatched_ids
                        )
                    ]
                else:
                    cleaned_content = list(response.content)

                if not cleaned_content:
                    break

                messages.append({"role": "assistant", "content": cleaned_content})
                messages.append({
                    "role": "user",
                    "content": "Please continue where you left off and return the complete JSON.",
                })

            # Extract JSON from collected text
            ai_response_text = "\n".join(all_text_parts)
            cleaned = ai_response_text.strip()

            # Strip markdown code fences
            if "```" in cleaned:
                fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", cleaned, re.DOTALL)
                if fence_match:
                    cleaned = fence_match.group(1).strip()

            # Extract JSON object
            if not cleaned.startswith("{"):
                brace_start = cleaned.find("{")
                if brace_start != -1:
                    cleaned = cleaned[brace_start:]
            if not cleaned.endswith("}"):
                brace_end = cleaned.rfind("}")
                if brace_end != -1:
                    cleaned = cleaned[: brace_end + 1]

            return json.loads(cleaned)

        except Exception as e:
            last_error = e
            error_str = str(e)
            # Retry on rate limit errors
            if "rate_limit" in error_str or "429" in error_str:
                if attempt < max_retries:
                    print(f"[admin] Rate limited on batch, waiting 60s before retry (attempt {attempt + 1})...")
                    time.sleep(60)
                    continue
            # Non-retryable error — raise immediately
            raise

    # All retries exhausted
    raise last_error  # type: ignore[misc]


# ---- Endpoints ----

@router.post("/research-defaults")
async def research_defaults(
    request: ResearchRequest = ResearchRequest(),
    x_user_email: Optional[str] = Header(None),
):
    """
    Use Claude AI to research current market values for all assumptions.

    Splits assumptions into batches (by category) and researches each
    batch separately to stay under API rate limits. Results are merged
    into a single comparison payload.
    """
    email = _verify_super_user(x_user_email)

    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=503, detail="Anthropic API key not configured")

    # Load data sources config
    data_sources = _load_data_sources()

    # Load current defaults
    from api.routes.defaults import get_current_defaults
    current_defaults = get_current_defaults()
    current_flat = _get_current_defaults_flat(current_defaults)

    today = datetime.now(timezone.utc).strftime("%B %d, %Y")

    system_prompt = (
        "You are a financial data research assistant. "
        "Use the web search tool to look up CURRENT market data from authoritative sources "
        "(FRED, BLS, ECB, BOJ, IMF, Bloomberg, MSCI, etc.) before compiling your response. "
        "Search for the most recent values — do NOT rely on your training data alone. "
        "After researching, return ONLY valid JSON and nothing else — no markdown fences, no explanation, just the JSON object."
    )

    # Split into small batches to avoid rate limits (30K tokens/min on basic tier).
    # Web search results count as input tokens, so each batch must be small.
    batches = _split_into_batches(data_sources)
    batch_labels = [
        "Macro US", "Macro Eurozone", "Macro Japan", "Macro EM",
        "Bonds DM", "Bonds EM", "Equity DM", "Equity EM+Alts",
    ]

    # Delay between batches (seconds). Must be >60s to fully reset the per-minute token window.
    BATCH_DELAY = 65

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        # Research each batch with a delay between them
        ai_suggestions: Dict[str, Any] = {}

        for i, batch in enumerate(batches):
            label = batch_labels[i] if i < len(batch_labels) else f"Batch {i + 1}"
            print(f"[admin] Researching batch {i + 1}/{len(batches)}: {label} ({len(batch)} assumptions)...")

            batch_result = _research_single_batch(
                client=client,
                batch_sources=batch,
                current_flat=current_flat,
                today=today,
                system_prompt=system_prompt,
            )
            ai_suggestions.update(batch_result)

            # Wait between batches to respect rate limits (skip after last batch)
            if i < len(batches) - 1:
                print(f"[admin] Batch {i + 1} complete. Waiting {BATCH_DELAY}s before next batch...")
                time.sleep(BATCH_DELAY)

        print(f"[admin] All batches complete. Total suggestions: {len(ai_suggestions)}")

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse AI response as JSON: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Claude research failed: {str(e)}"
        )

    # Build comparison payload
    comparisons = []
    for key, source_info in data_sources.items():
        current_val = current_flat.get(key)
        suggestion = ai_suggestions.get(key, {})
        suggested_val = suggestion.get("suggested_value", current_val)

        if current_val is not None and suggested_val is not None:
            abs_diff = round(suggested_val - current_val, 4)
            rel_diff = round(abs_diff / current_val * 100, 2) if current_val != 0 else 0
        else:
            abs_diff = 0
            rel_diff = 0

        comparisons.append({
            "key": key,
            "display_name": source_info["display_name"],
            "category": source_info["category"],
            "subcategory": source_info["subcategory"],
            "unit": source_info["unit"],
            "current_value": current_val,
            "suggested_value": suggested_val,
            "abs_diff": abs_diff,
            "rel_diff": rel_diff,
            "source": suggestion.get("source", source_info["source_description"]),
            "source_url": suggestion.get("source_url") or source_info.get("source_url"),
            "confidence": suggestion.get("confidence", "low"),
            "notes": suggestion.get("notes", ""),
        })

    # Sort by absolute magnitude of difference (biggest changes first)
    comparisons.sort(key=lambda x: abs(x["abs_diff"]), reverse=True)

    # Log to Supabase
    supabase = _get_supabase_client()
    log_id = str(uuid.uuid4())
    if supabase:
        try:
            supabase.table("assumption_refresh_log").insert({
                "id": log_id,
                "initiated_at": datetime.now(timezone.utc).isoformat(),
                "initiated_by": email,
                "suggestions_json": ai_suggestions,
                "applied_changes_json": None,
                "status": "pending" if not request.is_test else "test",
            }).execute()
        except Exception as e:
            print(f"[admin] Could not log research to Supabase: {e}")

    return {
        "log_id": log_id,
        "researched_at": datetime.now(timezone.utc).isoformat(),
        "comparisons": comparisons,
        "total_assumptions": len(comparisons),
        "is_test": request.is_test,
    }


@router.post("/apply-defaults")
async def apply_defaults(
    request: ApplyDefaultsRequest,
    x_user_email: Optional[str] = Header(None),
):
    """
    Apply accepted changes to the default_assumptions table in Supabase.
    """
    email = _verify_super_user(x_user_email)

    supabase = _get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase not available")

    # Load current defaults
    from api.routes.defaults import get_current_defaults, invalidate_defaults_cache
    current_defaults = get_current_defaults()

    # Apply only the accepted changes
    import copy
    new_defaults = copy.deepcopy(current_defaults)

    applied = []
    for change in request.accepted_changes:
        _unflatten_key(change.key, change.new_value, new_defaults)
        applied.append({"key": change.key, "new_value": change.new_value})

    # Upsert into default_assumptions table
    try:
        supabase.table("default_assumptions").upsert({
            "id": 1,
            "defaults_json": new_defaults,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": email,
        }).execute()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save defaults to Supabase: {str(e)}"
        )

    # Log the application
    status = "test" if request.is_test else "applied"
    try:
        supabase.table("assumption_refresh_log").insert({
            "id": str(uuid.uuid4()),
            "initiated_at": datetime.now(timezone.utc).isoformat(),
            "initiated_by": email,
            "suggestions_json": None,
            "applied_changes_json": applied,
            "status": status,
        }).execute()
    except Exception as e:
        print(f"[admin] Could not log application to Supabase: {e}")

    # Invalidate cache so next request picks up new defaults
    invalidate_defaults_cache()

    return {
        "success": True,
        "changes_applied": len(applied),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "is_test": request.is_test,
    }


@router.post("/revert-defaults")
async def revert_defaults(
    x_user_email: Optional[str] = Header(None),
):
    """
    Revert to the original hardcoded defaults.
    Deletes the Supabase default_assumptions row.
    """
    email = _verify_super_user(x_user_email)

    supabase = _get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase not available")

    try:
        supabase.table("default_assumptions").delete().eq("id", 1).execute()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to revert defaults: {str(e)}"
        )

    # Invalidate cache
    from api.routes.defaults import invalidate_defaults_cache
    invalidate_defaults_cache()

    # Log the revert
    try:
        supabase.table("assumption_refresh_log").insert({
            "id": str(uuid.uuid4()),
            "initiated_at": datetime.now(timezone.utc).isoformat(),
            "initiated_by": email,
            "suggestions_json": None,
            "applied_changes_json": {"action": "reverted_to_hardcoded"},
            "status": "applied",
        }).execute()
    except Exception as e:
        print(f"[admin] Could not log revert to Supabase: {e}")

    return {
        "success": True,
        "message": "Reverted to original hardcoded defaults",
    }


@router.get("/refresh-history")
async def refresh_history(
    x_user_email: Optional[str] = Header(None),
    limit: int = 20,
):
    """
    Get recent entries from the assumption_refresh_log.
    """
    _verify_super_user(x_user_email)

    supabase = _get_supabase_client()
    if not supabase:
        return {"history": []}

    try:
        result = (
            supabase.table("assumption_refresh_log")
            .select("*")
            .order("initiated_at", desc=True)
            .limit(limit)
            .execute()
        )
        return {"history": result.data or []}
    except Exception as e:
        print(f"[admin] Could not fetch refresh history: {e}")
        return {"history": []}


@router.get("/last-refresh")
async def last_refresh():
    """
    Get the date of the last successful refresh.
    Public endpoint (no auth required) - used by the quarterly banner.
    """
    supabase = _get_supabase_client()
    if not supabase:
        return {"last_refresh": None}

    try:
        result = (
            supabase.table("assumption_refresh_log")
            .select("initiated_at")
            .eq("status", "applied")
            .order("initiated_at", desc=True)
            .limit(1)
            .execute()
        )
        if result.data and len(result.data) > 0:
            return {"last_refresh": result.data[0]["initiated_at"]}
        return {"last_refresh": None}
    except Exception as e:
        print(f"[admin] Could not fetch last refresh: {e}")
        return {"last_refresh": None}
