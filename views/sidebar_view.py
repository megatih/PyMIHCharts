"""
Sidebar component for chart settings and indicator controls.
"""

from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import (QVBoxLayout, QWidget, QCheckBox, QFrame, 
                             QSizePolicy, QSpinBox, QComboBox, QLabel, QFormLayout, 
                             QApplication, QHBoxLayout, QToolButton)
from PySide6.QtCore import Qt, Signal
from models.enums import Interval, MAType, ChartType

class CollapsibleSection(QWidget):
    """A toggleable container for grouping related settings."""
    def __init__(self, title: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._is_expanded = True
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.header = QWidget()
        self.header.setCursor(Qt.PointingHandCursor)
        self.header_layout = QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(5, 5, 5, 5)

        self.toggle_btn = QToolButton()
        self.toggle_btn.setArrowType(Qt.DownArrow)
        self.toggle_btn.setFixedSize(20, 20)
        self.toggle_btn.setStyleSheet("border: none; background: transparent;")
        
        self.title_label = QLabel(title.upper())
        font = self.title_label.font()
        font.setBold(True)
        self.title_label.setFont(font)

        self.header_layout.addWidget(self.toggle_btn)
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(25, 5, 5, 10)

        self.main_layout.addWidget(self.header)
        self.main_layout.addWidget(self.content)
        self.header.mousePressEvent = lambda e: self.toggle()

    def toggle(self):
        self._is_expanded = not self._is_expanded
        self.content.setVisible(self._is_expanded)
        self.toggle_btn.setArrowType(Qt.DownArrow if self._is_expanded else Qt.RightArrow)

    def set_tooltips_enabled(self, enabled: bool):
        t = "Click to expand/collapse" if enabled else ""
        self.header.setToolTip(t)
        self.toggle_btn.setToolTip(t)

    def add_layout(self, layout): self.content_layout.addLayout(layout)
    def add_widget(self, widget): self.content_layout.addWidget(widget)
    def set_header_style(self, s): self.header.setStyleSheet(s)

class SidebarView(QFrame):
    """
    Control panel for technical analysis parameters.
    """
    interval_changed = Signal(str)
    chart_type_changed = Signal(str)
    setting_changed = Signal()
    font_settings_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMinimumWidth(280)
        self._tooltips = {}
        self._init_ui()
        self.set_tooltips_enabled(True)

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(1)

        # 1. Data Settings
        self.data_section = CollapsibleSection("Data Settings")
        self.interval_combo = QComboBox()
        for i in Interval:
            # Map enum name to a readable label
            label = i.name.replace("_", " ").title()
            self.interval_combo.addItem(label, i.value)
        self.interval_combo.setCurrentIndex(8) # Default: 1d
        self.interval_combo.currentIndexChanged.connect(lambda: self.interval_changed.emit(self.interval_combo.currentData()))
        
        ds_layout = QFormLayout()
        ds_layout.addRow("Interval:", self.interval_combo)
        self.data_section.add_layout(ds_layout)
        self.main_layout.addWidget(self.data_section)

        # 2. Chart Type
        self.chart_section = CollapsibleSection("Chart Type")
        self.chart_type_combo = QComboBox()
        for ct in ChartType:
            self.chart_type_combo.addItem(ct.value)
        self.chart_type_combo.currentTextChanged.connect(self.chart_type_changed.emit)
        self.chart_section.add_widget(self.chart_type_combo)
        self.main_layout.addWidget(self.chart_section)

        # 3. Indicators
        self.indicator_section = CollapsibleSection("Indicators")
        
        # TD Sequential
        self.td_label = self._create_header_label("TD SEQUENTIAL")
        self.td_checkbox = QCheckBox("Show TD Sequential")
        self.td_checkbox.setChecked(True)
        self.td_checkbox.stateChanged.connect(lambda s: self._toggle_td_settings(s))
        self.td_checkbox.stateChanged.connect(lambda: self.setting_changed.emit())
        
        self.td_container = QWidget()
        td_form = QFormLayout(self.td_container)
        td_form.setContentsMargins(0, 0, 0, 0)
        self.lookback_spin = self._create_spin(1, 20, 4)
        self.setup_spin = self._create_spin(2, 50, 9)
        self.countdown_spin = self._create_spin(2, 100, 13)
        td_form.addRow("Lookback:", self.lookback_spin)
        td_form.addRow("Setup:", self.setup_spin)
        td_form.addRow("Countdown:", self.countdown_spin)
        
        self.indicator_section.add_widget(self.td_label)
        self.indicator_section.add_widget(self.td_checkbox)
        self.indicator_section.add_widget(self.td_container)
        
        self.indicator_sep = QFrame()
        self.indicator_sep.setFrameShape(QFrame.HLine)
        self.indicator_section.add_widget(self.indicator_sep)

        # Bollinger Bands
        self.bb_label = self._create_header_label("BOLLINGER BANDS")
        self.bb_checkbox = QCheckBox("Show Bollinger Bands")
        self.bb_checkbox.stateChanged.connect(lambda s: self._toggle_bb_settings(s))
        self.bb_checkbox.stateChanged.connect(lambda: self.setting_changed.emit())
        
        self.bb_container = QWidget()
        self.bb_container.setVisible(False)
        bb_form = QFormLayout(self.bb_container)
        bb_form.setContentsMargins(0, 0, 0, 0)
        self.bb_period_spin = self._create_spin(1, 200, 20)
        self.bb_ma_type_combo = QComboBox()
        for ma in MAType: self.bb_ma_type_combo.addItem(ma.name, ma.value)
        self.bb_ma_type_combo.currentIndexChanged.connect(lambda: self.setting_changed.emit())
        
        self.bb_std_1_check = QCheckBox("1 SD")
        self.bb_std_2_check = QCheckBox("2 SD")
        self.bb_std_3_check = QCheckBox("3 SD")
        self.bb_std_2_check.setChecked(True)
        for cb in [self.bb_std_1_check, self.bb_std_2_check, self.bb_std_3_check]:
            cb.stateChanged.connect(lambda: self.setting_changed.emit())

        bb_form.addRow("Period:", self.bb_period_spin)
        bb_form.addRow("MA Type:", self.bb_ma_type_combo)
        std_box = QVBoxLayout()
        std_box.addWidget(self.bb_std_1_check); std_box.addWidget(self.bb_std_2_check); std_box.addWidget(self.bb_std_3_check)
        bb_form.addRow("Bands:", std_box)
        
        self.indicator_section.add_widget(self.bb_label)
        self.indicator_section.add_widget(self.bb_checkbox)
        self.indicator_section.add_widget(self.bb_container)
        self.main_layout.addWidget(self.indicator_section)

        # 4. Font Sizes
        self.font_section = CollapsibleSection("Font Sizes (Relative)")
        f_form = QFormLayout()
        self.base_font_spin = self._create_font_spin(6, 32, 13)
        self.header_offset_spin = self._create_font_spin(-10, 10, 2)
        self.labels_offset_spin = self._create_font_spin(-10, 10, -3)
        self.td_setup_offset_spin = self._create_font_spin(-10, 10, -3)
        self.td_countdown_offset_spin = self._create_font_spin(-10, 10, -3)
        
        f_form.addRow("Base Size:", self.base_font_spin)
        f_form.addRow("Header Off:", self.header_offset_spin)
        f_form.addRow("Labels Off:", self.labels_offset_spin)
        f_form.addRow("TD Setup Off:", self.td_setup_offset_spin)
        f_form.addRow("TD Count Off:", self.td_countdown_offset_spin)
        self.font_section.add_layout(f_form)
        self.main_layout.addWidget(self.font_section)

        self.main_layout.addStretch()

    def _create_header_label(self, text):
        lbl = QLabel(text)
        f = lbl.font(); f.setBold(True); f.setPointSize(f.pointSize()-1)
        lbl.setFont(f)
        return lbl

    def _create_spin(self, min_v, max_v, def_v):
        s = QSpinBox()
        s.setRange(min_v, max_v); s.setValue(def_v)
        s.valueChanged.connect(lambda: self.setting_changed.emit())
        return s

    def _create_font_spin(self, min_v, max_v, def_v):
        s = QSpinBox()
        s.setRange(min_v, max_v); s.setValue(def_v)
        s.valueChanged.connect(lambda: self.font_settings_changed.emit())
        return s

    def _toggle_td_settings(self, state):
        self.td_container.setVisible(state == Qt.Checked or state == 2)

    def _toggle_bb_settings(self, state):
        self.bb_container.setVisible(state == Qt.Checked or state == 2)

    def set_tooltips_enabled(self, enabled):
        for s in [self.data_section, self.chart_section, self.indicator_section, self.font_section]:
            s.set_tooltips_enabled(enabled)

    def apply_theme_styles(self, theme):
        self.setStyleSheet(f"SidebarView {{ background-color: {theme['widget_bg']}; color: {theme['text_main']}; border: none; }}")
        hs = f"QWidget {{ background-color: {theme['status_bg']}; color: {theme['status_text']}; border-bottom: 1px solid {theme['window_bg']}; }}"
        for s in [self.data_section, self.chart_section, self.indicator_section, self.font_section]:
            s.set_header_style(hs)
        if hasattr(self, 'indicator_sep'):
            self.indicator_sep.setStyleSheet(f"background-color: {theme['window_bg']}; max-height: 1px; border: none;")