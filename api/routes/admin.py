"""
Admin endpoints for quarterly assumption refresh.

Provides:
- POST /api/admin/research-defaults  (AI-powered market data research)
- POST /api/admin/apply-defaults     (apply accepted changes to Supabase)
- GET  /api/admin/refresh-history    (audit trail of past refreshes)
"""

import os
import json
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


# ---- Endpoints ----

@router.post("/research-defaults")
async def research_defaults(
    request: ResearchRequest = ResearchRequest(),
    x_user_email: Optional[str] = Header(None),
):
    """
    Use Claude AI to research current market values for all assumptions.

    Returns a comparison payload with current defaults, AI suggestions,
    differences, and source citations.
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

    # Build the prompt
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")

    assumptions_text = ""
    for key, source_info in data_sources.items():
        current_val = current_flat.get(key, "N/A")
        assumptions_text += (
            f"\n- Key: \"{key}\"\n"
            f"  Display name: {source_info['display_name']}\n"
            f"  Unit: {source_info['unit']}\n"
            f"  Current model value: {current_val}\n"
            f"  Lookup hint: {source_info['lookup_hint']}\n"
            f"  Source: {source_info['source_description']}\n"
        )

    prompt = f"""You are a market data research assistant for a capital market expectations (CME) model.
Today's date is {today}.

For each of the following market assumptions, provide the most current value based on publicly available data.
Return your response as a valid JSON object with the exact keys provided.

For each assumption key, return an object with:
- "suggested_value": the current value as a number (in the same unit as specified - percentage points for %, ratio for x, years for years)
- "source": where you found this data (specific publication, index, date of data)
- "confidence": "high" | "medium" | "low"
- "notes": brief explanation of any significant change from the current model value

IMPORTANT:
- For percentage values, return in percentage points (e.g., 2.5 means 2.5%, not 0.025)
- For ratio values (unit: x), return the ratio directly (e.g., 2.1)
- For year values, return in years (e.g., 7.0)
- Use the most recent available data
- If you cannot find a reliable current value, use the current model value and set confidence to "low"

Here are all the assumptions to research:
{assumptions_text}

Return ONLY valid JSON (no markdown, no code fences, no explanation) with the structure:
{{
  "<key>": {{
    "suggested_value": <number>,
    "source": "<string>",
    "confidence": "<high|medium|low>",
    "notes": "<string>"
  }},
  ...
}}"""

    # Call Anthropic Claude
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            temperature=0.1,
            system="You are a financial data research assistant. Always return valid JSON and nothing else -- no markdown fences, no explanation, just the JSON object.",
            messages=[
                {"role": "user", "content": prompt},
            ],
        )

        ai_response_text = response.content[0].text

        # Strip markdown code fences if Claude wraps the JSON
        cleaned = ai_response_text.strip()
        if cleaned.startswith("```"):
            # Remove opening fence (```json or ```)
            first_newline = cleaned.index("\n")
            cleaned = cleaned[first_newline + 1:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

        ai_suggestions = json.loads(cleaned)

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
