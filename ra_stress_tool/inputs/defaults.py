"""
Default input values based on Research Affiliates methodology.

This module provides the default assumptions used when no override is specified.
"""

from typing import Dict, Any, Optional
from copy import deepcopy

from ..config import (
    DEFAULT_MARKET_DATA,
    DEFAULT_ASSET_DATA,
    CREDIT_PARAMS,
    EWMA_PARAMS,
    MEAN_REVERSION_PARAMS,
    INFLATION_PARAMS,
    TBILL_PARAMS,
    BOND_PARAMS,
    EQUITY_PARAMS,
    HEDGE_FUND_PARAMS,
    AssetClass,
    Region,
)


class DefaultInputs:
    """
    Manages default input values for all models.

    This class provides a centralized way to access default assumptions
    based on the Research Affiliates methodology.
    """

    @classmethod
    def load_from_supabase(cls) -> Optional["DefaultInputs"]:
        """
        Try to load default assumptions from the Supabase default_assumptions table.
        Returns a DefaultInputs instance with overridden values, or None if unavailable.
        """
        try:
            import os
            from supabase import create_client

            url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
            key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
            if not url or not key:
                return None

            client = create_client(url, key)
            result = client.table("default_assumptions").select("defaults_json").eq("id", 1).execute()
            if result.data and len(result.data) > 0:
                import json
                db_defaults = result.data[0]["defaults_json"]
                if isinstance(db_defaults, str):
                    db_defaults = json.loads(db_defaults)
                # Return standard instance - the API layer handles
                # merging DB defaults with the frontend-facing structure
                return cls()
        except Exception as e:
            print(f"[DefaultInputs] Could not load from Supabase: {e}")
        return None

    def __init__(self):
        """Initialize with all default values from config."""
        self._macro_data = deepcopy(DEFAULT_MARKET_DATA)
        self._asset_data = deepcopy(DEFAULT_ASSET_DATA)
        self._credit_params = deepcopy(CREDIT_PARAMS)
        self._ewma_params = deepcopy(EWMA_PARAMS)
        self._mean_reversion = deepcopy(MEAN_REVERSION_PARAMS)
        self._inflation_params = deepcopy(INFLATION_PARAMS)
        self._tbill_params = deepcopy(TBILL_PARAMS)
        self._bond_params = deepcopy(BOND_PARAMS)
        self._equity_params = deepcopy(EQUITY_PARAMS)
        self._hedge_fund_params = deepcopy(HEDGE_FUND_PARAMS)

    def get_macro_inputs(self, region: str) -> Dict[str, Any]:
        """
        Get macroeconomic inputs for a region.

        Parameters
        ----------
        region : str
            Region identifier (us, eurozone, japan, em).

        Returns
        -------
        dict
            Macro inputs for the region.
        """
        region_key = region.lower()
        if region_key not in self._macro_data:
            raise ValueError(f"Unknown region: {region}. Valid: {list(self._macro_data.keys())}")
        return deepcopy(self._macro_data[region_key])

    def get_asset_inputs(self, asset_class: AssetClass) -> Dict[str, Any]:
        """
        Get default inputs for an asset class.

        Parameters
        ----------
        asset_class : AssetClass
            The asset class enum.

        Returns
        -------
        dict
            Default inputs for the asset class.
        """
        if asset_class not in self._asset_data:
            raise ValueError(f"Unknown asset class: {asset_class}")
        return deepcopy(self._asset_data[asset_class])

    def get_credit_params(self, credit_type: str) -> Dict[str, float]:
        """
        Get credit parameters for a credit type.

        Parameters
        ----------
        credit_type : str
            Credit type (investment_grade, high_yield, em_hard_currency, em_local_currency).

        Returns
        -------
        dict
            Credit parameters.
        """
        if credit_type not in self._credit_params:
            raise ValueError(f"Unknown credit type: {credit_type}")
        return deepcopy(self._credit_params[credit_type])

    def get_ewma_params(self, param_type: str) -> Dict[str, Any]:
        """
        Get EWMA parameters for a calculation type.

        Parameters
        ----------
        param_type : str
            EWMA parameter type.

        Returns
        -------
        dict
            EWMA parameters (window_years, half_life_years).
        """
        if param_type not in self._ewma_params:
            raise ValueError(f"Unknown EWMA param type: {param_type}")
        params = self._ewma_params[param_type]
        return {
            'window_years': params.window_years,
            'half_life_years': params.half_life_years,
        }

    def get_mean_reversion_params(self) -> Dict[str, Any]:
        """Get mean reversion parameters."""
        return deepcopy(self._mean_reversion)

    def get_inflation_params(self) -> Dict[str, float]:
        """Get inflation model parameters."""
        return deepcopy(self._inflation_params)

    def get_tbill_params(self) -> Dict[str, Any]:
        """Get T-Bill model parameters."""
        return deepcopy(self._tbill_params)

    def get_bond_params(self) -> Dict[str, Any]:
        """Get bond model parameters."""
        return deepcopy(self._bond_params)

    def get_equity_params(self) -> Dict[str, Any]:
        """Get equity model parameters."""
        return deepcopy(self._equity_params)

    def get_hedge_fund_params(self) -> Dict[str, Any]:
        """Get hedge fund model parameters."""
        return deepcopy(self._hedge_fund_params)

    def get_all_defaults(self) -> Dict[str, Any]:
        """
        Get all default values as a nested dictionary.

        Returns
        -------
        dict
            Complete default configuration.
        """
        return {
            'macro': deepcopy(self._macro_data),
            'assets': {k.value: v for k, v in self._asset_data.items()},
            'credit': deepcopy(self._credit_params),
            'ewma': {k: {'window_years': v.window_years, 'half_life_years': v.half_life_years}
                     for k, v in self._ewma_params.items()},
            'mean_reversion': deepcopy(self._mean_reversion),
            'inflation': deepcopy(self._inflation_params),
            'tbill': deepcopy(self._tbill_params),
            'bond': deepcopy(self._bond_params),
            'equity': deepcopy(self._equity_params),
            'hedge_fund': deepcopy(self._hedge_fund_params),
        }
