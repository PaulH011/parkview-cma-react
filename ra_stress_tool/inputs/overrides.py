"""
Override management for user-specified input assumptions.

This module handles the merging of user overrides with default values,
tracking which values come from defaults vs overrides.
"""

from typing import Dict, Any, Optional, Tuple
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum

from .defaults import DefaultInputs
from ..config import AssetClass


class InputSource(Enum):
    """Source of an input value."""
    DEFAULT = "default"
    OVERRIDE = "override"
    COMPUTED = "computed"


@dataclass
class TrackedValue:
    """A value with its source tracked."""
    value: Any
    source: InputSource

    def __repr__(self):
        return f"TrackedValue({self.value}, source={self.source.value})"


class OverrideManager:
    """
    Manages user overrides and merges them with defaults.

    This class provides a hierarchical override system where users can
    override values at different levels:
    - Macro level (region-specific)
    - Asset class level
    - Individual parameter level

    All retrieved values are tracked to show whether they came from
    defaults or user overrides.
    """

    def __init__(self, overrides: Optional[Dict[str, Any]] = None, equity_model_type: str = 'ra'):
        """
        Initialize the override manager.

        Parameters
        ----------
        overrides : dict, optional
            User override dictionary. Structure:
            {
                'macro': {
                    'us': {'inflation_forecast': 0.025, ...},
                    'eurozone': {...},
                },
                'bonds_global': {'current_yield': 0.04, ...},
                'bonds_hy': {...},
                'equity_us': {...},
                ...
            }
        equity_model_type : str, optional
            Equity model type ('ra' or 'gk'). Passed to DefaultInputs to
            select the correct equity defaults.
        """
        self._defaults = DefaultInputs(equity_model_type=equity_model_type)
        self._overrides = overrides or {}
        self._value_cache: Dict[str, TrackedValue] = {}

    def set_override(self, path: str, value: Any) -> None:
        """
        Set a single override value.

        Parameters
        ----------
        path : str
            Dot-separated path (e.g., 'macro.us.inflation_forecast').
        value : Any
            The override value.
        """
        parts = path.split('.')
        current = self._overrides

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value
        # Invalidate cache
        self._value_cache.clear()

    def set_overrides(self, overrides: Dict[str, Any]) -> None:
        """
        Set multiple overrides at once.

        Parameters
        ----------
        overrides : dict
            Override dictionary to merge in.
        """
        self._merge_dict(self._overrides, overrides)
        self._value_cache.clear()

    def clear_overrides(self) -> None:
        """Clear all overrides."""
        self._overrides = {}
        self._value_cache.clear()

    def _merge_dict(self, base: Dict, updates: Dict) -> None:
        """Recursively merge updates into base dictionary."""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_dict(base[key], value)
            else:
                base[key] = value

    def _get_override_value(self, *path_parts) -> Tuple[Any, bool]:
        """
        Get an override value if it exists.

        Returns
        -------
        tuple
            (value, found) where found is True if override exists.
        """
        current = self._overrides
        for part in path_parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None, False
        return current, True

    def has_override(self, path: str) -> bool:
        """
        Check if an override exists for a given path.

        Parameters
        ----------
        path : str
            Dot-separated path (e.g., 'macro.us.inflation_forecast').

        Returns
        -------
        bool
            True if an override exists at this path.
        """
        parts = path.split('.')
        _, found = self._get_override_value(*parts)
        return found

    def get_macro_inputs(self, region: str) -> Dict[str, TrackedValue]:
        """
        Get macroeconomic inputs with override tracking.

        Parameters
        ----------
        region : str
            Region identifier.

        Returns
        -------
        dict
            Dictionary of TrackedValue objects.
        """
        defaults = self._defaults.get_macro_inputs(region)
        result = {}

        for key, default_value in defaults.items():
            override_value, found = self._get_override_value('macro', region.lower(), key)
            if found:
                result[key] = TrackedValue(override_value, InputSource.OVERRIDE)
            else:
                result[key] = TrackedValue(default_value, InputSource.DEFAULT)

        return result

    def get_asset_inputs(self, asset_class: AssetClass) -> Dict[str, TrackedValue]:
        """
        Get asset class inputs with override tracking.

        Parameters
        ----------
        asset_class : AssetClass
            The asset class.

        Returns
        -------
        dict
            Dictionary of TrackedValue objects.
        """
        defaults = self._defaults.get_asset_inputs(asset_class)
        result = {}

        asset_key = asset_class.value

        for key, default_value in defaults.items():
            override_value, found = self._get_override_value(asset_key, key)
            if found:
                if isinstance(default_value, dict) and isinstance(override_value, dict):
                    # Merge nested overrides with nested defaults (used by regime-based assets)
                    merged = deepcopy(default_value)
                    self._merge_dict(merged, override_value)
                    result[key] = TrackedValue(merged, InputSource.OVERRIDE)
                else:
                    result[key] = TrackedValue(override_value, InputSource.OVERRIDE)
            else:
                result[key] = TrackedValue(default_value, InputSource.DEFAULT)

        return result

    def get_credit_params(self, credit_type: str) -> Dict[str, TrackedValue]:
        """
        Get credit parameters with override tracking.

        Parameters
        ----------
        credit_type : str
            Credit type identifier.

        Returns
        -------
        dict
            Dictionary of TrackedValue objects.
        """
        defaults = self._defaults.get_credit_params(credit_type)
        result = {}

        for key, default_value in defaults.items():
            override_value, found = self._get_override_value('credit', credit_type, key)
            if found:
                result[key] = TrackedValue(override_value, InputSource.OVERRIDE)
            else:
                result[key] = TrackedValue(default_value, InputSource.DEFAULT)

        return result

    def get_value(
        self,
        category: str,
        subcategory: Optional[str] = None,
        param: Optional[str] = None,
        default: Any = None
    ) -> TrackedValue:
        """
        Get a specific value with override tracking.

        Parameters
        ----------
        category : str
            Top-level category (macro, bonds_hy, equity_us, etc.).
        subcategory : str, optional
            Subcategory (region for macro, or None).
        param : str, optional
            Parameter name.
        default : Any
            Default value if not found anywhere.

        Returns
        -------
        TrackedValue
            The value with its source.
        """
        # Build path
        path_parts = [category]
        if subcategory:
            path_parts.append(subcategory)
        if param:
            path_parts.append(param)

        # Check override
        override_value, found = self._get_override_value(*path_parts)
        if found:
            return TrackedValue(override_value, InputSource.OVERRIDE)

        # Return default
        return TrackedValue(default, InputSource.DEFAULT)

    def get_ewma_params(self, param_type: str) -> Dict[str, Any]:
        """Get EWMA parameters (rarely overridden)."""
        return self._defaults.get_ewma_params(param_type)

    def get_mean_reversion_params(self) -> Dict[str, Any]:
        """Get mean reversion parameters."""
        return self._defaults.get_mean_reversion_params()

    def get_inflation_params(self) -> Dict[str, float]:
        """Get inflation model parameters."""
        return self._defaults.get_inflation_params()

    def get_tbill_params(self) -> Dict[str, Any]:
        """Get T-Bill model parameters."""
        return self._defaults.get_tbill_params()

    def get_bond_params(self) -> Dict[str, Any]:
        """Get bond model parameters."""
        return self._defaults.get_bond_params()

    def get_equity_params(self) -> Dict[str, Any]:
        """Get equity model parameters."""
        return self._defaults.get_equity_params()

    def get_hedge_fund_params(self) -> Dict[str, Any]:
        """Get hedge fund model parameters."""
        return self._defaults.get_hedge_fund_params()

    def get_overrides_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all active overrides.

        Returns
        -------
        dict
            All override values currently set.
        """
        return deepcopy(self._overrides)

    def compare_with_defaults(self) -> Dict[str, Dict[str, Tuple[Any, Any]]]:
        """
        Compare current overrides with defaults.

        Returns
        -------
        dict
            Dictionary showing {path: (default_value, override_value)}.
        """
        result = {}
        all_defaults = self._defaults.get_all_defaults()

        def compare_recursive(defaults_dict, overrides_dict, path=""):
            for key, default_val in defaults_dict.items():
                current_path = f"{path}.{key}" if path else key

                if isinstance(default_val, dict):
                    override_sub = overrides_dict.get(key, {}) if isinstance(overrides_dict, dict) else {}
                    compare_recursive(default_val, override_sub, current_path)
                else:
                    if isinstance(overrides_dict, dict) and key in overrides_dict:
                        override_val = overrides_dict[key]
                        if default_val != override_val:
                            result[current_path] = (default_val, override_val)

        compare_recursive(all_defaults, self._overrides)
        return result


def extract_values(tracked_dict: Dict[str, TrackedValue]) -> Dict[str, Any]:
    """
    Extract raw values from a dictionary of TrackedValue objects.

    Parameters
    ----------
    tracked_dict : dict
        Dictionary with TrackedValue values.

    Returns
    -------
    dict
        Dictionary with raw values.
    """
    return {key: tv.value for key, tv in tracked_dict.items()}


def extract_sources(tracked_dict: Dict[str, TrackedValue]) -> Dict[str, str]:
    """
    Extract sources from a dictionary of TrackedValue objects.

    Parameters
    ----------
    tracked_dict : dict
        Dictionary with TrackedValue values.

    Returns
    -------
    dict
        Dictionary mapping keys to source strings.
    """
    return {key: tv.source.value for key, tv in tracked_dict.items()}
