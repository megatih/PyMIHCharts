"""
Registry and Manager for the modular indicator system.
"""

from typing import Dict, List, Any, Type, Optional
import pandas as pd
from models.indicators.base import BaseIndicator
from models.indicators.heiken_ashi import HeikenAshi
from models.indicators.bollinger_bands import BollingerBands
from models.indicators.td_sequential import TDSequential

class IndicatorRegistry:
    """
    A singleton registry that tracks all available technical indicators.
    
    This allows the application to discover and instantiate indicators 
    without hardcoding them into the main data flow.
    """
    _instance: Optional['IndicatorRegistry'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IndicatorRegistry, cls).__new__(cls)
            cls._instance._indicators: Dict[str, BaseIndicator] = {}
            cls._instance._register_defaults()
        return cls._instance

    def _register_defaults(self):
        """Registers the core indicators included with the application."""
        self.register(HeikenAshi())
        self.register(BollingerBands())
        self.register(TDSequential())

    def register(self, indicator: BaseIndicator):
        """Adds a new indicator to the registry."""
        self._indicators[indicator.name] = indicator

    def get_indicator(self, name: str) -> Optional[BaseIndicator]:
        """Retrieves an indicator instance by its name."""
        return self._indicators.get(name)

    def list_indicators(self) -> List[str]:
        """Returns a list of all registered indicator names."""
        return list(self._indicators.keys())

class IndicatorManager:
    """
    Orchestrates the calculation pipeline for technical indicators.
    
    The manager ensures that indicators are calculated in a consistent order
    and handles the passing of specific settings to each indicator class.
    """
    
    def __init__(self):
        self.registry = IndicatorRegistry()

    def calculate_all(self, df: pd.DataFrame, app_state: Any) -> pd.DataFrame:
        """
        Runs the full calculation pipeline on a DataFrame.
        
        Args:
            df: The raw price DataFrame.
            app_state: The AppState containing individual indicator settings.
            
        Returns:
            pd.DataFrame: Enriched with all calculated indicator data.
        """
        # 1. Always calculate Heiken-Ashi (for the HA chart type)
        ha = self.registry.get_indicator("Heiken-Ashi")
        if ha:
            df = ha.calculate(df)

        # 2. Calculate Bollinger Bands if requested
        bb = self.registry.get_indicator("Bollinger Bands")
        if bb:
            df = bb.calculate(df, app_state.bb_settings)

        # 3. Calculate TD Sequential if requested
        td = self.registry.get_indicator("TD Sequential")
        if td:
            df = td.calculate(df, app_state.td_settings)

        # NOTE TO DEVELOPERS: 
        # To add a new indicator to the pipeline:
        # 1. Create a new class in models/indicators/ inheriting from BaseIndicator.
        # 2. Register it in IndicatorRegistry._register_defaults().
        # 3. Add its calculation call here in IndicatorManager.calculate_all().
        
        return df
