"""
Master container for the multi-pane charting engine.
"""

from typing import Optional, Dict, Any, List, Tuple
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPinchGesture, QGestureEvent, QApplication
from PySide6.QtGui import QPainter, QColor, QMouseEvent, QWheelEvent
from PySide6.QtCore import Qt, QPointF, Signal, QEvent, QSize
import pandas as pd

from views.chart.price_pane import PricePane
from models.enums import ChartType

class CandlestickChart(QWidget):
    """
    The top-level chart widget that orchestrates multiple ChartPanes.
    
    Responsibilities:
    - Manage common state (zoom, scroll, data).
    - Dispatch input events (pan, zoom, mouse move) to children.
    - Synchronize layout of multiple panes (future-proofing for RSI/MACD).
    """

    hovered_data_changed = Signal(object)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.df: Optional[pd.DataFrame] = None
        
        # Shared State
        self.visible_bars = 150
        self.scroll_offset = 0
        self.last_mouse_pos: Optional[QPointF] = None
        
        # Child Panes
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)
        
        self.price_pane = PricePane()
        self.layout.addWidget(self.price_pane, stretch=1)
        
        # NOTE TO DEVELOPERS (Multi-Pane Logic):
        # To add a new sub-pane (e.g., RSI):
        # 1. Instantiate the new pane class (inheriting from ChartPane).
        # 2. Add it to this layout: self.layout.addWidget(rsi_pane, stretch=0).
        # 3. Ensure it is updated in set_data() and event handlers.

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.grabGesture(Qt.GestureType.PinchGesture)

    def set_data(self, df: pd.DataFrame, metadata: Dict[str, str]):
        """Propagates new data to all child panes."""
        self.df = df
        self.scroll_offset = 0
        if df is not None and not df.empty:
            self.visible_bars = min(150, len(df))
            
        self.price_pane.metadata = metadata
        self._sync_panes()

    def apply_theme(self, theme: Dict[str, str]):
        """Propagates theme to all child panes."""
        self.price_pane.apply_theme(theme)

    def update_font_settings(self, settings: Any):
        """Propagates font changes to child panes."""
        self.price_pane.update_fonts(settings)

    def _sync_panes(self):
        """Ensures all panes have the same scroll and zoom level."""
        self.price_pane.set_data(self.df, self.visible_bars, self.scroll_offset)

    # --- Interaction Logic (Coordinated across panes) ---

    def event(self, event: QEvent):
        if event.type() == QEvent.Gesture:
            if gesture := event.gesture(Qt.GestureType.PinchGesture):
                self._on_pinch(gesture)
                return True
        return super().event(event)

    def _on_pinch(self, gesture: QPinchGesture):
        factor = gesture.scaleFactor()
        if factor != 1.0 and self.df is not None:
            new_visible = int(self.visible_bars / factor)
            self.visible_bars = max(20, min(len(self.df), new_visible))
            self._sync_panes()

    def wheelEvent(self, event: QWheelEvent):
        if self.df is not None:
            self.visible_bars = max(20, min(len(self.df), int(self.visible_bars * (0.9 if event.angleDelta().y() > 0 else 1.1))))
            self._sync_panes()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton: 
            self.last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        # 1. Update Crosshairs for all panes
        self.price_pane.mouse_pos = event.pos()
        self.price_pane.update()
        
        # 2. Emit hovered data to controller
        self._emit_hover_data(event.pos())
        
        # 3. Panning Logic
        if self.last_mouse_pos and self.df is not None:
            # Use price_pane's mapper for coordinate logic
            mapper = self.price_pane.mapper
            inner_w = mapper.view_w - mapper.p_left - mapper.p_right
            if inner_w > 0:
                shift = int((event.pos().x() - self.last_mouse_pos.x()) * (self.visible_bars / inner_w))
                if shift != 0:
                    self.scroll_offset = max(0, min(len(self.df) - self.visible_bars, self.scroll_offset + shift))
                    self.last_mouse_pos = event.pos()
                    self._sync_panes()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton: 
            self.last_mouse_pos = None

    def leaveEvent(self, event: QEvent):
        self.price_pane.mouse_pos = None
        self.hovered_data_changed.emit(None)
        self.update()

    def _emit_hover_data(self, pos: QPointF):
        if self.df is None or self.df.empty: return
        mapper = self.price_pane.mapper
        if mapper.p_left <= pos.x() <= self.width() - mapper.p_right:
            idx_rel = int((pos.x() - mapper.p_left) / mapper.get_bar_width())
            idx_act = max(0, len(self.df) - self.scroll_offset - self.visible_bars) + idx_rel
            if 0 <= idx_act < len(self.df):
                r = self.df.iloc[idx_act]
                self.hovered_data_changed.emit({
                    'Date': self.df.index[idx_act].strftime('%Y-%m-%d'), 
                    'Open': r['Open'], 'High': r['High'], 'Low': r['Low'], 'Close': r['Close']
                })
                return
        self.hovered_data_changed.emit(None)

    def sizeHint(self) -> QSize:
        return QSize(800, 600)
