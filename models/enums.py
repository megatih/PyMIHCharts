"""
Core Enumerations for PyMIHCharts.

This module provides type-safe constants for chart configurations, 
intervals, and indicator parameters.
"""

from enum import Enum, auto

class ChartType(Enum):
    """Available visual representations of price data."""
    CANDLESTICK = "Candlestick"
    OHLC = "OHLC"
    LINE = "Line"
    HEIKEN_ASHI = "Heiken-Ashi"

class Interval(Enum):
    """Supported data intervals for yfinance fetching."""
    MIN_1 = "1m"
    MIN_2 = "2m"
    MIN_5 = "5m"
    MIN_15 = "15m"
    MIN_30 = "30m"
    MIN_60 = "60m"
    MIN_90 = "90m"
    HOUR_1 = "1h"
    DAY_1 = "1d"
    DAY_5 = "5d"
    WEEK_1 = "1wk"
    MONTH_1 = "1mo"
    MONTH_3 = "3mo"

class MAType(Enum):
    """Moving Average types for indicator calculations."""
    SMA = "SMA"
    EMA = "EMA"

class IndicatorType(Enum):
    """Categorization of indicators for UI and Rendering placement."""
    OVERLAY = auto()    # Drawn directly on the Price Pane (e.g., BB, TD)
    SUB_PANE = auto()   # Drawn in a separate bottom pane (e.g., RSI, MACD)
