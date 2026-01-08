"""
Native candlestick chart rendering engine using PySide6's QPainter.

This module provides a high-performance, interactive candlestick chart widget.
It uses native Qt drawing commands (QPainter) to achieve high frame rates and 
smooth interaction without the overhead of web-based charting libraries.
"""

import sys
import math
from typing import Optional, Dict, Any, List, Tuple

from PySide6.QtWidgets import QWidget, QPinchGesture, QGestureEvent, QApplication
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QMouseEvent, QWheelEvent, QFontMetrics
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QEvent, QSize
import pandas as pd
import numpy as np


class CandlestickChart(QWidget):
    """
    A custom QWidget for rendering interactive technical analysis charts.
    
    Features:
    - Interactive panning (drag) and zooming (scroll/pinch).
    - Multi-indicator support (TD Sequential, Bollinger Bands).
    - High-performance native rendering.
    - Hover crosshairs and OHLC data signaling.
    """

    # Signal emitted when the mouse hovers over a different price bar
    hovered_data_changed = Signal(object)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.df: Optional[pd.DataFrame] = None
        self.symbol: str = ""
        self.full_name: str = ""
        self.exchange: str = ""
        self.currency: str = ""
        
        # --- View State ---
        self.visible_bars: int = 150
        self.scroll_offset: int = 0
        self.show_td_sequential: bool = True
        self.show_bollinger_bands: bool = False
        self.bb_std_devs: List[float] = [2.0]
        self.chart_type: str = "Candlestick"

        # --- Interaction State ---
        self.last_mouse_pos: Optional[QPointF] = None
        self.mouse_point: Optional[QPointF] = None

        # --- Cached GDI / Font Objects ---
        # Initializing these here avoids repeated lookups during paintEvent
        base_font = QApplication.font()
        base_size = base_font.pointSize()
        if base_size <= 0: base_size = 13  # Fallback for systems using pixel sizes
        
        self.font_main = QFont(base_font)
        self.font_main.setPointSize(base_size + 2)
        self.font_main.setBold(True)
        
        # Axis and legend labels (Increased for better legibility)
        self.font_labels = QFont(base_font)
        self.font_labels.setPointSize(base_size - 3)
        
        self.font_year = QFont(base_font)
        self.font_year.setPointSize(base_size - 3)
        self.font_year.setBold(True)
        
        # TD Sequential Setup numbers (Keeping at 8pt)
        self.font_td_setup = QFont(base_font)
        self.font_td_setup.setPointSize(base_size - 5)
        
        # TD Sequential Countdown numbers (Keeping at 10pt)
        self.font_countdown = QFont(base_font)
        self.font_countdown.setPointSize(base_size - 3)
        self.font_countdown.setBold(True)
        
        self.fm_main = QFontMetrics(self.font_main)
        self.fm_labels = QFontMetrics(self.font_labels)
        
        # Default Theme Colors
        self.pen_grid = QPen(QColor(60, 60, 60), 1)
        self.color_bg = QColor(30, 30, 30)
        self.color_bull = QColor(0, 200, 0)
        self.color_bear = QColor(200, 0, 0)
        self.color_setup_buy = QColor(0, 255, 0)
        self.color_setup_sell = QColor(255, 50, 50)
        self.color_cd_buy = QColor(0, 255, 255)
        self.color_cd_sell = QColor(255, 255, 0)
        self.color_perfected = QColor(255, 0, 255)
        self.color_text_main = Qt.white
        self.color_text_label = Qt.gray
        self.color_crosshair = QColor(150, 150, 150)
        self.color_widget_bg = QColor(45, 45, 45)
        self.color_bb_mid = QColor(255, 170, 0)
        self.color_bb_upper = QColor(0, 170, 255)
        self.color_bb_lower = QColor(255, 0, 170)

        self._update_margins()

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.grabGesture(Qt.GestureType.PinchGesture)

    def _get_margins(self) -> Tuple[int, int, int, int]:
        """
        Calculates dynamic margins for axis labels based on current font metrics.
        Returns (left, right, top, bottom).
        """
        padding_bottom = self.fm_labels.height() + 10
        padding_right = self.fm_labels.horizontalAdvance("00000.00") + 10
        padding_top = self.fm_main.height() + (self.fm_labels.height() if self.show_td_sequential else 0) + 30
        padding_left = 10
        return padding_left, padding_right, padding_top, padding_bottom

    def _update_margins(self):
        """Internal helper to refresh padding attributes."""
        self.padding_left, self.padding_right, self.padding_top, self.padding_bottom = self._get_margins()

    def sizeHint(self) -> QSize:
        """Suggests a default size for layout managers."""
        return QSize(800, 600)

    def apply_theme(self, theme: Dict[str, str]):
        """Updates internal color state and triggers a repaint."""
        self.color_bg = QColor(theme["chart_bg"])
        self.color_widget_bg = QColor(theme["widget_bg"])
        self.pen_grid = QPen(QColor(theme["grid"]), 1)
        self.color_bull = QColor(theme["bull"])
        self.color_bear = QColor(theme["bear"])
        self.color_setup_buy = QColor(theme["setup_buy"])
        self.color_setup_sell = QColor(theme["setup_sell"])
        self.color_cd_buy = QColor(theme["cd_buy"])
        self.color_cd_sell = QColor(theme["cd_sell"])
        self.color_perfected = QColor(theme["perfected"])
        self.color_text_main = QColor(theme["text_main"])
        self.color_text_label = QColor(theme["text_label"])
        self.color_crosshair = QColor(theme["crosshair"])
        self.color_bb_mid = QColor(theme.get("bb_mid", "#ffaa00"))
        self.color_bb_upper = QColor(theme.get("bb_upper", "#00aaff"))
        self.color_bb_lower = QColor(theme.get("bb_lower", "#ff00aa"))
        self.update()

    def event(self, event: QEvent):
        """Overridden event handler to support gestures."""
        if event.type() == QEvent.Gesture:
            return self.gestureEvent(event)
        return super().event(event)

    def gestureEvent(self, event: QGestureEvent):
        """Dispatches gesture events to specific handlers."""
        if gesture := event.gesture(Qt.GestureType.PinchGesture):
            self.pinchTriggered(gesture)
        return True

    def pinchTriggered(self, gesture: QPinchGesture):
        """Handles pinch-to-zoom logic on touchscreens or trackpads."""
        factor = gesture.scaleFactor()
        if factor != 1.0 and self.df is not None:
            new_visible = int(self.visible_bars / factor)
            self.visible_bars = max(20, min(len(self.df), new_visible))
            self.update()

    def set_show_td_sequential(self, show: bool):
        """Toggles rendering of TD Sequential markers."""
        self.show_td_sequential = show
        self.update()

    def set_chart_type(self, chart_type: str):
        """Switches between Candlestick, OHLC, Line, and Heiken-Ashi."""
        self.chart_type = chart_type
        self.update()

    def set_data(self, df: pd.DataFrame, symbol: str, full_name: str = "", exchange: str = "", currency: str = ""):
        """
        Populates the chart with new price data.
        
        Args:
            df: DataFrame containing price and indicator data.
            symbol: Ticker symbol.
            full_name: Descriptive name of the security.
            exchange: Market exchange name.
            currency: Trading currency.
        """
        self.df = df
        self.symbol = symbol
        self.full_name = full_name
        self.exchange = exchange
        self.currency = currency
        self.scroll_offset = 0
        if df is not None and not df.empty:
            self.visible_bars = min(150, len(df))
        self.update()

    def paintEvent(self, event):
        """Main rendering loop called by the Qt event system."""
        self._update_margins()

        if self.df is None or self.df.empty:
            painter = QPainter(self)
            painter.setPen(Qt.white)
            painter.drawText(self.rect(), Qt.AlignCenter, "No Data Loaded")
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), self.color_bg)
        
        # 1. Identify which subset of the DataFrame is currently in the viewport
        visible_df, start_idx, end_idx = self._get_visible_data()
        if visible_df.empty:
            return

        # 2. Calculate dynamic price range for vertical scaling
        min_p, max_p = self._calculate_price_range(visible_df)
        p_range = max_p - min_p
        
        # 3. Draw Axis and Grid
        self._draw_price_axis(painter, min_p, max_p, p_range)
        self._draw_date_axis(painter, start_idx, end_idx, visible_df)

        # 4. Draw Indicators (background layers)
        if self.show_bollinger_bands:
            self._draw_bollinger_bands(painter, visible_df, min_p, p_range)

        # 5. Draw Primary Chart (Candles / Line)
        self._draw_main_chart(painter, visible_df, min_p, p_range)
        
        # 6. Draw Indicators (foreground overlays)
        if self.show_td_sequential:
            self._draw_td_indicators(painter, visible_df, min_p, p_range)
        
        self._draw_legend(painter)
        self._draw_header(painter)
        
        # 7. Draw Interaction Overlays
        if self.mouse_point:
            self._draw_crosshairs(painter, min_p, p_range)

    def _get_visible_data(self) -> Tuple[pd.DataFrame, int, int]:
        """Slices the DataFrame based on current scroll and zoom state."""
        total_len = len(self.df)
        end_idx = total_len - self.scroll_offset
        start_idx = max(0, end_idx - self.visible_bars)
        return self.df.iloc[start_idx:end_idx], start_idx, end_idx

    def _calculate_price_range(self, visible_df: pd.DataFrame) -> Tuple[float, float]:
        """Calculates min and max prices in the visible range to fit the chart vertically."""
        if self.chart_type == "Heiken-Ashi":
            min_p, max_p = visible_df['HA_Low'].min(), visible_df['HA_High'].max()
        elif self.chart_type == "Line":
            min_p, max_p = visible_df['Close'].min(), visible_df['Close'].max()
        else:
            min_p, max_p = visible_df['Low'].min(), visible_df['High'].max()
        
        # Expand range if Bollinger Bands are visible
        if self.show_bollinger_bands:
            for std in self.bb_std_devs:
                if f'bb_upper_{std}' in visible_df.columns:
                    max_p = max(max_p, visible_df[f'bb_upper_{std}'].max())
                if f'bb_lower_{std}' in visible_df.columns:
                    min_p = min(min_p, visible_df[f'bb_lower_{std}'].min())
            
        # Add 10% vertical buffer
        buf = (max_p - min_p) * 0.1 if max_p != min_p else 1.0
        return min_p - buf, max_p + buf

    def _price_to_y(self, price: float, min_p: float, p_range: float) -> float:
        """Maps a price value to a vertical pixel coordinate."""
        h = self.height() - self.padding_top - self.padding_bottom
        if p_range == 0:
            return self.padding_top + h / 2
        return self.padding_top + h - ((price - min_p) / p_range * h)

    def _draw_price_axis(self, painter: QPainter, min_p: float, max_p: float, p_range: float):
        """Renders vertical price labels and horizontal grid lines."""
        h = self.height() - self.padding_top - self.padding_bottom
        max_ticks = max(1, h // 50) # Target roughly one label every 50 pixels
        raw_inc = p_range / max_ticks if p_range > 0 else 1
        
        # Determine "nice" round numbers for ticks
        p10 = 10 ** math.floor(math.log10(raw_inc)) if raw_inc > 0 else 1
        nice_inc = min([p10, 2 * p10, 5 * p10, 10 * p10], key=lambda x: abs(x - raw_inc))
        precision = 0 if nice_inc >= 1 and nice_inc == int(nice_inc) else max(0, math.ceil(-math.log10(nice_inc)))

        painter.setFont(self.font_labels)
        curr_tick = math.ceil(min_p / nice_inc) * nice_inc
        while curr_tick <= max_p:
            y = self._price_to_y(curr_tick, min_p, p_range)
            painter.setPen(self.pen_grid)
            painter.drawLine(self.padding_left, int(y), self.width() - self.padding_right, int(y))
            painter.setPen(self.color_text_label)
            painter.drawText(self.width() - self.padding_right + 5, int(y + 5), f"{curr_tick:.{precision}f}")
            curr_tick += nice_inc

    def _draw_date_axis(self, painter: QPainter, start_idx: int, end_idx: int, visible_df: pd.DataFrame):
        """Renders horizontal date labels and vertical grid lines."""
        w = self.width() - self.padding_left - self.padding_right
        bar_w = w / self.visible_bars
        
        # Scan for year and month transitions to place labels
        last_year, last_month = -1, -1
        all_transitions = []
        for i, idx in enumerate(range(start_idx, end_idx)):
            d = self.df.index[idx]
            if d.year != last_year or d.month != last_month:
                all_transitions.append({'rel_idx': i, 'date': d, 'is_year': d.year != last_year})
                last_year, last_month = d.year, d.month

        # Adjust label density based on viewport width
        avg_px_per_month = w / len(all_transitions) if all_transitions else 100
        month_step = 1 if avg_px_per_month >= 60 else (2 if avg_px_per_month >= 30 else (3 if avg_px_per_month >= 20 else (6 if avg_px_per_month >= 10 else 12)))

        for trans in all_transitions:
            d = trans['date']
            x = self.padding_left + (trans['rel_idx'] + 0.5) * bar_w
            if trans['is_year'] or ((d.month - 1) % month_step == 0):
                painter.setPen(self.pen_grid)
                painter.drawLine(int(x), self.padding_top, int(x), self.height() - self.padding_bottom)
                painter.setPen(self.color_text_main if trans['is_year'] else self.color_text_label)
                painter.setFont(self.font_year if trans['is_year'] else self.font_labels)
                painter.drawText(int(x - 15), int(self.height() - self.padding_bottom + 15), d.strftime('%Y' if trans['is_year'] else '%b'))

    def _draw_bollinger_bands(self, painter: QPainter, visible_df: pd.DataFrame, min_p: float, p_range: float):
        """Renders Bollinger Band lines (Middle, Upper, Lower)."""
        w = self.width() - self.padding_left - self.padding_right
        bar_w = w / self.visible_bars
        
        # 1. Draw Middle Band (Baseline)
        if 'bb_middle' in visible_df.columns:
            painter.setPen(QPen(self.color_bb_mid, 1, Qt.DashLine))
            points = []
            for i in range(len(visible_df)):
                val = visible_df['bb_middle'].iloc[i]
                if not np.isnan(val):
                    points.append(QPointF(self.padding_left + (i + 0.5) * bar_w, self._price_to_y(val, min_p, p_range)))
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i+1])

        # 2. Draw standard deviation bands
        for std in self.bb_std_devs:
            upper_col, lower_col = f'bb_upper_{std}', f'bb_lower_{std}'
            
            # Draw Upper Band
            if upper_col in visible_df.columns:
                painter.setPen(QPen(self.color_bb_upper, 1))
                points = []
                for i in range(len(visible_df)):
                    val = visible_df[upper_col].iloc[i]
                    if not np.isnan(val):
                        points.append(QPointF(self.padding_left + (i + 0.5) * bar_w, self._price_to_y(val, min_p, p_range)))
                for i in range(len(points) - 1):
                    painter.drawLine(points[i], points[i+1])

            # Draw Lower Band
            if lower_col in visible_df.columns:
                painter.setPen(QPen(self.color_bb_lower, 1))
                points = []
                for i in range(len(visible_df)):
                    val = visible_df[lower_col].iloc[i]
                    if not np.isnan(val):
                        points.append(QPointF(self.padding_left + (i + 0.5) * bar_w, self._price_to_y(val, min_p, p_range)))
                for i in range(len(points) - 1):
                    painter.drawLine(points[i], points[i+1])

    def _draw_main_chart(self, painter: QPainter, visible_df: pd.DataFrame, min_p: float, p_range: float):
        """Renders the primary price representation (Candles, OHLC bars, or Line)."""
        w = self.width() - self.padding_left - self.padding_right
        bar_w = w / self.visible_bars
        
        is_ha = self.chart_type == "Heiken-Ashi"
        opens, highs, lows, closes = (visible_df['HA_'+c].values if is_ha else visible_df[c].values for c in ['Open', 'High', 'Low', 'Close'])

        if self.chart_type == "Line":
            painter.setPen(QPen(self.color_cd_buy, 2))
            points = [QPointF(self.padding_left + (i + 0.5) * bar_w, self._price_to_y(closes[i], min_p, p_range)) for i in range(len(visible_df))]
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i+1])
        else:
            for i in range(len(visible_df)):
                x = self.padding_left + (i + 0.5) * bar_w
                color = self.color_bull if closes[i] >= opens[i] else self.color_bear
                painter.setPen(QPen(color, 1))
                painter.setBrush(color)
                yh, yl, yo, yc = (self._price_to_y(v, min_p, p_range) for v in [highs[i], lows[i], opens[i], closes[i]])
                if self.chart_type == "OHLC":
                    painter.drawLine(QPointF(x, yh), QPointF(x, yl))
                    painter.drawLine(QPointF(x - bar_w * 0.3, yo), QPointF(x, yo))
                    painter.drawLine(QPointF(x, yc), QPointF(x + bar_w * 0.3, yc))
                else:
                    # Candlestick
                    painter.drawLine(QPointF(x, yh), QPointF(x, yl))
                    painter.drawRect(QRectF(x - bar_w * 0.35, min(yo, yc), bar_w * 0.7, max(1, abs(yo - yc))))

    def _draw_td_indicators(self, painter: QPainter, visible_df: pd.DataFrame, min_p: float, p_range: float):
        """Renders TD Sequential setup and countdown numbers."""
        w = self.width() - self.padding_left - self.padding_right
        bar_w = w / self.visible_bars
        scs, sts, perfs, ccs, cts = (visible_df[c].values for c in ['setup_count', 'setup_type', 'perfected', 'countdown_count', 'countdown_type'])
        rhs, rls = visible_df['High'].values, visible_df['Low'].values

        for i in range(len(visible_df)):
            x = self.padding_left + (i + 0.5) * bar_w
            yhr, ylr = self._price_to_y(rhs[i], min_p, p_range), self._price_to_y(rls[i], min_p, p_range)
            
            # Setup numbers (1-9)
            if scs[i] > 0:
                painter.setFont(self.font_td_setup)
                painter.setPen(self.color_perfected if perfs[i] else (self.color_setup_buy if sts[i] == 'buy' else self.color_setup_sell))
                painter.drawText(QRectF(x - 10, (ylr + 5 if sts[i] == 'buy' else yhr - 20), 20, 15), Qt.AlignCenter, str(scs[i]))
            
            # Countdown numbers (1-13)
            if ccs[i] > 0:
                painter.setFont(self.font_countdown)
                painter.setPen(self.color_cd_buy if cts[i] == 'buy' else self.color_cd_sell)
                painter.drawText(QRectF(x - 15, (ylr + 20 if cts[i] == 'buy' else yhr - 40), 30, 20), Qt.AlignCenter, "13+" if ccs[i] == 12.5 else str(int(ccs[i])))

    def _draw_header(self, painter: QPainter):
        """Renders ticker information at the top of the chart."""
        painter.setPen(self.color_text_main)
        painter.setFont(self.font_main)
        painter.drawText(20, 25, f"{self.full_name or self.symbol} ({self.symbol}) - {self.exchange} - {self.currency}")

    def _draw_legend(self, painter: QPainter):
        """Renders a dynamic legend identifying indicator colors."""
        lx, ly = 20, 35
        bg = QColor(self.color_widget_bg)
        bg.setAlpha(150)
        painter.setBrush(bg)
        painter.setPen(Qt.NoPen)
        
        legend_items = []
        if self.show_td_sequential:
            legend_items.extend([
                (self.color_setup_buy, "Buy Setup"),
                (self.color_setup_sell, "Sell Setup"),
                (self.color_perfected, "Perfected"),
                (self.color_cd_buy, "Buy Countdown"),
                (self.color_cd_sell, "Sell Countdown")
            ])
        
        if self.show_bollinger_bands:
            legend_items.extend([
                (self.color_bb_mid, "BB Mid"),
                (self.color_bb_upper, "BB Upper"),
                (self.color_bb_lower, "BB Lower")
            ])

        if not legend_items:
            return

        total_w = sum(painter.fontMetrics().horizontalAdvance(txt) + 45 for _, txt in legend_items)
        painter.drawRect(lx - 5, ly - 5, total_w + 10, 25)
        
        painter.setFont(self.font_labels)
        for col, txt in legend_items:
            painter.setBrush(col)
            painter.drawRect(lx, ly + 2, 10, 10)
            painter.setPen(self.color_text_main)
            painter.drawText(lx + 15, ly + 11, txt)
            lx += painter.fontMetrics().horizontalAdvance(txt) + 30

    def _draw_crosshairs(self, painter: QPainter, min_p: float, p_range: float):
        """Renders intersecting dashed lines following the mouse cursor."""
        x_raw = self.mouse_point.x()
        if self.padding_left <= x_raw <= self.width() - self.padding_right:
            bw = (self.width() - self.padding_left - self.padding_right) / self.visible_bars
            act_idx = max(0, len(self.df) - self.scroll_offset - self.visible_bars) + int((x_raw - self.padding_left) / bw)
            if 0 <= act_idx < len(self.df):
                sx = self.padding_left + (int((x_raw - self.padding_left) / bw) + 0.5) * bw
                # Snap horizontal line to the close price
                sy = self._price_to_y(self.df['HA_Close' if self.chart_type == "Heiken-Ashi" else 'Close'].iloc[act_idx], min_p, p_range)
                painter.setPen(QPen(self.color_crosshair, 1, Qt.DashLine))
                painter.drawLine(QPointF(sx, self.padding_top), QPointF(sx, self.height() - self.padding_bottom))
                painter.drawLine(QPointF(self.padding_left, sy), QPointF(self.width() - self.padding_right, sy))

    def wheelEvent(self, event: QWheelEvent):
        """Zoom in/out using the mouse wheel."""
        self.visible_bars = max(20, min(len(self.df) if self.df is not None else 500, int(self.visible_bars * (0.9 if event.angleDelta().y() > 0 else 1.1))))
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        """Capture starting point for drag-to-scroll interaction."""
        if event.button() == Qt.LeftButton: self.last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle panning (dragging) and crosshair updates."""
        self.mouse_point = event.pos()
        self.update()
        
        # Emit hovered data to the controller for the status bar
        if self.df is not None and not self.df.empty:
            inner_w = self.width() - self.padding_left - self.padding_right
            if self.padding_left <= event.pos().x() <= self.width() - self.padding_right:
                idx = max(0, len(self.df) - self.scroll_offset - self.visible_bars) + int((event.pos().x() - self.padding_left) / (inner_w / self.visible_bars))
                if 0 <= idx < len(self.df):
                    r = self.df.iloc[idx]
                    self.hovered_data_changed.emit({'Date': self.df.index[idx].strftime('%Y-%m-%d'), 'Open': r['Open'], 'High': r['High'], 'Low': r['Low'], 'Close': r['Close']})
                else: self.hovered_data_changed.emit(None)
            else: self.hovered_data_changed.emit(None)
        
        # Panning logic
        if self.last_mouse_pos and self.df is not None:
            shift = int((event.pos().x() - self.last_mouse_pos.x()) * (self.visible_bars / (self.width() - self.padding_left - self.padding_right)))
            if shift != 0:
                self.scroll_offset = max(0, min(len(self.df) - self.visible_bars, self.scroll_offset + shift))
                self.last_mouse_pos = event.pos()
                self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Terminate the drag interaction."""
        if event.button() == Qt.LeftButton: self.last_mouse_pos = None

    def leaveEvent(self, event: QEvent):
        """Clear overlays when the mouse leaves the widget."""
        self.mouse_point = None
        self.hovered_data_changed.emit(None)
        self.update()