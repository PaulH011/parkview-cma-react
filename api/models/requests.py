"""Pydantic request models for API endpoints."""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class CalculateRequest(BaseModel):
    """Request model for full CME calculation."""
    overrides: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Override values for inputs. Structure matches app.py build_overrides() output."
    )
    base_currency: str = Field(
        default="usd",
        description="Base currency for returns: 'usd' or 'eur'"
    )
    scenario_name: str = Field(
        default="Current Scenario",
        description="Name for this calculation scenario"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "overrides": {
                    "macro": {
                        "us": {
                            "rgdp_growth": 0.02,
                            "inflation_forecast": 0.025
                        }
                    }
                },
                "base_currency": "usd",
                "scenario_name": "Bull Case"
            }
        }


class MacroPreviewRequest(BaseModel):
    """Request model for lightweight macro preview calculation."""
    region: str = Field(
        description="Region identifier: us, eurozone, japan, or em"
    )
    building_blocks: Dict[str, float] = Field(
        description="Building block values (as decimals, e.g., 0.012 for 1.2%)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "region": "us",
                "building_blocks": {
                    "population_growth": 0.004,
                    "productivity_growth": 0.012,
                    "my_ratio": 2.1,
                    "current_headline_inflation": 0.025,
                    "long_term_inflation": 0.022,
                    "current_tbill": 0.0367,
                    "country_factor": 0.0
                }
            }
        }


