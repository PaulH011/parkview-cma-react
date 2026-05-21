"""
Macroeconomic models for GDP growth, inflation, and T-Bill rates.

These models form the foundation for all asset class return calculations.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

from ..inputs.overrides import OverrideManager, TrackedValue, InputSource, extract_values
from ..utils.ewma import sigmoid_my_ratio


@dataclass
class MacroForecast:
    """Container for macroeconomic forecasts."""
    rgdp_growth: float
    inflation: float
    tbill_rate: float
    nominal_gdp_growth: float

    # Component breakdown
    components: Dict[str, Any]

    # Source tracking
    sources: Dict[str, str]


class MacroModel:
    """
    Macroeconomic model implementing RA methodology.

    This model computes:
    1. Real GDP growth forecast
    2. Inflation forecast
    3. T-Bill rate forecast

    All intermediate values can be overridden.
    """

    def __init__(self, override_manager: OverrideManager):
        """
        Initialize the macro model.

        Parameters
        ----------
        override_manager : OverrideManager
            Manager for handling input overrides.
        """
        self.overrides = override_manager

    def forecast_rgdp_growth(self, region: str) -> Dict[str, TrackedValue]:
        """
        Forecast real GDP growth for a region.

        E[RGDP Growth] = E[Output-per-Capita Growth] + E[Population Growth]

        Where:
        E[Output-per-Capita Growth] = Normal Growth + Demographic Effect + Adjustment

        Parameters
        ----------
        region : str
            Region identifier (us, eurozone, japan, em).

        Returns
        -------
        dict
            Forecast components as TrackedValue objects.
        """
        inputs = self.overrides.get_macro_inputs(region)

        # Check for direct override of rgdp_growth
        direct_override = self.overrides.get_value('macro', region, 'rgdp_growth')
        if direct_override.source == InputSource.OVERRIDE:
            return {
                'rgdp_growth': direct_override,
                'population_growth': inputs.get('population_growth', TrackedValue(0.0, InputSource.DEFAULT)),
                'output_per_capita_growth': TrackedValue(
                    direct_override.value - inputs.get('population_growth', TrackedValue(0.0, InputSource.DEFAULT)).value,
                    InputSource.COMPUTED
                ),
            }

        # Get component inputs
        population_growth = inputs.get('population_growth', TrackedValue(0.004, InputSource.DEFAULT))
        productivity_growth = inputs.get('productivity_growth', TrackedValue(0.012, InputSource.DEFAULT))
        my_ratio = inputs.get('my_ratio', TrackedValue(2.0, InputSource.DEFAULT))

        # Calculate demographic effect using MY ratio
        demographic_effect = sigmoid_my_ratio(my_ratio.value)

        # Adjustment factor (typically small, accounts for skewness)
        # Check for override
        adjustment_override = self.overrides.get_value('macro', region, 'rgdp_adjustment')
        if adjustment_override.source == InputSource.OVERRIDE:
            adjustment = adjustment_override.value
            adjustment_source = InputSource.OVERRIDE
        else:
            # Default adjustment based on typical values
            adjustment = -0.003 if region.lower() in ['us', 'eurozone', 'japan'] else -0.005
            adjustment_source = InputSource.DEFAULT

        # Calculate output per capita growth
        output_per_capita = productivity_growth.value + demographic_effect + adjustment

        # Total RGDP growth
        rgdp_growth = output_per_capita + population_growth.value

        return {
            'rgdp_growth': TrackedValue(rgdp_growth, InputSource.COMPUTED),
            'population_growth': population_growth,
            'productivity_growth': productivity_growth,
            'demographic_effect': TrackedValue(demographic_effect, InputSource.COMPUTED),
            'adjustment': TrackedValue(adjustment, adjustment_source),
            'output_per_capita_growth': TrackedValue(output_per_capita, InputSource.COMPUTED),
        }

    def forecast_inflation(self, region: str) -> Dict[str, TrackedValue]:
        """
        Forecast inflation for a region.

        E[Inflation] = 30% × Current Headline + 70% × Long Term + Adjustment

        Parameters
        ----------
        region : str
            Region identifier.

        Returns
        -------
        dict
            Forecast components as TrackedValue objects.
        """
        inputs = self.overrides.get_macro_inputs(region)
        inflation_params = self.overrides.get_inflation_params()

        # Check for direct override
        direct_override = self.overrides.get_value('macro', region, 'inflation_forecast')
        if direct_override.source == InputSource.OVERRIDE:
            return {
                'inflation_forecast': direct_override,
                'current_headline_inflation': inputs.get('current_headline_inflation',
                                                         TrackedValue(0.025, InputSource.DEFAULT)),
                'long_term_inflation': TrackedValue(direct_override.value, InputSource.COMPUTED),
            }

        # Get inputs
        current_headline = inputs.get('current_headline_inflation', TrackedValue(0.025, InputSource.DEFAULT))

        # Long-term inflation (typically inflation target or EWMA of core)
        long_term_override = self.overrides.get_value('macro', region, 'long_term_inflation')
        if long_term_override.source == InputSource.OVERRIDE:
            long_term_inflation = long_term_override.value
            long_term_source = InputSource.OVERRIDE
        else:
            # Q2 2026 long-term inflation defaults by region
            long_term_defaults = {
                'us': 0.030,        # 3.0%
                'eurozone': 0.020,  # 2.0% (ECB target)
                'japan': 0.015,     # 1.5%
                'em': 0.040,        # 4.0%
            }
            long_term_inflation = long_term_defaults.get(region.lower(), 0.025)
            long_term_source = InputSource.DEFAULT

        # Adjustment (typically small negative for skewness)
        adjustment_override = self.overrides.get_value('macro', region, 'inflation_adjustment')
        if adjustment_override.source == InputSource.OVERRIDE:
            adjustment = adjustment_override.value
        else:
            adjustment = 0.0  # Default no adjustment

        # Calculate forecast
        current_weight = inflation_params['current_weight']
        long_term_weight = inflation_params['long_term_weight']

        inflation_forecast = (
            current_weight * current_headline.value +
            long_term_weight * long_term_inflation +
            adjustment
        )

        return {
            'inflation_forecast': TrackedValue(inflation_forecast, InputSource.COMPUTED),
            'current_headline_inflation': current_headline,
            'long_term_inflation': TrackedValue(long_term_inflation, long_term_source),
            'adjustment': TrackedValue(adjustment, InputSource.DEFAULT),
            'current_weight': TrackedValue(current_weight, InputSource.DEFAULT),
            'long_term_weight': TrackedValue(long_term_weight, InputSource.DEFAULT),
        }

    def forecast_tbill(self, region: str, rgdp_forecast: Optional[float] = None,
                       inflation_forecast: Optional[float] = None) -> Dict[str, TrackedValue]:
        """
        Forecast T-Bill rate for a region.

        E[T-Bill] = 30% × Current T-Bill + 70% × Long Term
        Long Term = max(-0.75%, Country Factor + RGDP + Inflation)

        Parameters
        ----------
        region : str
            Region identifier.
        rgdp_forecast : float, optional
            Pre-computed RGDP forecast. If None, computed internally.
        inflation_forecast : float, optional
            Pre-computed inflation forecast. If None, computed internally.

        Returns
        -------
        dict
            Forecast components as TrackedValue objects.
        """
        inputs = self.overrides.get_macro_inputs(region)
        tbill_params = self.overrides.get_tbill_params()

        # Check for direct override
        direct_override = self.overrides.get_value('macro', region, 'tbill_forecast')
        if direct_override.source == InputSource.OVERRIDE:
            return {
                'tbill_forecast': direct_override,
                'current_tbill': inputs.get('current_tbill', TrackedValue(0.04, InputSource.DEFAULT)),
            }

        # Get current T-Bill
        current_tbill = inputs.get('current_tbill', TrackedValue(0.04, InputSource.DEFAULT))

        # Get RGDP forecast if not provided
        if rgdp_forecast is None:
            rgdp_result = self.forecast_rgdp_growth(region)
            rgdp_forecast = rgdp_result['rgdp_growth'].value

        # Get inflation forecast if not provided
        if inflation_forecast is None:
            inflation_result = self.forecast_inflation(region)
            inflation_forecast = inflation_result['inflation_forecast'].value

        # Country factor (liquidity premium adjustment)
        country_factor_override = self.overrides.get_value('macro', region, 'country_factor')
        if country_factor_override.source == InputSource.OVERRIDE:
            country_factor = country_factor_override.value
            country_factor_source = InputSource.OVERRIDE
        else:
            # Q2 2026 country factor defaults
            # EM is structurally negative (financial repression / capital
            # controls suppress short rates below RGDP + Inflation theoretical).
            country_factors = {
                'us': 0.0,
                'eurozone': -0.002,
                'japan': -0.005,
                'em': -0.034,
            }
            country_factor = country_factors.get(region.lower(), 0.0)
            country_factor_source = InputSource.DEFAULT

        # Calculate long-term T-Bill rate
        rate_floor = tbill_params['rate_floor']
        long_term_tbill = max(
            rate_floor,
            country_factor + rgdp_forecast + inflation_forecast
        )

        # Calculate forecast
        current_weight = tbill_params['current_weight']
        long_term_weight = tbill_params['long_term_weight']

        tbill_forecast = (
            current_weight * current_tbill.value +
            long_term_weight * long_term_tbill
        )

        return {
            'tbill_forecast': TrackedValue(tbill_forecast, InputSource.COMPUTED),
            'current_tbill': current_tbill,
            'long_term_tbill': TrackedValue(long_term_tbill, InputSource.COMPUTED),
            'country_factor': TrackedValue(country_factor, country_factor_source),
            'rgdp_forecast': TrackedValue(rgdp_forecast, InputSource.COMPUTED),
            'inflation_forecast': TrackedValue(inflation_forecast, InputSource.COMPUTED),
            'rate_floor': TrackedValue(rate_floor, InputSource.DEFAULT),
        }

    def compute_full_forecast(self, region: str) -> MacroForecast:
        """
        Compute complete macroeconomic forecast for a region.

        Parameters
        ----------
        region : str
            Region identifier.

        Returns
        -------
        MacroForecast
            Complete forecast with all components.
        """
        # Compute each component
        rgdp_result = self.forecast_rgdp_growth(region)
        inflation_result = self.forecast_inflation(region)
        tbill_result = self.forecast_tbill(
            region,
            rgdp_forecast=rgdp_result['rgdp_growth'].value,
            inflation_forecast=inflation_result['inflation_forecast'].value
        )

        # Extract key values
        rgdp_growth = rgdp_result['rgdp_growth'].value
        inflation = inflation_result['inflation_forecast'].value
        tbill_rate = tbill_result['tbill_forecast'].value
        nominal_gdp = rgdp_growth + inflation

        # Combine all components
        components = {
            'rgdp': extract_values(rgdp_result),
            'inflation': extract_values(inflation_result),
            'tbill': extract_values(tbill_result),
        }

        # Track sources
        sources = {}
        for prefix, result in [('rgdp', rgdp_result), ('inflation', inflation_result), ('tbill', tbill_result)]:
            for key, tv in result.items():
                sources[f"{prefix}.{key}"] = tv.source.value

        return MacroForecast(
            rgdp_growth=rgdp_growth,
            inflation=inflation,
            tbill_rate=tbill_rate,
            nominal_gdp_growth=nominal_gdp,
            components=components,
            sources=sources,
        )


def compute_global_rgdp_growth(macro_model: MacroModel, weights: Optional[Dict[str, float]] = None) -> float:
    """
    Compute GDP-weighted global RGDP growth forecast.

    Parameters
    ----------
    macro_model : MacroModel
        The macro model instance.
    weights : dict, optional
        GDP weights by region. Defaults to approximate 2024 weights.

    Returns
    -------
    float
        Global RGDP growth forecast.
    """
    if weights is None:
        # Approximate GDP weights
        weights = {
            'us': 0.26,
            'eurozone': 0.15,
            'japan': 0.05,
            'em': 0.40,  # Includes China, India, etc.
        }

    total_weight = sum(weights.values())
    global_growth = 0.0

    for region, weight in weights.items():
        try:
            forecast = macro_model.compute_full_forecast(region)
            global_growth += (weight / total_weight) * forecast.rgdp_growth
        except ValueError:
            continue  # Skip unknown regions

    return global_growth
