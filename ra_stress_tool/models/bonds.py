"""
Bond return models for government, high yield, and emerging market bonds.

Bond Return = Yield + Roll Return + Valuation Return - Credit Losses
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

from ..inputs.overrides import OverrideManager, TrackedValue, InputSource, extract_values
from ..config import AssetClass


@dataclass
class BondForecast:
    """Container for bond return forecasts."""
    expected_return_nominal: float
    expected_return_real: float

    # Component breakdown
    yield_component: float
    roll_return: float
    valuation_return: float
    credit_loss: float

    # Inflation used for real return
    inflation: float

    # Full component details
    components: Dict[str, Any]
    sources: Dict[str, str]


class BondModel(ABC):
    """
    Abstract base class for bond return models.

    All bond models follow the common framework:
    Return = Yield + Roll Return + Valuation Return - Credit Losses
    """

    def __init__(self, override_manager: OverrideManager, asset_class: AssetClass):
        """
        Initialize bond model.

        Parameters
        ----------
        override_manager : OverrideManager
            Manager for handling input overrides.
        asset_class : AssetClass
            The specific asset class for this bond model.
        """
        self.overrides = override_manager
        self.asset_class = asset_class

    def get_inputs(self) -> Dict[str, TrackedValue]:
        """Get inputs for this bond model."""
        return self.overrides.get_asset_inputs(self.asset_class)

    @abstractmethod
    def compute_credit_loss(self, inputs: Dict[str, TrackedValue]) -> Dict[str, TrackedValue]:
        """Compute expected credit losses."""
        pass

    def forecast_yield_component(
        self,
        current_yield: float,
        current_yield_source: InputSource,
        default_current_yield: float,
        tbill_forecast: float,
        duration: float,
        forecast_horizon: int = 10
    ) -> Dict[str, TrackedValue]:
        """
        Forecast the average yield over the forecast horizon.

        The yield component accounts for:
        1. Current yield
        2. Expected path of short rates (T-Bill)
        3. Term premium mean reversion

        Parameters
        ----------
        current_yield : float
            Current yield to maturity.
        current_yield_source : InputSource
            Source of the current yield value (DEFAULT or OVERRIDE).
        default_current_yield : float
            The default current yield for this asset class.
        tbill_forecast : float
            Expected T-Bill rate.
        duration : float
            Modified duration.
        forecast_horizon : int
            Years for forecast.

        Returns
        -------
        dict
            Yield forecast components.
        """
        inputs = self.get_inputs()

        # Get the base current_term_premium from inputs
        base_term_premium = inputs.get('current_term_premium',
                                       TrackedValue(0.015, InputSource.DEFAULT))
        
        # If current_yield was overridden, adjust term premium by the same delta
        # This ensures that changing yield by X% changes the term premium by X%
        if current_yield_source == InputSource.OVERRIDE:
            yield_delta = current_yield - default_current_yield
            adjusted_tp = base_term_premium.value + yield_delta
            current_term_premium = TrackedValue(adjusted_tp, InputSource.COMPUTED)
        else:
            current_term_premium = base_term_premium

        # Fair term premium (long-term average)
        fair_term_premium = inputs.get('fair_term_premium',
                                       TrackedValue(0.015, InputSource.DEFAULT))

        # Term premium mean reversion
        # Use exponential decay toward fair value
        mean_reversion = self.overrides.get_mean_reversion_params()
        reversion_speed = abs(mean_reversion.get('bond_term_premium_bounds', (-0.05, -0.015))[0])

        # Average term premium over horizon (decaying from current toward fair)
        avg_term_premium = self._average_mean_reverting_value(
            current_term_premium.value,
            fair_term_premium.value,
            reversion_speed,
            forecast_horizon
        )

        # Average yield = T-Bill + average term premium
        avg_yield = tbill_forecast + avg_term_premium

        return {
            'current_yield': TrackedValue(current_yield, current_yield_source),
            'tbill_forecast': TrackedValue(tbill_forecast, InputSource.COMPUTED),
            'current_term_premium': current_term_premium,
            'fair_term_premium': fair_term_premium,
            'avg_term_premium': TrackedValue(avg_term_premium, InputSource.COMPUTED),
            'avg_yield': TrackedValue(avg_yield, InputSource.COMPUTED),
        }

    def forecast_roll_return(
        self,
        duration: float,
        term_premium: float,
        maturity_years: float = 10.0
    ) -> Dict[str, TrackedValue]:
        """
        Forecast roll return from yield curve roll-down.

        Roll return occurs as bonds "roll down" the yield curve
        as they approach maturity.

        Parameters
        ----------
        duration : float
            Modified duration.
        term_premium : float
            Current term premium.
        maturity_years : float
            Average maturity of the index.

        Returns
        -------
        dict
            Roll return components.
        """
        # Simplified roll return calculation
        # Assumes constant yield curve slope
        # Roll return ≈ (slope) × (duration / maturity)
        slope = term_premium / maturity_years
        roll_return = slope * duration

        return {
            'roll_return': TrackedValue(roll_return, InputSource.COMPUTED),
            'yield_curve_slope': TrackedValue(slope, InputSource.COMPUTED),
            'duration': TrackedValue(duration, InputSource.DEFAULT),
        }

    def forecast_valuation_return(
        self,
        current_term_premium: float,
        fair_term_premium: float,
        duration: float,
        forecast_horizon: int = 10
    ) -> Dict[str, TrackedValue]:
        """
        Forecast valuation return from term premium mean reversion.

        When term premiums are below fair value, we expect yields to rise
        (prices fall, negative valuation return) and vice versa.

        Parameters
        ----------
        current_term_premium : float
            Current term premium.
        fair_term_premium : float
            Fair value term premium.
        duration : float
            Modified duration.
        forecast_horizon : int
            Years for forecast.

        Returns
        -------
        dict
            Valuation return components.
        """
        mean_reversion = self.overrides.get_mean_reversion_params()

        # Change in term premium over horizon
        # Using partial mean reversion
        reversion_fraction = 1 - (1 - 0.03) ** (forecast_horizon * 12)  # Monthly reversion
        reversion_fraction = min(reversion_fraction, 1.0)

        expected_tp_change = (fair_term_premium - current_term_premium) * reversion_fraction

        # Valuation return = -duration × yield change
        # If term premium rises (yields rise), prices fall
        valuation_return = -duration * expected_tp_change / forecast_horizon

        return {
            'valuation_return': TrackedValue(valuation_return, InputSource.COMPUTED),
            'expected_tp_change': TrackedValue(expected_tp_change, InputSource.COMPUTED),
            'reversion_fraction': TrackedValue(reversion_fraction, InputSource.COMPUTED),
        }

    def _average_mean_reverting_value(
        self,
        current: float,
        fair: float,
        reversion_speed: float,
        years: int
    ) -> float:
        """
        Calculate average value over time with mean reversion.

        Parameters
        ----------
        current : float
            Current value.
        fair : float
            Fair/target value.
        reversion_speed : float
            Annual reversion speed (0 to 1).
        years : int
            Time horizon.

        Returns
        -------
        float
            Average value over the period.
        """
        total = 0.0
        value = current

        for _ in range(years):
            total += value
            value = value + reversion_speed * (fair - value)

        return total / years

    def compute_return(
        self,
        tbill_forecast: float,
        inflation_forecast: float,
        forecast_horizon: int = 10
    ) -> BondForecast:
        """
        Compute complete bond return forecast.

        Parameters
        ----------
        tbill_forecast : float
            Expected T-Bill rate.
        inflation_forecast : float
            Expected inflation rate.
        forecast_horizon : int
            Years for forecast.

        Returns
        -------
        BondForecast
            Complete forecast with components.
        """
        inputs = self.get_inputs()

        # Get default current_yield for this asset class from defaults
        from ..inputs.defaults import DefaultInputs
        defaults = DefaultInputs()
        default_inputs = defaults.get_asset_inputs(self.asset_class)
        default_current_yield = default_inputs.get('current_yield', 0.04)

        # Extract key inputs with source tracking
        current_yield_tv = inputs.get('current_yield', TrackedValue(default_current_yield, InputSource.DEFAULT))
        current_yield = current_yield_tv.value
        current_yield_source = current_yield_tv.source
        duration = inputs.get('duration', TrackedValue(7.0, InputSource.DEFAULT)).value

        # Yield component
        yield_result = self.forecast_yield_component(
            current_yield, current_yield_source, default_current_yield, tbill_forecast, duration, forecast_horizon
        )
        avg_yield = yield_result['avg_yield'].value
        current_tp = yield_result['current_term_premium'].value
        fair_tp = yield_result['fair_term_premium'].value

        # Roll return
        roll_result = self.forecast_roll_return(duration, current_tp)
        roll_return = roll_result['roll_return'].value

        # Valuation return
        val_result = self.forecast_valuation_return(current_tp, fair_tp, duration, forecast_horizon)
        valuation_return = val_result['valuation_return'].value

        # Credit losses
        credit_result = self.compute_credit_loss(inputs)
        credit_loss = credit_result.get('credit_loss', TrackedValue(0.0, InputSource.DEFAULT)).value

        # Total return
        expected_return_nominal = avg_yield + roll_return + valuation_return - credit_loss
        expected_return_real = expected_return_nominal - inflation_forecast

        # Combine components
        components = {
            'yield': extract_values(yield_result),
            'roll': extract_values(roll_result),
            'valuation': extract_values(val_result),
            'credit': extract_values(credit_result),
        }

        # Track sources
        sources = {}
        for prefix, result in [('yield', yield_result), ('roll', roll_result),
                               ('valuation', val_result), ('credit', credit_result)]:
            for key, tv in result.items():
                sources[f"{prefix}.{key}"] = tv.source.value

        return BondForecast(
            expected_return_nominal=expected_return_nominal,
            expected_return_real=expected_return_real,
            yield_component=avg_yield,
            roll_return=roll_return,
            valuation_return=valuation_return,
            credit_loss=credit_loss,
            inflation=inflation_forecast,
            components=components,
            sources=sources,
        )


class GovernmentBondModel(BondModel):
    """
    Government bond model (Bonds Global - Developed Government).

    Assumes zero credit losses for sovereign developed market bonds.
    """

    def __init__(self, override_manager: OverrideManager):
        super().__init__(override_manager, AssetClass.BONDS_GLOBAL)

    def compute_credit_loss(self, inputs: Dict[str, TrackedValue]) -> Dict[str, TrackedValue]:
        """Government bonds have zero credit losses."""
        return {
            'credit_loss': TrackedValue(0.0, InputSource.DEFAULT),
            'default_rate': TrackedValue(0.0, InputSource.DEFAULT),
            'recovery_rate': TrackedValue(1.0, InputSource.DEFAULT),
        }


class HighYieldBondModel(BondModel):
    """
    High Yield bond model.

    Incorporates credit spread and expected default losses.
    Credit Loss = Default Rate × (1 - Recovery Rate)
    """

    def __init__(self, override_manager: OverrideManager):
        super().__init__(override_manager, AssetClass.BONDS_HY)

    def compute_credit_loss(self, inputs: Dict[str, TrackedValue]) -> Dict[str, TrackedValue]:
        """
        Compute expected credit losses for high yield bonds.

        Returns
        -------
        dict
            Credit loss components.
        """
        # Get credit parameters
        default_rate = inputs.get('default_rate', TrackedValue(0.055, InputSource.DEFAULT))
        recovery_rate = inputs.get('recovery_rate', TrackedValue(0.40, InputSource.DEFAULT))

        # Annual credit loss
        credit_loss = default_rate.value * (1 - recovery_rate.value)

        return {
            'credit_loss': TrackedValue(credit_loss, InputSource.COMPUTED),
            'default_rate': default_rate,
            'recovery_rate': recovery_rate,
        }

    def compute_return(
        self,
        tbill_forecast: float,
        inflation_forecast: float,
        forecast_horizon: int = 10
    ) -> BondForecast:
        """
        Compute high yield return with credit spread dynamics.

        High yield bonds also have credit spread mean reversion.
        """
        inputs = self.get_inputs()

        # Get credit spread inputs
        credit_spread = inputs.get('credit_spread', TrackedValue(0.0271, InputSource.DEFAULT)).value
        fair_credit_spread = inputs.get('fair_credit_spread', TrackedValue(0.04, InputSource.DEFAULT)).value

        # Base calculation
        forecast = super().compute_return(tbill_forecast, inflation_forecast, forecast_horizon)

        # Add credit spread valuation effect
        duration = inputs.get('duration', TrackedValue(4.0, InputSource.DEFAULT)).value

        # Credit spread mean reversion
        reversion_fraction = 0.5  # 50% reversion over 10 years
        spread_change = (fair_credit_spread - credit_spread) * reversion_fraction

        # Spread widening = price decline (negative valuation)
        spread_valuation = -duration * spread_change / forecast_horizon

        # Adjust return
        adjusted_return = forecast.expected_return_nominal + spread_valuation
        adjusted_real = adjusted_return - inflation_forecast

        # Update components
        forecast.components['credit_spread'] = {
            'current_spread': credit_spread,
            'fair_spread': fair_credit_spread,
            'spread_valuation': spread_valuation,
        }

        return BondForecast(
            expected_return_nominal=adjusted_return,
            expected_return_real=adjusted_real,
            yield_component=forecast.yield_component,
            roll_return=forecast.roll_return,
            valuation_return=forecast.valuation_return + spread_valuation,
            credit_loss=forecast.credit_loss,
            inflation=inflation_forecast,
            components=forecast.components,
            sources=forecast.sources,
        )


class EMBondModel(BondModel):
    """
    Emerging Market Local Currency Bond model.

    Uses EM-specific default rates and T-Bill forecasts.
    """

    def __init__(self, override_manager: OverrideManager):
        super().__init__(override_manager, AssetClass.BONDS_EM)

    def compute_credit_loss(self, inputs: Dict[str, TrackedValue]) -> Dict[str, TrackedValue]:
        """
        Compute expected credit losses for EM local currency bonds.

        EM local currency has relatively low default rates (sovereign in own currency).
        """
        default_rate = inputs.get('default_rate', TrackedValue(0.0018, InputSource.DEFAULT))
        recovery_rate = inputs.get('recovery_rate', TrackedValue(0.40, InputSource.DEFAULT))

        credit_loss = default_rate.value * (1 - recovery_rate.value)

        return {
            'credit_loss': TrackedValue(credit_loss, InputSource.COMPUTED),
            'default_rate': default_rate,
            'recovery_rate': recovery_rate,
        }

    def compute_return(
        self,
        tbill_forecast: float,
        inflation_forecast: float,
        forecast_horizon: int = 10,
        em_tbill_forecast: Optional[float] = None,
        hard_currency: bool = False
    ) -> BondForecast:
        """
        Compute EM bond return.

        Parameters
        ----------
        tbill_forecast : float
            US T-Bill forecast (for reference).
        inflation_forecast : float
            Inflation forecast for real return calculation.
            For hard currency bonds, this should be US/DM inflation.
            For local currency bonds, this is the base before EM premium.
        forecast_horizon : int
            Years for forecast.
        em_tbill_forecast : float, optional
            EM-specific T-Bill forecast. If None, uses US + spread.
        hard_currency : bool, optional
            If True, treats as USD-denominated hard currency bonds.
            Uses passed inflation directly without EM premium adjustment.

        Returns
        -------
        BondForecast
            EM bond forecast.
        """
        inputs = self.get_inputs()

        # Use EM T-Bill if provided, otherwise estimate from US + spread
        if em_tbill_forecast is None:
            em_spread = 0.02  # Default 2% spread over US
            em_tbill_forecast = tbill_forecast + em_spread

        # For hard currency bonds (USD-denominated), use the passed inflation directly
        # (should be US inflation for proper real return calculation)
        # For local currency bonds, add EM inflation premium
        if hard_currency:
            effective_inflation = inflation_forecast
        else:
            em_inflation_premium = inputs.get('em_inflation_premium',
                                              TrackedValue(0.015, InputSource.DEFAULT)).value
            effective_inflation = inflation_forecast + em_inflation_premium

        # Compute base forecast using EM T-Bill
        return super().compute_return(em_tbill_forecast, effective_inflation, forecast_horizon)
