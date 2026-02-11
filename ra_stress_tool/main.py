"""
Main calculation engine for the RA CME Stress Testing Tool.

This module provides the primary interface for computing capital market
expectations across all asset classes, with support for user overrides.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

from .inputs.overrides import OverrideManager
from .models.macro import MacroModel, compute_global_rgdp_growth
from .models.bonds import GovernmentBondModel, HighYieldBondModel, EMBondModel
from .models.equities import EquityModel, EquityRegion
from .models.alternatives import HedgeFundModel
from .models.currency import FXModel
from .output import CMEResults, AssetClassResult, MacroDependency, format_results_table, format_comparison_table
from .config import AssetClass, BaseCurrency, ASSET_LOCAL_CURRENCY, CURRENCY_TO_MACRO_REGION


class CMEEngine:
    """
    Capital Market Expectations calculation engine.

    This is the main interface for computing expected returns across
    all supported asset classes. It coordinates the macro models with
    the individual asset class models.
    """

    # Asset class display names
    ASSET_NAMES = {
        AssetClass.LIQUIDITY: "Liquidity (Cash)",
        AssetClass.BONDS_GLOBAL: "Bonds Global (Gov)",
        AssetClass.BONDS_HY: "Bonds High Yield",
        AssetClass.BONDS_EM: "Bonds EM (Hard Currency)",
        AssetClass.EQUITY_US: "Equity US",
        AssetClass.EQUITY_EUROPE: "Equity Europe",
        AssetClass.EQUITY_JAPAN: "Equity Japan",
        AssetClass.EQUITY_EM: "Equity EM",
        AssetClass.ABSOLUTE_RETURN: "Absolute Return (HF)",
    }

    def __init__(self, overrides: Optional[Dict[str, Any]] = None, base_currency: str = 'usd'):
        """
        Initialize the CME engine.

        Parameters
        ----------
        overrides : dict, optional
            User override dictionary. See OverrideManager for structure.
        base_currency : str, optional
            Base currency for return calculations ('usd' or 'eur'). Default is 'usd'.
        """
        self.override_manager = OverrideManager(overrides)
        self.base_currency = BaseCurrency(base_currency.lower())

        # Initialize models
        self.macro_model = MacroModel(self.override_manager)
        self.equity_model = EquityModel(self.override_manager)
        self.gov_bond_model = GovernmentBondModel(self.override_manager)
        self.hy_bond_model = HighYieldBondModel(self.override_manager)
        self.em_bond_model = EMBondModel(self.override_manager)
        self.hf_model = HedgeFundModel(self.override_manager)
        self.fx_model = FXModel(self.override_manager)

        # Cache for computed macro values
        self._macro_cache: Dict[str, Any] = {}

    def set_overrides(self, overrides: Dict[str, Any]) -> None:
        """
        Set or update overrides.

        Parameters
        ----------
        overrides : dict
            Override dictionary to apply.
        """
        self.override_manager.set_overrides(overrides)
        self._macro_cache.clear()

    def clear_overrides(self) -> None:
        """Clear all overrides and reset to defaults."""
        self.override_manager.clear_overrides()
        self._macro_cache.clear()

    def _get_base_currency_region(self) -> str:
        """Get the macro region for the base currency."""
        if self.base_currency == BaseCurrency.EUR:
            return 'eurozone'
        return 'us'

    def _get_fx_adjustment(self, asset_class: AssetClass) -> Dict[str, Any]:
        """
        Calculate FX adjustment for an asset class based on base currency.

        Parameters
        ----------
        asset_class : AssetClass
            The asset class to calculate FX adjustment for.

        Returns
        -------
        dict
            FX adjustment details with 'fx_return' and 'components'.
        """
        local_currency = ASSET_LOCAL_CURRENCY.get(asset_class, 'usd')

        # Handle 'base' currency assets (Liquidity, Absolute Return)
        # These use the base currency directly, no FX adjustment needed
        if local_currency == 'base':
            return {'fx_return': 0.0, 'components': {}, 'needs_adjustment': False}

        # Determine base currency string
        base_ccy = 'eur' if self.base_currency == BaseCurrency.EUR else 'usd'

        # No adjustment if asset is already in base currency
        if local_currency == base_ccy:
            return {'fx_return': 0.0, 'components': {}, 'needs_adjustment': False}

        # Get macro forecasts for FX calculation
        macro = self.compute_macro_forecasts()

        # Calculate FX adjustment using the FX model
        fx_result = self.fx_model.get_fx_adjustment_for_asset(
            home_currency=base_ccy,
            asset_local_currency=local_currency,
            macro_forecasts=macro
        )

        return {
            'fx_return': fx_result['fx_return'],
            'components': fx_result.get('components', {}),
            'needs_adjustment': fx_result['needs_adjustment']
        }

    def _apply_fx_to_result(
        self,
        result: AssetClassResult,
        asset_class: AssetClass
    ) -> AssetClassResult:
        """
        Apply FX adjustment to an asset class result.

        Parameters
        ----------
        result : AssetClassResult
            The original asset class result in local currency.
        asset_class : AssetClass
            The asset class enum.

        Returns
        -------
        AssetClassResult
            The result adjusted for FX if applicable.
        """
        fx_adj = self._get_fx_adjustment(asset_class)

        if not fx_adj['needs_adjustment'] or fx_adj['fx_return'] == 0.0:
            return result

        # Add FX component to returns
        new_nominal = result.expected_return_nominal + fx_adj['fx_return']
        new_real = result.expected_return_real + fx_adj['fx_return']

        # Add FX to components
        new_components = dict(result.components)
        new_components['fx_return'] = fx_adj['fx_return']

        # Add FX inputs to tracking
        new_inputs = dict(result.inputs_used)
        fx_comps = fx_adj.get('components', {})
        if fx_comps:
            new_inputs['fx_home_tbill'] = {'value': fx_comps.get('home_tbill', 0), 'source': 'computed'}
            new_inputs['fx_foreign_tbill'] = {'value': fx_comps.get('foreign_tbill', 0), 'source': 'computed'}
            new_inputs['fx_home_inflation'] = {'value': fx_comps.get('home_inflation', 0), 'source': 'computed'}
            new_inputs['fx_foreign_inflation'] = {'value': fx_comps.get('foreign_inflation', 0), 'source': 'computed'}
            new_inputs['fx_carry_component'] = {'value': fx_comps.get('carry_component', 0), 'source': 'computed'}
            new_inputs['fx_ppp_component'] = {'value': fx_comps.get('ppp_component', 0), 'source': 'computed'}

        return AssetClassResult(
            asset_class=result.asset_class,
            expected_return_nominal=new_nominal,
            expected_return_real=new_real,
            components=new_components,
            inputs_used=new_inputs,
            macro_dependencies=result.macro_dependencies,
        )

    def compute_fx_forecasts(self) -> Dict[str, Dict[str, float]]:
        """
        Compute FX forecasts for all major currency pairs relative to base currency.

        Returns
        -------
        dict
            FX forecasts by foreign currency.
        """
        if self.base_currency == BaseCurrency.USD:
            return {}  # No FX forecasts needed for USD base

        macro = self.compute_macro_forecasts()
        base_ccy = 'eur' if self.base_currency == BaseCurrency.EUR else 'usd'

        fx_forecasts = {}
        for foreign_ccy in ['usd', 'jpy', 'em']:
            if foreign_ccy != base_ccy:
                fx_result = self.fx_model.get_fx_adjustment_for_asset(
                    home_currency=base_ccy,
                    asset_local_currency=foreign_ccy,
                    macro_forecasts=macro
                )
                fx_forecasts[foreign_ccy] = {
                    'fx_change': fx_result['fx_return'],
                    'carry_component': fx_result['components'].get('carry_component', 0),
                    'ppp_component': fx_result['components'].get('ppp_component', 0),
                }

        return fx_forecasts

    def compute_macro_forecasts(self) -> Dict[str, Any]:
        """
        Compute macro forecasts for all regions.

        Returns
        -------
        dict
            Macro forecasts by region.
        """
        if self._macro_cache:
            return self._macro_cache

        regions = ['us', 'eurozone', 'japan', 'em']
        forecasts = {}

        for region in regions:
            forecast = self.macro_model.compute_full_forecast(region)
            forecasts[region] = {
                'rgdp_growth': forecast.rgdp_growth,
                'inflation': forecast.inflation,
                'tbill_rate': forecast.tbill_rate,
                'nominal_gdp_growth': forecast.nominal_gdp_growth,
                'components': forecast.components,
            }

        # Compute global GDP growth
        global_rgdp = compute_global_rgdp_growth(self.macro_model)
        forecasts['global'] = {'rgdp_growth': global_rgdp}

        self._macro_cache = forecasts
        return forecasts

    def _get_macro_sources(self) -> Dict[str, str]:
        """
        Get the source (default/override) for each macro input.
        
        Returns
        -------
        dict
            Mapping of macro input keys to their sources.
        """
        sources = {}
        
        # Check direct forecast overrides
        direct_fields = ['inflation_forecast', 'rgdp_growth', 'tbill_forecast']
        regions = ['us', 'eurozone', 'japan', 'em']
        
        for region in regions:
            for field in direct_fields:
                override_key = f"macro.{region}.{field}"
                if self.override_manager.has_override(override_key):
                    sources[f"{region}.{field}"] = "override"
                else:
                    sources[f"{region}.{field}"] = "default"
            
            # Check building block inputs
            building_blocks = [
                'population_growth', 'productivity_growth', 'my_ratio',
                'current_headline_inflation', 'long_term_inflation',
                'current_tbill', 'country_factor'
            ]
            for bb in building_blocks:
                override_key = f"macro.{region}.{bb}"
                if self.override_manager.has_override(override_key):
                    sources[f"{region}.{bb}"] = "override"
                else:
                    sources[f"{region}.{bb}"] = "default"
        
        # Global GDP is affected if any regional GDP is overridden
        global_gdp_affected = any(
            sources.get(f"{r}.rgdp_growth") == "override" or
            sources.get(f"{r}.population_growth") == "override" or
            sources.get(f"{r}.productivity_growth") == "override" or
            sources.get(f"{r}.my_ratio") == "override"
            for r in regions
        )
        sources["global.rgdp_growth"] = "affected_by_override" if global_gdp_affected else "computed"
        
        return sources

    def _build_macro_dependencies(
        self,
        asset_type: str,
        macro_region: str,
        macro: Dict[str, Any],
        macro_sources: Dict[str, str],
        include_tbill: bool = True,
        include_inflation: bool = True,
        include_gdp_cap: bool = False,
    ) -> Dict[str, MacroDependency]:
        """
        Build macro dependency tracking for an asset.
        
        Parameters
        ----------
        asset_type : str
            Type of asset for description context ('bond', 'equity', 'liquidity', 'hedge_fund').
        macro_region : str
            The macro region used for this asset.
        macro : dict
            The macro forecasts dictionary.
        macro_sources : dict
            The macro sources dictionary.
        include_tbill : bool
            Whether T-Bill rate is a dependency.
        include_inflation : bool
            Whether inflation is a dependency.
        include_gdp_cap : bool
            Whether global GDP cap is a dependency (for equities).
            
        Returns
        -------
        dict
            MacroDependency objects keyed by dependency name.
        """
        deps = {}
        region_macro = macro[macro_region]
        
        if include_tbill:
            # T-Bill dependency
            tbill_source = macro_sources.get(f"{macro_region}.tbill_forecast", "computed")
            # T-Bill is affected if GDP or inflation are overridden (since long-term T-Bill = GDP + Inflation)
            if tbill_source == "default":
                gdp_source = macro_sources.get(f"{macro_region}.rgdp_growth", "default")
                inf_source = macro_sources.get(f"{macro_region}.inflation_forecast", "default")
                if gdp_source == "override" or inf_source == "override":
                    tbill_source = "affected_by_override"
            
            if asset_type == 'liquidity':
                impact = f"T-Bill rate is the direct cash return ({region_macro['tbill_rate']*100:.2f}%)"
            elif asset_type == 'bond':
                impact = f"Base rate for yield calculation"
            else:
                impact = f"Risk-free rate component"
                
            deps['tbill'] = MacroDependency(
                macro_input=f"{macro_region}.tbill_forecast",
                value_used=region_macro['tbill_rate'],
                source=tbill_source,
                affects=['yield', 'expected_return_nominal'] if asset_type == 'bond' else ['expected_return_nominal'],
                impact_description=impact,
            )
        
        if include_inflation:
            inf_source = macro_sources.get(f"{macro_region}.inflation_forecast", "default")
            
            if asset_type == 'equity':
                impact = f"Added to real return for nominal ({region_macro['inflation']*100:.2f}%)"
            elif asset_type == 'bond':
                impact = f"Subtracted from nominal for real return"
            else:
                impact = f"Inflation forecast for region"
                
            deps['inflation'] = MacroDependency(
                macro_input=f"{macro_region}.inflation_forecast",
                value_used=region_macro['inflation'],
                source=inf_source,
                affects=['expected_return_nominal'] if asset_type == 'equity' else ['expected_return_real'],
                impact_description=impact,
            )
        
        if include_gdp_cap:
            global_rgdp = macro['global']['rgdp_growth']
            gdp_source = macro_sources.get("global.rgdp_growth", "computed")
            
            deps['global_gdp_cap'] = MacroDependency(
                macro_input="global.rgdp_growth",
                value_used=global_rgdp,
                source=gdp_source,
                affects=['real_eps_growth'],
                impact_description=f"Caps EPS growth at {global_rgdp*100:.2f}% (GDP-weighted global average)",
            )
        
        return deps

    def compute_liquidity_return(self) -> AssetClassResult:
        """
        Compute expected return for liquidity (cash/T-Bills).

        Uses the base currency region's T-Bill rate.

        Returns
        -------
        AssetClassResult
            Liquidity return result.
        """
        macro = self.compute_macro_forecasts()
        macro_sources = self._get_macro_sources()

        # Use base currency region
        base_region = self._get_base_currency_region()
        region_macro = macro[base_region]

        nominal_return = region_macro['tbill_rate']
        real_return = nominal_return - region_macro['inflation']

        # Build macro dependencies
        macro_deps = self._build_macro_dependencies(
            asset_type='liquidity',
            macro_region=base_region,
            macro=macro,
            macro_sources=macro_sources,
            include_tbill=True,
            include_inflation=True,
            include_gdp_cap=False,
        )

        # Extract T-Bill computation inputs for display
        tbill_components = region_macro['components'].get('tbill', {})
        inputs_used = {
            'base_currency': {'value': self.base_currency.value, 'source': 'computed'},
        }
        # Add all T-Bill sub-inputs (current_tbill, country_factor, rgdp_forecast, inflation_forecast, etc.)
        for key, val in tbill_components.items():
            if hasattr(val, 'value') and hasattr(val, 'source'):
                inputs_used[key] = {'value': val.value, 'source': val.source.value}
            elif isinstance(val, dict) and 'value' in val:
                inputs_used[key] = val
            else:
                inputs_used[key] = {'value': val, 'source': 'computed'}

        return AssetClassResult(
            asset_class=self.ASSET_NAMES[AssetClass.LIQUIDITY],
            expected_return_nominal=nominal_return,
            expected_return_real=real_return,
            components={
                'tbill_rate': nominal_return,
            },
            inputs_used=inputs_used,
            macro_dependencies=macro_deps,
        )

    def compute_bonds_global_return(self) -> AssetClassResult:
        """
        Compute expected return for global government bonds.

        Returns
        -------
        AssetClassResult
            Government bond return result.
        """
        macro = self.compute_macro_forecasts()
        macro_sources = self._get_macro_sources()

        # Use weighted average of DM T-Bill and inflation
        # Simplified: use US as proxy for global DM
        us_macro = macro['us']

        forecast = self.gov_bond_model.compute_return(
            tbill_forecast=us_macro['tbill_rate'],
            inflation_forecast=us_macro['inflation'],
        )

        # Build macro dependencies
        macro_deps = self._build_macro_dependencies(
            asset_type='bond',
            macro_region='us',
            macro=macro,
            macro_sources=macro_sources,
            include_tbill=True,
            include_inflation=True,
            include_gdp_cap=False,
        )

        return AssetClassResult(
            asset_class=self.ASSET_NAMES[AssetClass.BONDS_GLOBAL],
            expected_return_nominal=forecast.expected_return_nominal,
            expected_return_real=forecast.expected_return_real,
            components={
                'yield': forecast.yield_component,
                'roll_return': forecast.roll_return,
                'valuation': forecast.valuation_return,
                'credit_loss': forecast.credit_loss,
            },
            inputs_used=self._extract_bond_inputs(forecast),
            macro_dependencies=macro_deps,
        )

    def compute_bonds_hy_return(self) -> AssetClassResult:
        """
        Compute expected return for high yield bonds.

        Returns
        -------
        AssetClassResult
            High yield bond return result.
        """
        macro = self.compute_macro_forecasts()
        macro_sources = self._get_macro_sources()
        us_macro = macro['us']

        forecast = self.hy_bond_model.compute_return(
            tbill_forecast=us_macro['tbill_rate'],
            inflation_forecast=us_macro['inflation'],
        )

        # Build macro dependencies
        macro_deps = self._build_macro_dependencies(
            asset_type='bond',
            macro_region='us',
            macro=macro,
            macro_sources=macro_sources,
            include_tbill=True,
            include_inflation=True,
            include_gdp_cap=False,
        )

        return AssetClassResult(
            asset_class=self.ASSET_NAMES[AssetClass.BONDS_HY],
            expected_return_nominal=forecast.expected_return_nominal,
            expected_return_real=forecast.expected_return_real,
            components={
                'yield': forecast.yield_component,
                'roll_return': forecast.roll_return,
                'valuation': forecast.valuation_return,
                'credit_loss': forecast.credit_loss,
            },
            inputs_used=self._extract_bond_inputs(forecast),
            macro_dependencies=macro_deps,
        )

    def compute_bonds_em_return(self) -> AssetClassResult:
        """
        Compute expected return for EM hard currency bonds (USD-denominated).

        For hard currency bonds:
        - Yield based on US T-Bill + EM credit spread (bonds priced off US curve)
        - US inflation for real return (investor receives USD)

        Returns
        -------
        AssetClassResult
            EM bond return result.
        """
        macro = self.compute_macro_forecasts()
        macro_sources = self._get_macro_sources()
        us_macro = macro['us']

        # For hard currency (USD-denominated) bonds:
        # - Use US T-Bill as base rate (bonds priced off US Treasury curve)
        # - Model adds EM credit spread (~2%) when em_tbill_forecast is None
        # - Use US inflation for real return (investor receives USD)
        forecast = self.em_bond_model.compute_return(
            tbill_forecast=us_macro['tbill_rate'],  # US T-Bill as base
            inflation_forecast=us_macro['inflation'],  # US inflation for hard currency
            em_tbill_forecast=None,  # Let model add EM credit spread
            hard_currency=True,  # USD-denominated bonds
        )

        # Build macro dependencies (uses US macro for hard currency bonds)
        macro_deps = self._build_macro_dependencies(
            asset_type='bond',
            macro_region='us',
            macro=macro,
            macro_sources=macro_sources,
            include_tbill=True,
            include_inflation=True,
            include_gdp_cap=False,
        )

        return AssetClassResult(
            asset_class=self.ASSET_NAMES[AssetClass.BONDS_EM],
            expected_return_nominal=forecast.expected_return_nominal,
            expected_return_real=forecast.expected_return_real,
            components={
                'yield': forecast.yield_component,
                'roll_return': forecast.roll_return,
                'valuation': forecast.valuation_return,
                'credit_loss': forecast.credit_loss,
            },
            inputs_used=self._extract_bond_inputs(forecast),
            macro_dependencies=macro_deps,
        )

    def compute_equity_return(self, region: EquityRegion) -> AssetClassResult:
        """
        Compute expected return for an equity region.

        Parameters
        ----------
        region : EquityRegion
            The equity region.

        Returns
        -------
        AssetClassResult
            Equity return result.
        """
        macro = self.compute_macro_forecasts()
        macro_sources = self._get_macro_sources()

        # Map equity region to macro region
        region_map = {
            EquityRegion.US: 'us',
            EquityRegion.EUROPE: 'eurozone',
            EquityRegion.JAPAN: 'japan',
            EquityRegion.EM: 'em',
        }

        macro_region = region_map[region]
        region_macro = macro[macro_region]
        global_rgdp = macro['global']['rgdp_growth']

        forecast = self.equity_model.compute_return(
            region=region,
            inflation_forecast=region_macro['inflation'],
            global_rgdp_growth=global_rgdp,
        )

        # Map region to asset class for naming
        region_to_asset = {
            EquityRegion.US: AssetClass.EQUITY_US,
            EquityRegion.EUROPE: AssetClass.EQUITY_EUROPE,
            EquityRegion.JAPAN: AssetClass.EQUITY_JAPAN,
            EquityRegion.EM: AssetClass.EQUITY_EM,
        }

        # Build macro dependencies (equities use regional inflation + global GDP cap)
        macro_deps = self._build_macro_dependencies(
            asset_type='equity',
            macro_region=macro_region,
            macro=macro,
            macro_sources=macro_sources,
            include_tbill=False,
            include_inflation=True,
            include_gdp_cap=True,
        )

        return AssetClassResult(
            asset_class=self.ASSET_NAMES[region_to_asset[region]],
            expected_return_nominal=forecast.expected_return_nominal,
            expected_return_real=forecast.expected_return_real,
            components={
                'dividend_yield': forecast.dividend_yield,
                'real_eps_growth': forecast.real_eps_growth,
                'valuation_change': forecast.valuation_change,
            },
            inputs_used=self._extract_equity_inputs(forecast),
            macro_dependencies=macro_deps,
        )

    def compute_absolute_return(self) -> AssetClassResult:
        """
        Compute expected return for absolute return (hedge funds).

        Uses the base currency region's T-Bill rate as the risk-free rate.

        Returns
        -------
        AssetClassResult
            Hedge fund return result.
        """
        macro = self.compute_macro_forecasts()
        macro_sources = self._get_macro_sources()

        # Use base currency region for T-Bill and inflation
        base_region = self._get_base_currency_region()
        base_macro = macro[base_region]

        # Still use US equity return for market premium calculation
        us_macro = macro['us']
        equity_forecast = self.equity_model.compute_return(
            region=EquityRegion.US,
            inflation_forecast=us_macro['inflation'],
            global_rgdp_growth=macro['global']['rgdp_growth'],
        )

        forecast = self.hf_model.compute_return(
            tbill_forecast=base_macro['tbill_rate'],
            inflation_forecast=base_macro['inflation'],
            equity_return=equity_forecast.expected_return_nominal,
        )

        inputs_used = self._extract_hf_inputs(forecast)
        inputs_used['base_currency'] = {'value': self.base_currency.value, 'source': 'computed'}

        # Build macro dependencies
        macro_deps = self._build_macro_dependencies(
            asset_type='hedge_fund',
            macro_region=base_region,
            macro=macro,
            macro_sources=macro_sources,
            include_tbill=True,
            include_inflation=True,
            include_gdp_cap=False,
        )
        
        # Also add dependency on US equity return (for market factor)
        us_inf_source = macro_sources.get("us.inflation_forecast", "default")
        global_gdp_source = macro_sources.get("global.rgdp_growth", "computed")
        equity_affected = us_inf_source == "override" or global_gdp_source in ["override", "affected_by_override"]
        
        macro_deps['us_equity_return'] = MacroDependency(
            macro_input="us.equity_return",
            value_used=equity_forecast.expected_return_nominal,
            source="affected_by_override" if equity_affected else "computed",
            affects=['factor_return'],
            impact_description=f"US equity return ({equity_forecast.expected_return_nominal*100:.2f}%) used for market factor premium",
        )

        return AssetClassResult(
            asset_class=self.ASSET_NAMES[AssetClass.ABSOLUTE_RETURN],
            expected_return_nominal=forecast.expected_return_nominal,
            expected_return_real=forecast.expected_return_real,
            components={
                'tbill': forecast.tbill_component,
                'factor_return': forecast.factor_return,
                'trading_alpha': forecast.trading_alpha,
            },
            inputs_used=inputs_used,
            macro_dependencies=macro_deps,
        )

    def compute_all_returns(self, scenario_name: str = "Base Case") -> CMEResults:
        """
        Compute expected returns for all asset classes.

        Parameters
        ----------
        scenario_name : str
            Name for this scenario.

        Returns
        -------
        CMEResults
            Complete CME results.
        """
        results = {}

        # Liquidity (already uses base currency, no FX adjustment needed)
        results[AssetClass.LIQUIDITY.value] = self.compute_liquidity_return()

        # Bonds - apply FX adjustments
        bonds_global = self.compute_bonds_global_return()
        results[AssetClass.BONDS_GLOBAL.value] = self._apply_fx_to_result(
            bonds_global, AssetClass.BONDS_GLOBAL
        )

        bonds_hy = self.compute_bonds_hy_return()
        results[AssetClass.BONDS_HY.value] = self._apply_fx_to_result(
            bonds_hy, AssetClass.BONDS_HY
        )

        bonds_em = self.compute_bonds_em_return()
        results[AssetClass.BONDS_EM.value] = self._apply_fx_to_result(
            bonds_em, AssetClass.BONDS_EM
        )

        # Equities - apply FX adjustments
        region_to_asset = {
            EquityRegion.US: AssetClass.EQUITY_US,
            EquityRegion.EUROPE: AssetClass.EQUITY_EUROPE,
            EquityRegion.JAPAN: AssetClass.EQUITY_JAPAN,
            EquityRegion.EM: AssetClass.EQUITY_EM,
        }
        for region in EquityRegion:
            asset_class = region_to_asset[region]
            equity_result = self.compute_equity_return(region)
            results[asset_class.value] = self._apply_fx_to_result(
                equity_result, asset_class
            )

        # Alternatives (already uses base currency, no FX adjustment needed)
        results[AssetClass.ABSOLUTE_RETURN.value] = self.compute_absolute_return()

        # Get macro assumptions
        macro = self.compute_macro_forecasts()
        macro_summary = {
            region: {
                'rgdp_growth': data['rgdp_growth'],
                'inflation': data['inflation'],
                'tbill_rate': data.get('tbill_rate', 'N/A'),
            }
            for region, data in macro.items()
            if region != 'global'
        }

        # Add FX forecasts if EUR base
        fx_forecasts = self.compute_fx_forecasts()

        return CMEResults(
            scenario_name=scenario_name,
            results=results,
            macro_assumptions=macro_summary,
            overrides_applied=self.override_manager.get_overrides_summary(),
            base_currency=self.base_currency.value,
            fx_forecasts=fx_forecasts,
        )

    def _extract_bond_inputs(self, forecast) -> Dict[str, Dict[str, Any]]:
        """Extract input tracking from bond forecast."""
        inputs = {}
        for section, values in forecast.components.items():
            for key, value in values.items():
                source = forecast.sources.get(f"{section}.{key}", "computed")
                inputs[f"{section}_{key}"] = {'value': value, 'source': source}
        return inputs

    def _extract_equity_inputs(self, forecast) -> Dict[str, Dict[str, Any]]:
        """Extract input tracking from equity forecast."""
        inputs = {}
        for section, values in forecast.components.items():
            for key, value in values.items():
                source = forecast.sources.get(f"{section}.{key}", "computed")
                inputs[f"{section}_{key}"] = {'value': value, 'source': source}
        return inputs

    def _extract_hf_inputs(self, forecast) -> Dict[str, Dict[str, Any]]:
        """Extract input tracking from hedge fund forecast."""
        inputs = {
            'tbill_forecast': {'value': forecast.tbill_component, 'source': 'computed'},
            'trading_alpha': {'value': forecast.trading_alpha, 'source': forecast.sources.get('trading_alpha', 'default')},
        }
        # Add factor betas with proper source tracking (beta value + override source)
        betas = forecast.components.get('factors', {}).get('betas', {})
        for factor in ['market', 'size', 'value', 'profitability', 'investment', 'momentum']:
            beta_val = betas.get(factor, 0)
            beta_source = forecast.sources.get(f'beta_{factor}', 'default')
            inputs[f'beta_{factor}'] = {'value': beta_val, 'source': beta_source}
        # Also keep factor contributions for reference
        for factor, contribution in forecast.factor_contributions.items():
            inputs[f'factor_{factor}'] = {'value': contribution, 'source': 'computed'}
        return inputs


def run_stress_test(
    base_overrides: Optional[Dict[str, Any]] = None,
    stress_overrides: Optional[Dict[str, Any]] = None,
    base_name: str = "RA Defaults",
    stress_name: str = "Stress Scenario",
    base_currency: str = 'usd'
) -> tuple:
    """
    Run a stress test comparing base case to stressed scenario.

    Parameters
    ----------
    base_overrides : dict, optional
        Overrides for base case (defaults to RA methodology).
    stress_overrides : dict, optional
        Overrides for stress scenario.
    base_name : str
        Name for base scenario.
    stress_name : str
        Name for stress scenario.
    base_currency : str, optional
        Base currency for return calculations ('usd' or 'eur'). Default is 'usd'.

    Returns
    -------
    tuple
        (base_results, stress_results, comparison_text)
    """
    # Base case
    base_engine = CMEEngine(base_overrides, base_currency=base_currency)
    base_results = base_engine.compute_all_returns(base_name)

    # Stress case
    stress_engine = CMEEngine(stress_overrides, base_currency=base_currency)
    stress_results = stress_engine.compute_all_returns(stress_name)

    # Comparison
    comparison = format_comparison_table(base_results, stress_results)

    return base_results, stress_results, comparison


# Convenience function for quick calculations
def quick_cme(
    overrides: Optional[Dict[str, Any]] = None,
    print_results: bool = True,
    base_currency: str = 'usd'
) -> CMEResults:
    """
    Quick calculation of CME with optional overrides.

    Parameters
    ----------
    overrides : dict, optional
        Override dictionary.
    print_results : bool
        Whether to print formatted results.
    base_currency : str, optional
        Base currency for return calculations ('usd' or 'eur'). Default is 'usd'.

    Returns
    -------
    CMEResults
        The computed results.
    """
    engine = CMEEngine(overrides, base_currency=base_currency)
    results = engine.compute_all_returns(
        "Custom Scenario" if overrides else "RA Defaults"
    )

    if print_results:
        print(format_results_table(results))

    return results
