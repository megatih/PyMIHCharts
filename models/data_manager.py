"""
Model component for fetching and managing market data.
"""

from typing import Optional, Dict, Any, Tuple
import yfinance as yf
import pandas as pd


class DataManager:
    """
    Handles downloading and cleaning financial data from yfinance.
    """

    def __init__(self):
        self.raw_df: Optional[pd.DataFrame] = None
        self.metadata: Dict[str, str] = {}

    def fetch_data(self, symbol: str) -> Tuple[Optional[pd.DataFrame], Dict[str, str]]:
        """
        Downloads historical data and metadata for a given symbol.
        """
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="max", interval="1d")

        if df.empty:
            return None, {}

        # Clean MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        self.raw_df = df
        
        info = ticker.info
        self.metadata = {
            'symbol': symbol,
            'full_name': info.get('longName', symbol),
            'exchange': info.get('exchange', 'Unknown'),
            'currency': info.get('currency', 'USD')
        }
        
        return self.raw_df, self.metadata
