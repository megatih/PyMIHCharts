"""
Heiken-Ashi technical indicator implementation.
"""

from typing import Any
import numpy as np
import pandas as pd
from models.indicators.base import BaseIndicator
from models.enums import IndicatorType

class HeikenAshi(BaseIndicator):
    """
    Calculates Heiken-Ashi candles for trend filtering.
    """
    
    def __init__(self):
        super().__init__("Heiken-Ashi", IndicatorType.OVERLAY)

    def calculate(self, df: pd.DataFrame, settings: Any = None) -> pd.DataFrame:
        """
        Formula:
        - HA_Close = (Open + High + Low + Close) / 4
        - HA_Open = (Previous HA_Open + Previous HA_Close) / 2
        - HA_High = max(High, HA_Open, HA_Close)
        - HA_Low = min(Low, HA_Open, HA_Close)
        """
        df = df.copy()
        n = len(df)
        if n == 0:
            return df
        
        # Vectorized close calculation
        ha_close = (df['Open'].values + df['High'].values + df['Low'].values + df['Close'].values) / 4.0
        
        # HA_Open is recursive, so we use a loop (or specialized numba/cython if performance was critical)
        ha_open = np.zeros(n)
        ha_open[0] = (df['Open'].values[0] + df['Close'].values[0]) / 2.0
        
        for i in range(1, n):
            ha_open[i] = (ha_open[i-1] + ha_close[i-1]) / 2.0
            
        df['HA_Open'] = ha_open
        df['HA_Close'] = ha_close
        df['HA_High'] = np.maximum(df['High'].values, np.maximum(ha_open, ha_close))
        df['HA_Low'] = np.minimum(df['Low'].values, np.minimum(ha_open, ha_close))
        
        return df
