"""
Base interface for technical indicators.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
import pandas as pd
from models.enums import IndicatorType

class BaseIndicator(ABC):
    """
    Abstract Base Class for all technical indicators.
    
    Any new indicator must inherit from this class and implement the 'calculate' 
    method. This ensures a consistent interface for the data processing pipeline.
    """

    def __init__(self, name: str, indicator_type: IndicatorType):
        """
        Initializes the indicator metadata.
        
        Args:
            name: Human-readable name (e.g., "Bollinger Bands").
            indicator_type: Whether it's an OVERLAY or SUB_PANE indicator.
        """
        self.name = name
        self.type = indicator_type

    @abstractmethod
    def calculate(self, df: pd.DataFrame, settings: Any) -> pd.DataFrame:
        """
        Performs vectorized calculations on the provided DataFrame.
        
        Args:
            df: Input DataFrame with at least OHLC data.
            settings: A dataclass or dict containing indicator parameters.
            
        Returns:
            pd.DataFrame: The DataFrame enriched with indicator-specific columns.
        """
        pass
