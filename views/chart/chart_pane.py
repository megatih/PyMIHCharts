"""
Base class for a single chart pane in the multi-pane architecture.
"""

from typing import Optional, Dict, Any, Tuple
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QFont, QFontMetrics, QColor, QPen
from PySide6.QtCore import Qt, QSize
import pandas as pd
from views.chart.coordinate_mapper import CoordinateMapper

class ChartPane(QWidget):
    """
    An individual drawing area within the larger Chart Container.
    
    Each pane (Price, RSI, MACD) inherits from this class and implements 
    its own 'paintEvent'. It maintains its own CoordinateMapper for 
    independent vertical scaling.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.df: Optional[pd.DataFrame] = None
        self.mapper = CoordinateMapper()
        self.theme: Dict[str, str] = {}
        
        # Rendering state from parent
        self.visible_bars = 150
        self.scroll_offset = 0
        
        # Panning/Zooming state
        self.min_p = 0.0
        self.max_p = 1.0
        
        self.setMouseTracking(True)

    def set_data(self, df: pd.DataFrame, visible_bars: int, scroll_offset: int):
        """Updates the local data reference and viewport state."""
        self.df = df
        self.visible_bars = visible_bars
        self.scroll_offset = scroll_offset
        self.update()

    def apply_theme(self, theme: Dict[str, str]):
        """Updates color configuration."""
        self.theme = theme
        self.update()

    def _get_visible_data(self) -> Tuple[pd.DataFrame, int, int]:
        """Utility to slice the dataframe based on scroll state."""
        if self.df is None or self.df.empty:
            return pd.DataFrame(), 0, 0
        total_len = len(self.df)
        end_idx = total_len - self.scroll_offset
        start_idx = max(0, end_idx - self.visible_bars)
        return self.df.iloc[start_idx:end_idx], start_idx, end_idx

    # NOTE TO DEVELOPERS: 
    # To add a new indicator pane (e.g., RSI):
    # 1. Inherit from ChartPane.
    # 2. Implement paintEvent() using self.mapper.
    # 3. Add the pane to the main ChartContainer layout.
