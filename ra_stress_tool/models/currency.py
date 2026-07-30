"""
FX forecasting model using Research Affiliates' PPP-based methodology.

This module provides FX forecasts for translating asset returns between
different base currencies (USD/EUR).
"""

from typing import Dict, Any

from ..config import CURRENCY_TO_MACRO_REGION


class FXModel:
    """
    FX forecasting model using RA's PPP-based methodology.

    The model uses a 30/70 weighting convention:
    - 30% weight on short-term carry (interest rate differential)
    - 70% weight on long-term PPP convergence (inflation differential)
    """

    # Weighting for FX forecast components
    CARRY_WEIGHT = 0.30  # Short-term: interest rate differential
    PPP_WEIGHT = 0.70    # Long-term: inflation differential (PPP)

    def __init__(self, override_manager=None):
        """
        Initialize the FX model.

        Parameters
        ----------
        override_manager : OverrideManager, optional
            Override manager for custom inputs.
        """
        self.override_manager = override_manager

    def forecast_fx_change(
        self,
        home_region: str,
        foreign_region: str,
        macro_forecasts: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Forecast expected annual FX change (home currency depreciation vs foreign).

        The formula follows RA's PPP-based approach:

        E[FX Change] = 30% × (Home T-Bill - Foreign T-Bill)
                     + 70% × (Home Inflation - Foreign Inflation)

        A positive return means the home currency is expected to depreciate,
        which adds to foreign asset returns when expressed in home currency.

        Parameters
        ----------
        home_region : str
            Home currency region ('us', 'eurozone', 'japan', 'em').
        foreign_region : str
            Foreign currency region.
        macro_forecasts : dict
            Macro forecasts by region containing 'tbill_rate' and 'inflation'.

        Returns
        -------
        dict
            FX forecast components:
            - 'fx_change': Total expected FX change (positive = home depreciation)
            - 'carry_component': Interest rate differential contribution
            - 'ppp_component': Inflation differential contribution
            - 'home_tbill': Home T-Bill rate used
            - 'foreign_tbill': Foreign T-Bill rate used
            - 'home_inflation': Home inflation rate used
            - 'foreign_inflation': Foreign inflation rate used
        """
        # Get macro data for each region
        home_macro = macro_forecasts.get(home_region, {})
        foreign_macro = macro_forecasts.get(foreign_region, {})

        # Extract T-Bill rates
        home_tbill = home_macro.get('tbill_rate', 0.0)
        foreign_tbill = foreign_macro.get('tbill_rate', 0.0)

        # Extract inflation rates
        home_inflation = home_macro.get('inflation', 0.0)
        foreign_inflation = foreign_macro.get('inflation', 0.0)

        # Calculate components
        # Carry component: higher home rates -> home currency depreciates
        carry_component = home_tbill - foreign_tbill

        # PPP component: higher home inflation -> home currency depreciates
        ppp_component = home_inflation - foreign_inflation

        # Total FX change (weighted average)
        fx_change = (
            self.CARRY_WEIGHT * carry_component +
            self.PPP_WEIGHT * ppp_component
        )

        return {
            'fx_change': fx_change,
            'carry_component': carry_component,
            'ppp_component': ppp_component,
            'home_tbill': home_tbill,
            'foreign_tbill': foreign_tbill,
            'home_inflation': home_inflation,
            'foreign_inflation': foreign_inflation,
        }

    def get_fx_adjustment_for_asset(
        self,
        home_currency: str,
        asset_local_currency: str,
        macro_forecasts: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get the FX adjustment needed for an asset given base and local currencies.

        Parameters
        ----------
        home_currency : str
            Base currency for returns ('usd' or 'eur').
        asset_local_currency : str
            Local currency of the asset ('usd', 'eur', 'jpy', 'em').
        macro_forecasts : dict
            Macro forecasts by region.

        Returns
        -------
        dict
            FX adjustment details:
            - 'fx_return': FX impact to add to local currency return
            - 'needs_adjustment': Whether adjustment was needed
            - 'components': Detailed FX forecast components (if adjustment needed)
        """
        # Currency to macro region mapping (single source of truth in config)
        currency_to_region = CURRENCY_TO_MACRO_REGION

        # No adjustment needed if asset is in base currency
        if home_currency == asset_local_currency:
            return {
                'fx_return': 0.0,
                'needs_adjustment': False,
                'components': {},
            }

        # Get regions
        home_region = currency_to_region.get(home_currency, 'us')
        foreign_region = currency_to_region.get(asset_local_currency, 'us')

        # Calculate FX forecast
        fx_forecast = self.forecast_fx_change(
            home_region=home_region,
            foreign_region=foreign_region,
            macro_forecasts=macro_forecasts
        )

        return {
            'fx_return': fx_forecast['fx_change'],
            'needs_adjustment': True,
            'components': fx_forecast,
        }
