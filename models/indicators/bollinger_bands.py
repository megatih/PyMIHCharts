"""
Bollinger Bands technical indicator implementation.
"""

from typing import Any
import pandas as pd
from models.indicators.base import BaseIndicator
from models.enums import IndicatorType, MAType
from models.data_models import BollingerBandsSettings

class BollingerBands(BaseIndicator):
    """
    Calculates volatility-based bands around a moving average.
    """
    
    def __init__(self):
        super().__init__("Bollinger Bands", IndicatorType.OVERLAY)

    def calculate(self, df: pd.DataFrame, settings: BollingerBandsSettings) -> pd.DataFrame:
        """
        Calculates Middle, Upper, and Lower bands.
        """
        df = df.copy()
        period = settings.period
        ma_type = settings.ma_type
        std_devs = settings.std_devs
        
        # 1. Calculate Middle Band
        if ma_type == MAType.EMA:
            middle_band = df['Close'].ewm(span=period, adjust=False).mean()
        else:
            middle_band = df['Close'].rolling(window=period).mean()

        # 2. Calculate rolling standard deviation
        rolling_std = df['Close'].rolling(window=period).std()

        df['bb_middle'] = middle_band
        
        # 3. Generate requested deviation bands
        for std in std_devs:
            df[f'bb_upper_{std}'] = middle_band + (rolling_std * std)
            df[f'bb_lower_{std}'] = middle_band - (rolling_std * std)

        return df
