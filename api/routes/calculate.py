"""
Calculation endpoints.

Wraps the ra_stress_tool CMEEngine for API access.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import sys
import os

# Add parent directory to path to import ra_stress_tool
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ra_stress_tool.main import CMEEngine
from ra_stress_tool.utils.ewma import sigmoid_my_ratio
from api.models.requests import CalculateRequest, MacroPreviewRequest
from api.models.responses import CalculateResponse, MacroPreviewResponse, AssetResult, MacroDependencyResponse

router = APIRouter()


@router.post("/full", response_model=CalculateResponse)
async def calculate_full(request: CalculateRequest):
    """
    Run full CME calculation with optional overrides.

    This is the main calculation endpoint that computes expected returns
    for all asset classes based on the provided overrides and base currency.

    Returns:
        Complete results including expected returns, components, and macro forecasts.
    """
    try:
        engine = CMEEngine(
            overrides=request.overrides,
            base_currency=request.base_currency.lower(),
            equity_model_type=request.equity_model,
        )
        results = engine.compute_all_returns(request.scenario_name)

        # Get macro forecasts
        macro = engine.compute_macro_forecasts()

        # Helper to convert MacroDependency to response format
        def convert_macro_deps(deps):
            if not deps:
                return {}
            return {
                key: MacroDependencyResponse(
                    macro_input=dep.macro_input,
                    value_used=dep.value_used,
                    source=dep.source,
                    affects=dep.affects,
                    impact_description=dep.impact_description
                )
                for key, dep in deps.items()
            }

        # Convert to JSON-serializable format
        # Filter out 'global' from macro_forecasts (it only has rgdp_growth, no inflation/tbill)
        macro_regions = ['us', 'eurozone', 'japan', 'em']

        # Build FX forecasts if available (non-empty when base currency is EUR)
        fx_forecasts = None
        if results.fx_forecasts:
            fx_forecasts = results.fx_forecasts

        return CalculateResponse(
            scenario_name=results.scenario_name,
            base_currency=results.base_currency,
            results={
                key: AssetResult(
                    expected_return_nominal=r.expected_return_nominal,
                    expected_return_real=r.expected_return_real,
                    components=r.components,
                    inputs_used=r.inputs_used,
                    macro_dependencies=convert_macro_deps(r.macro_dependencies)
                )
                for key, r in results.results.items()
            },
            macro_forecasts={
                region: {
                    "rgdp_growth": macro[region].get("rgdp_growth", 0),
                    "inflation": macro[region].get("inflation", 0),
                    "tbill_rate": macro[region].get("tbill_rate", 0),
                }
                for region in macro_regions
                if region in macro
            },
            fx_forecasts=fx_forecasts,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/macro-preview", response_model=MacroPreviewResponse)
async def calculate_macro_preview(request: MacroPreviewRequest):
    """
    Compute macro forecasts from building blocks (lightweight preview).

    This endpoint performs a quick calculation without running the full CMEEngine,
    useful for real-time preview as users adjust building block inputs.

    The calculation follows the RA methodology:
    - GDP: Output-per-Capita (productivity + demographic + adjustment) + Population
    - Inflation: 30% Current Headline + 70% Long-Term Target
    - T-Bill: 30% Current + 70% Long-Term (GDP + Inflation + Country Factor)
    """
    region = request.region.lower()
    bb = request.building_blocks

    # Extract values with defaults
    pop_growth = bb.get('population_growth', 0.004)
    prod_growth = bb.get('productivity_growth', 0.012)
    my_ratio = bb.get('my_ratio', 2.0)
    curr_infl = bb.get('current_headline_inflation', 0.025)
    lt_infl = bb.get('long_term_inflation', 0.022)
    curr_tb = bb.get('current_tbill', 0.04)
    ctry_factor = bb.get('country_factor', 0.0)

    # Compute GDP forecast
    demographic_effect = sigmoid_my_ratio(my_ratio)
    adjustment = -0.003 if region in ['us', 'eurozone', 'japan'] else -0.005
    output_per_capita = prod_growth + demographic_effect + adjustment
    rgdp_growth = output_per_capita + pop_growth

    # Compute Inflation forecast
    # E[Inflation] = 30% × Current Headline + 70% × Long-Term Target
    inflation_forecast = 0.30 * curr_infl + 0.70 * lt_infl

    # Compute T-Bill forecast
    # Long Term = max(-0.75%, Country Factor + RGDP + Inflation)
    rate_floor = -0.0075
    long_term_tbill = max(rate_floor, ctry_factor + rgdp_growth + inflation_forecast)

    # E[T-Bill] = 30% × Current T-Bill + 70% × Long-Term
    tbill_forecast = 0.30 * curr_tb + 0.70 * long_term_tbill

    return MacroPreviewResponse(
        rgdp_growth=rgdp_growth,
        inflation=inflation_forecast,
        tbill=tbill_forecast,
        intermediate={
            "population_growth": pop_growth,
            "productivity_growth": prod_growth,
            "my_ratio": my_ratio,
            "demographic_effect": demographic_effect,
            "adjustment": adjustment,
            "output_per_capita": output_per_capita,
            "current_headline_inflation": curr_infl,
            "long_term_inflation": lt_infl,
            "current_tbill": curr_tb,
            "country_factor": ctry_factor,
            "long_term_tbill": long_term_tbill,
        }
    )


@router.post("/compare")
async def compare_scenarios(scenarios: list[CalculateRequest]):
    """
    Calculate and compare multiple scenarios side by side.

    Useful for scenario analysis and sensitivity testing.
    """
    if len(scenarios) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 scenarios for comparison")

    results = []
    for scenario in scenarios:
        try:
            engine = CMEEngine(
                overrides=scenario.overrides,
                base_currency=scenario.base_currency.lower(),
                equity_model_type=scenario.equity_model,
            )
            calc_results = engine.compute_all_returns(scenario.scenario_name)

            results.append({
                "scenario_name": scenario.scenario_name,
                "base_currency": scenario.base_currency,
                "results": {
                    key: {
                        "expected_return_nominal": r.expected_return_nominal,
                        "expected_return_real": r.expected_return_real,
                    }
                    for key, r in calc_results.results.items()
                }
            })
        except Exception as e:
            results.append({
                "scenario_name": scenario.scenario_name,
                "error": str(e)
            })

    return {"scenarios": results}
