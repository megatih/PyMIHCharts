"""
Native candlestick chart rendering engine using PySide6's QPainter.

This module provides a high-performance, interactive candlestick chart widget
with specialized rendering for TD Sequential indicators. It avoids heavy
web-based rendering in favor of native GDI/Painter calls.
"""

import sys
import math
from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QMouseEvent, QWheelEvent
from PySide6.QtCore import Qt, QRectF, QPointF, Signal
import pandas as pd
import numpy as np


class CandlestickChart(QWidget):
    """
    A custom QWidget for rendering interactive candlestick charts.

    Features:
    - High-performance QPainter-based rendering.
    - Interactive zoom (mouse wheel) and pan (click-drag).
    - Dynamic price axis with "nice" increments (1-2-5 logic).
    - Smart date axis that adapts to zoom levels.
    - TD Sequential indicator visualization (Setup and Countdown).
    - Snapping crosshairs and hover data reporting.
    """

    # Signal emitted when the mouse hovers over a different price bar
    hovered_data_changed = Signal(object)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.df: Optional[pd.DataFrame] = None
        self.symbol: str = ""
        
        # --- View State ---
        self.visible_bars: int = 150
        self.scroll_offset: int = 0  # Number of bars hidden from the right
        
        # --- Layout & Margins ---
        self.padding_left: int = 60
        self.padding_right: int = 60
        self.padding_top: int = 40
        self.padding_bottom: int = 40

        # --- Interaction State ---
        self.last_mouse_pos: Optional[QPointF] = None
        self.mouse_point: Optional[QPointF] = None  # Current crosshair position

        # --- Cached GDI Objects ---
        # Initializing objects once to avoid allocation overhead during paintEvent
        self.font_main = QFont("Arial", 12, QFont.Bold)
        self.font_labels = QFont("Arial", 8)
        self.font_countdown = QFont("Arial", 10, QFont.Bold)
        
        self.pen_grid = QPen(QColor(60, 60, 60), 1)
        self.color_bg = QColor(30, 30, 30)
        self.color_bull = QColor(0, 200, 0)
        self.color_bear = QColor(200, 0, 0)
        self.color_setup_buy = QColor(0, 255, 0)
        self.color_setup_sell = QColor(255, 50, 50)
        self.color_cd_buy = QColor(0, 255, 255)
        self.color_cd_sell = QColor(255, 255, 0)
        self.color_perfected = QColor(255, 0, 255)  # Magenta for perfected setups

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

    def set_data(self, df: pd.DataFrame, symbol: str):
        """
        Updates the chart with new price data and indicator results.

        Args:
            df: DataFrame containing Open, High, Low, Close and TD columns.
            symbol: The ticker symbol string for the title.
        """
        self.df = df
        self.symbol = symbol
        self.scroll_offset = 0
        if df is not None and not df.empty:
            # Adjust visible bars if the dataset is small
            self.visible_bars = min(150, len(df))
        self.update()

    def paintEvent(self, event):
        """
        The main rendering loop for the chart.
        Called by Qt whenever the widget needs to be redrawn.
        """
        if self.df is None or self.df.empty:
            painter = QPainter(self)
            painter.setPen(Qt.white)
            painter.drawText(self.rect(), Qt.AlignCenter, "No Data Loaded")
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), self.color_bg)
        
        # Determine the slice of data currently visible on screen
        total_len = len(self.df)
        end_idx = total_len - self.scroll_offset
        start_idx = max(0, end_idx - self.visible_bars)
        visible_df = self.df.iloc[start_idx:end_idx]
        
        if visible_df.empty:
            return

        # Calculate Price Range for the visible slice
        min_p = visible_df['Low'].min()
        max_p = visible_df['High'].max()
        # Add 10% vertical buffer
        buf = (max_p - min_p) * 0.1
        min_p -= buf
        max_p += buf
        p_range = max_p - min_p
        
        # Calculate Canvas dimensions
        w = self.width() - self.padding_left - self.padding_right
        h = self.height() - self.padding_top - self.padding_bottom
        bar_w = w / self.visible_bars
        
        def price_to_y(price: float) -> float:
            """Helper to map a price value to a vertical pixel coordinate."""
            return self.padding_top + h - ((price - min_p) / p_range * h)

        # --- 1. Dynamic Price Axis (1-2-5 Logic) ---
        # We want to find "nice" mathematical increments for gridlines.
        min_spacing_px = 50
        max_ticks = max(1, h // min_spacing_px)
        raw_inc = p_range / max_ticks if p_range > 0 else 1
        
        # Find the power of 10 for the current scale
        p10 = 10 ** math.floor(math.log10(raw_inc))
        # Test 1x, 2x, 5x, and 10x steps
        possible_incs = [p10, 2 * p10, 5 * p10, 10 * p10]
        nice_inc = min(possible_incs, key=lambda x: abs(x - raw_inc))
        
        # Determine decimal precision based on increment size
        if nice_inc >= 1:
            precision = 0 if nice_inc == int(nice_inc) else 1
        else:
            precision = math.ceil(-math.log10(nice_inc))

        # Draw Price Gridlines and Labels
        painter.setFont(self.font_labels)
        first_tick = math.ceil(min_p / nice_inc) * nice_inc
        curr_tick = first_tick
        
        while curr_tick <= max_p:
            y = price_to_y(curr_tick)
            
            # Draw horizontal gridline
            painter.setPen(self.pen_grid)
            painter.drawLine(self.padding_left, y, self.width() - self.padding_right, y)
            
            # Draw price label on the right
            painter.setPen(Qt.gray)
            txt = f"{curr_tick:.{precision}f}"
            painter.drawText(self.width() - self.padding_right + 5, int(y + 5), txt)
            
            curr_tick += nice_inc

        # --- 2. Smart Date Axis ---
        painter.setFont(self.font_labels)
        visible_indices = range(start_idx, end_idx)
        
        if len(visible_indices) > 0:
            # Pass 1: Identify all Month and Year transitions in the visible data
            last_year, last_month = -1, -1
            all_transitions = []
            for i, idx in enumerate(visible_indices):
                d = self.df.index[idx]
                if d.year != last_year or d.month != last_month:
                    all_transitions.append({
                        'rel_idx': i, 
                        'date': d, 
                        'is_year': d.year != last_year
                    })
                    last_year, last_month = d.year, d.month

            # Pass 2: Calculate optimal month step based on pixel density
            # We aim for roughly 60 pixels per label
            total_months = len(all_transitions)
            avg_px_per_month = w / total_months if total_months > 0 else 100
            
            if avg_px_per_month >= 60: month_step = 1
            elif avg_px_per_month >= 30: month_step = 2
            elif avg_px_per_month >= 20: month_step = 3
            elif avg_px_per_month >= 10: month_step = 6
            else: month_step = 12

            # Pass 3: Draw date labels and vertical gridlines
            for trans in all_transitions:
                d = trans['date']
                x = self.padding_left + (trans['rel_idx'] + 0.5) * bar_w
                
                # Logic: Always draw Year starts. Draw Months if they match the step.
                should_draw = trans['is_year'] or ((d.month - 1) % month_step == 0)
                
                if should_draw:
                    painter.setPen(self.pen_grid)
                    painter.drawLine(x, self.padding_top, x, self.height() - self.padding_bottom)
                    
                    if trans['is_year']:
                        painter.setPen(Qt.white)
                        painter.setFont(QFont("Arial", 8, QFont.Bold))
                        txt = d.strftime('%Y')
                    else:
                        painter.setPen(Qt.gray)
                        painter.setFont(self.font_labels)
                        txt = d.strftime('%b')
                    
                    painter.drawText(int(x - 15), int(self.height() - self.padding_bottom + 15), txt)

        # --- 3. Candlesticks & TD Sequential Indicators ---
        # Extract slices into arrays for efficient iteration
        setup_counts = visible_df['setup_count'].values
        setup_types = visible_df['setup_type'].values
        perfected = visible_df['perfected'].values
        cd_counts = visible_df['countdown_count'].values
        cd_types = visible_df['countdown_type'].values
        opens = visible_df['Open'].values
        highs = visible_df['High'].values
        lows = visible_df['Low'].values
        closes = visible_df['Close'].values

        for i in range(len(visible_df)):
            x_center = self.padding_left + (i + 0.5) * bar_w
            
            # Draw Candlestick
            color = self.color_bull if closes[i] >= opens[i] else self.color_bear
            painter.setPen(QPen(color, 1))
            painter.setBrush(color)
            
            y_high = price_to_y(highs[i])
            y_low = price_to_y(lows[i])
            painter.drawLine(QPointF(x_center, y_high), QPointF(x_center, y_low))
            
            y_open = price_to_y(opens[i])
            y_close = price_to_y(closes[i])
            body_top = min(y_open, y_close)
            body_h = max(1, abs(y_open - y_close))
            painter.drawRect(QRectF(x_center - bar_w * 0.35, body_top, bar_w * 0.7, body_h))
            
            # --- Draw TD Setup Phase Numbers ---
            sc = setup_counts[i]
            st = setup_types[i]
            is_perf = perfected[i]

            if sc > 0:
                painter.setFont(self.font_labels)
                if is_perf:
                    painter.setPen(self.color_perfected)
                elif st == 'buy':
                    painter.setPen(self.color_setup_buy)
                else:
                    painter.setPen(self.color_setup_sell)
                
                if st == 'buy':
                    painter.drawText(QRectF(x_center - 10, y_low + 5, 20, 15), Qt.AlignCenter, str(sc))
                else:
                    painter.drawText(QRectF(x_center - 10, y_high - 20, 20, 15), Qt.AlignCenter, str(sc))

            # --- Draw TD Countdown Phase Numbers ---
            cc = cd_counts[i]
            ct = cd_types[i]
            if cc > 0:
                painter.setFont(self.font_countdown)
                # Handle deferred 13 (represented internally as 12.5)
                txt = "13+" if cc == 12.5 else str(int(cc))
                
                if ct == 'buy':
                    painter.setPen(self.color_cd_buy)
                    painter.drawText(QRectF(x_center - 15, y_low + 20, 30, 20), Qt.AlignCenter, txt)
                else:
                    painter.setPen(self.color_cd_sell)
                    painter.drawText(QRectF(x_center - 15, y_high - 40, 30, 20), Qt.AlignCenter, txt)

        # --- 4. Legend ---
        lx, ly = self.width() - 180, 10
        painter.setBrush(QColor(45, 45, 45, 200))
        painter.setPen(QPen(Qt.gray, 1))
        painter.drawRect(lx, ly, 160, 110)
        painter.setFont(self.font_labels)
        
        legend_items = [
            (self.color_setup_buy, "Buy Setup (1-9)"),
            (self.color_setup_sell, "Sell Setup (1-9)"),
            (self.color_perfected, "Perfected Setup"),
            (self.color_cd_buy, "Buy Countdown (13)"),
            (self.color_cd_sell, "Sell Countdown (13)")
        ]
        for idx, (col, txt) in enumerate(legend_items):
            iy = ly + 15 + (idx * 18)
            painter.setPen(Qt.NoPen)
            painter.setBrush(col)
            painter.drawRect(lx + 10, iy, 10, 10)
            painter.setPen(Qt.white)
            painter.drawText(lx + 25, iy + 10, txt)

        # --- 5. Chart Header ---
        painter.setPen(Qt.white)
        painter.setFont(self.font_main)
        painter.drawText(20, 30, f"{self.symbol} (Daily)")

        # --- 6. Crosshairs (Snap to Bar Center and Close Price) ---
        if self.mouse_point and self.df is not None:
            x_raw = self.mouse_point.x()
            if self.padding_left <= x_raw <= self.width() - self.padding_right:
                bw = (self.width() - self.padding_left - self.padding_right) / self.visible_bars
                rel_idx = int((x_raw - self.padding_left) / bw)
                end_i = len(self.df) - self.scroll_offset
                start_i = max(0, end_i - self.visible_bars)
                act_idx = start_i + rel_idx
                
                if 0 <= act_idx < len(self.df):
                    # Snap vertical line to bar center
                    snap_x = self.padding_left + (rel_idx + 0.5) * bw
                    # Snap horizontal line to the bar's Close price
                    snap_y = price_to_y(self.df['Close'].iloc[act_idx])
                    
                    cross_pen = QPen(QColor(150, 150, 150), 1, Qt.DashLine)
                    painter.setPen(cross_pen)
                    # Vertical crosshair
                    painter.drawLine(QPointF(snap_x, self.padding_top), 
                                   QPointF(snap_x, self.height() - self.padding_bottom))
                    # Horizontal crosshair
                    painter.drawLine(QPointF(self.padding_left, snap_y), 
                                   QPointF(self.width() - self.padding_right, snap_y))

    def wheelEvent(self, event: QWheelEvent):
        """Handles zoom operations via the mouse wheel."""
        angle = event.angleDelta().y()
        if angle > 0:
            # Zoom In: Reduce number of visible bars
            self.visible_bars = max(20, int(self.visible_bars * 0.9))
        else:
            # Zoom Out: Increase number of visible bars
            limit = len(self.df) if self.df is not None else 500
            self.visible_bars = min(limit, int(self.visible_bars * 1.1))
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        """Initializes panning on left-click."""
        if event.button() == Qt.LeftButton:
            self.last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handles both crosshair movement and click-drag panning."""
        self.mouse_point = event.pos()
        self.update()
        
        # --- Update Status Bar Data via Signal ---
        if self.df is not None and not self.df.empty:
            x = event.pos().x()
            w_inner = self.width() - self.padding_left - self.padding_right
            if self.padding_left <= x <= self.width() - self.padding_right:
                bw = w_inner / self.visible_bars
                rel_idx = int((x - self.padding_left) / bw)
                end_i = len(self.df) - self.scroll_offset
                start_i = max(0, end_i - self.visible_bars)
                act_idx = start_i + rel_idx
                if 0 <= act_idx < len(self.df):
                    r = self.df.iloc[act_idx]
                    self.hovered_data_changed.emit({
                        'Date': self.df.index[act_idx].strftime('%Y-%m-%d'),
                        'Open': r['Open'], 'High': r['High'], 
                        'Low': r['Low'], 'Close': r['Close']
                    })
                else: self.hovered_data_changed.emit(None)
            else: self.hovered_data_changed.emit(None)

        # --- Handle Chart Panning ---
        if self.last_mouse_pos and self.df is not None:
            dx = event.pos().x() - self.last_mouse_pos.x()
            w_inner = self.width() - self.padding_left - self.padding_right
            # Calculate bars-per-pixel ratio
            bpp = self.visible_bars / w_inner
            shift = int(dx * bpp)
            if shift != 0:
                # Update scroll offset and reset last position to the current one
                self.scroll_offset = max(0, min(len(self.df) - self.visible_bars, 
                                              self.scroll_offset + shift))
                self.last_mouse_pos = event.pos()
                self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Clears panning state on mouse release."""
        if event.button() == Qt.LeftButton:
            self.last_mouse_pos = None

    def leaveEvent(self, event):
        """Clears crosshairs when the mouse leaves the widget."""
        self.mouse_point = None
        self.hovered_data_changed.emit(None)
        self.update()