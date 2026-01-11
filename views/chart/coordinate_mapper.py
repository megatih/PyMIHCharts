"""
Coordinate mapping logic for chart rendering.

This module provides the mathematical transformations required to map
financial data (price, time) to screen coordinates (pixels).
"""

from typing import Tuple
from PySide6.QtCore import QPointF

class CoordinateMapper:
    """
    Handles scaling and transformation for a single chart pane.
    
    Attributes:
        width: Width of the drawable area.
        height: Height of the drawable area.
        padding_top: Top margin.
        padding_bottom: Bottom margin.
        padding_left: Left margin.
        padding_right: Right margin.
    """
    
    def __init__(self):
        self.view_w = 0
        self.view_h = 0
        self.p_top = 0
        self.p_bottom = 0
        self.p_left = 0
        self.p_right = 0
        
        # State used for mapping
        self.min_p = 0.0
        self.max_p = 1.0
        self.p_range = 1.0
        self.visible_bars = 1
        self.scroll_offset = 0

    def update_view_dims(self, w: int, h: int, pt: int, pb: int, pl: int, pr: int):
        """Updates the pixel dimensions of the viewport."""
        self.view_w = w
        self.view_h = h
        self.p_top = pt
        self.p_bottom = pb
        self.p_left = pl
        self.p_right = pr

    def update_data_range(self, min_p: float, max_p: float, visible_bars: int, scroll_offset: int):
        """Updates the data bounds used for scaling."""
        self.min_p = min_p
        self.max_p = max_p
        self.p_range = max_p - min_p if max_p != min_p else 1.0
        self.visible_bars = visible_bars
        self.scroll_offset = scroll_offset

    def price_to_y(self, price: float) -> float:
        """Maps a price value to a vertical pixel coordinate."""
        h = self.view_h - self.p_top - self.p_bottom
        return self.p_top + h - ((price - self.min_p) / self.p_range * h)

    def index_to_x(self, relative_index: int) -> float:
        """
        Maps a relative bar index (0 to visible_bars) to a horizontal pixel.
        
        Args:
            relative_index: Index within the visible window.
        """
        w = self.view_w - self.p_left - self.p_right
        bar_w = w / self.visible_bars
        return self.p_left + (relative_index + 0.5) * bar_w

    def get_bar_width(self) -> float:
        """Returns the width of a single bar in pixels."""
        w = self.view_w - self.p_left - self.p_right
        return w / self.visible_bars
