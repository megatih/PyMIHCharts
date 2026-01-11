"""
Data containers and state models for PyMIHCharts.

These dataclasses provide a structured, type-safe way to pass data between
the Model, View, and Controller layers.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import pandas as pd
from models.enums import ChartType, Interval, MAType

@dataclass
class TDSequentialSettings:
    """Parameters for the Tom DeMark Sequential indicator."""
    lookback: int = 4
    setup_max: int = 9
    countdown_max: int = 13
    visible: bool = True

@dataclass
class BollingerBandsSettings:
    """Parameters for the Bollinger Bands indicator."""
    period: int = 20
    ma_type: MAType = MAType.SMA
    std_devs: List[float] = field(default_factory=lambda: [2.0])
    visible: bool = False

@dataclass
class FontSettings:
    """Relative font size configurations for the rendering engine."""
    base_size: int = 13
    header_offset: int = 2
    labels_offset: int = -3
    td_setup_offset: int = -3
    td_countdown_offset: int = -3

@dataclass
class ChartMetadata:
    """Security information associated with a loaded dataset."""
    symbol: str = ""
    full_name: str = ""
    exchange: str = ""
    currency: str = ""

@dataclass
class AppState:
    """
    Global application state container.
    
    Used by the Controller to maintain synchronization between the UI,
    the background workers, and the rendering engine.
    """
    symbol: Optional[str] = None
    interval: Interval = Interval.DAY_1
    chart_type: ChartType = ChartType.CANDLESTICK
    theme_name: str = "Default"
    tooltips_enabled: bool = True
    sidebar_visible: bool = True
    
    # Nested Settings
    td_settings: TDSequentialSettings = field(default_factory=TDSequentialSettings)
    bb_settings: BollingerBandsSettings = field(default_factory=BollingerBandsSettings)
    font_settings: FontSettings = field(default_factory=FontSettings)

@dataclass
class ChartData:
    """Container for a processed dataset and its raw source."""
    df: pd.DataFrame
    metadata: ChartMetadata
    raw_df: pd.DataFrame = field(default_factory=pd.DataFrame)
