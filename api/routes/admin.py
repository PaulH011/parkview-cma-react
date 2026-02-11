"""
Admin endpoints for quarterly assumption refresh.

Provides:
- POST /api/admin/research-defaults     (start AI research as background job)
- GET  /api/admin/research-status/{id}   (poll for research progress)
- POST /api/admin/apply-defaults         (apply accepted changes to Supabase)
- GET  /api/admin/refresh-history        (audit trail of past refreshes)
"""

import os
import re
import json
import time
import uuid
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

logger = logging.getLogger(__name__)

from api.config import SUPER_USER_EMAIL, ANTHROPIC_API_KEY

router = APIRouter()

# ---- In-memory job store ----
# Stores background research jobs keyed by job_id (UUID string).
# Each job: { status, progress, result, error, started_at }
_research_jobs: Dict[str, Dict[str, Any]] = {}

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
        logger.warning("Could not create Supabase client: %s", e)
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
        "max_uses": 3,
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
                    model="claude-haiku-4-5-20251001",
                    max_tokens=8000,
                    temperature=0.1,
                    system=system_prompt,
                    messages=messages,
                    tools=[tool_def],
                )

                # Log response structure for debugging
                block_types = [getattr(b, "type", "unknown") for b in response.content]
                logger.info("Response blocks: %s, stop_reason=%s", block_types, response.stop_reason)

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
            logger.info("Collected text length: %d chars", len(ai_response_text))

            if not ai_response_text.strip():
                raise ValueError("No text content returned from Claude — response may have been empty or all search blocks")

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

            result = json.loads(cleaned)
            logger.info("Parsed %d keys from response", len(result))
            return result

        except Exception as e:
            last_error = e
            error_str = str(e)
            logger.warning("Batch attempt %d failed: %s", attempt + 1, error_str[:200])
            # Retry on rate limit errors OR empty responses (may be transient)
            is_retryable = (
                "rate_limit" in error_str
                or "429" in error_str
                or "No text content returned" in error_str
            )
            if is_retryable and attempt < max_retries:
                wait = 70 if "rate_limit" in error_str or "429" in error_str else 30
                logger.info("Waiting %ds before retry...", wait)
                time.sleep(wait)
                continue
            # Non-retryable error or retries exhausted — raise
            raise

    # All retries exhausted
    raise last_error  # type: ignore[misc]


# ---- Background research worker ----

def _cleanup_old_jobs():
    """Remove jobs older than 1 hour to prevent memory leaks."""
    now = datetime.now(timezone.utc)
    expired = []
    for jid, job in _research_jobs.items():
        started = datetime.fromisoformat(job["started_at"])
        if (now - started).total_seconds() > 3600:
            expired.append(jid)
    for jid in expired:
        del _research_jobs[jid]


def _run_research_job(job_id: str, email: str, is_test: bool):
    """
    Background worker that runs batched AI research.
    Updates _research_jobs[job_id] in-place so the status endpoint can report progress.
    """
    job = _research_jobs[job_id]

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        data_sources = _load_data_sources()

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

        batches = _split_into_batches(data_sources)
        batch_labels = [
            "Macro US", "Macro Eurozone", "Macro Japan", "Macro EM",
            "Bonds DM", "Bonds EM", "Equity DM", "Equity EM+Alts",
        ]

        BATCH_DELAY = 75

        ai_suggestions: Dict[str, Any] = {}
        failed_batches: List[str] = []

        job["progress"]["total_batches"] = len(batches)

        for i, batch in enumerate(batches):
            label = batch_labels[i] if i < len(batch_labels) else f"Batch {i + 1}"
            job["progress"]["current_batch"] = i + 1
            job["progress"]["current_label"] = label
            job["progress"]["phase"] = "researching"
            logger.info("Job %s: Batch %d/%d: %s (%d assumptions)...", job_id[:8], i + 1, len(batches), label, len(batch))

            try:
                batch_result = _research_single_batch(
                    client=client,
                    batch_sources=batch,
                    current_flat=current_flat,
                    today=today,
                    system_prompt=system_prompt,
                )
                ai_suggestions.update(batch_result)
                job["progress"]["completed_batches"].append(label)
                logger.info("Job %s: Batch %d (%s) succeeded: %d keys", job_id[:8], i + 1, label, len(batch_result))
            except Exception as batch_err:
                logger.error("Job %s: Batch %d (%s) FAILED: %s", job_id[:8], i + 1, label, str(batch_err)[:200])
                failed_batches.append(label)
                job["progress"]["failed_batches"].append(label)

            # Wait between batches (skip after last)
            if i < len(batches) - 1:
                job["progress"]["phase"] = "waiting"
                logger.info("Job %s: Waiting %ds before next batch...", job_id[:8], BATCH_DELAY)
                time.sleep(BATCH_DELAY)

        logger.info("Job %s: All batches done. Suggestions: %d, Failed: %d", job_id[:8], len(ai_suggestions), len(failed_batches))

        if not ai_suggestions:
            job["status"] = "failed"
            job["error"] = f"All research batches failed: {', '.join(failed_batches)}"
            return

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
                    "status": "pending" if not is_test else "test",
                }).execute()
            except Exception as e:
                logger.warning("Could not log research to Supabase: %s", e)

        # Store final result
        job["status"] = "completed"
        job["result"] = {
            "log_id": log_id,
            "researched_at": datetime.now(timezone.utc).isoformat(),
            "comparisons": comparisons,
            "total_assumptions": len(comparisons),
            "is_test": is_test,
        }
        logger.info("Job %s: COMPLETED with %d comparisons", job_id[:8], len(comparisons))

    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
        logger.error("Job %s: FAILED with error: %s", job_id[:8], str(e)[:300])


# ---- Endpoints ----

@router.post("/research-defaults")
async def research_defaults(
    request: ResearchRequest = ResearchRequest(),
    x_user_email: Optional[str] = Header(None),
):
    """
    Start AI market-data research as a background job.
    Returns a job_id immediately — poll /research-status/{job_id} for progress.
    """
    email = _verify_super_user(x_user_email)

    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=503, detail="Anthropic API key not configured")

    # Cleanup old jobs
    _cleanup_old_jobs()

    # Create job entry
    job_id = str(uuid.uuid4())
    _research_jobs[job_id] = {
        "status": "running",
        "progress": {
            "current_batch": 0,
            "total_batches": 8,
            "current_label": "Starting...",
            "completed_batches": [],
            "failed_batches": [],
            "phase": "starting",
        },
        "result": None,
        "error": None,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }

    # Launch background thread
    thread = threading.Thread(
        target=_run_research_job,
        args=(job_id, email, request.is_test),
        daemon=True,
    )
    thread.start()

    logger.info("Started research job %s for %s (test=%s)", job_id[:8], email, request.is_test)

    return {"job_id": job_id}


@router.get("/research-status/{job_id}")
async def research_status(job_id: str):
    """
    Poll this endpoint to check research progress.
    Returns status, progress, and (when complete) the full result.
    """
    job = _research_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Research job not found")

    response: Dict[str, Any] = {
        "status": job["status"],
        "progress": job["progress"],
        "started_at": job["started_at"],
    }

    if job["status"] == "completed":
        response["result"] = job["result"]
    elif job["status"] == "failed":
        response["error"] = job["error"]

    return response


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
        logger.warning("Could not log application to Supabase: %s", e)

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
        logger.warning("Could not log revert to Supabase: %s", e)

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
        logger.warning("Could not fetch refresh history: %s", e)
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
        logger.warning("Could not fetch last refresh: %s", e)
        return {"last_refresh": None}
