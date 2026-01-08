"""
Sidebar component for chart settings and indicators.
"""

from PySide6.QtWidgets import (QVBoxLayout, QWidget, QCheckBox, QFrame, 
                             QSizePolicy, QSpinBox, QComboBox, QLabel, QFormLayout)
from PySide6.QtCore import Qt, Signal


class SidebarView(QFrame):
    """
    View component containing chart controls and indicator settings.
    """
    # Signals for the controller
    chart_type_changed = Signal(str)
    td_toggle_changed = Signal(int)
    setting_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setFrameShape(QFrame.NoFrame)
        self._init_ui()

    def _init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(15)
        
        # Chart Type Section
        chart_group = QWidget()
        chart_layout = QVBoxLayout(chart_group)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        chart_layout.setSpacing(5)
        
        lbl_chart = QLabel("CHART TYPE")
        font = lbl_chart.font()
        font.setBold(True)
        font.setPointSize(10)
        lbl_chart.setFont(font)
        
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["Candlestick", "OHLC", "Line", "Heiken-Ashi"])
        self.chart_type_combo.currentTextChanged.connect(self.chart_type_changed.emit)
        
        chart_layout.addWidget(lbl_chart)
        chart_layout.addWidget(self.chart_type_combo)
        self.layout.addWidget(chart_group)
        
        # Indicators Section
        indicator_group = QWidget()
        indicator_layout = QVBoxLayout(indicator_group)
        indicator_layout.setContentsMargins(0, 0, 0, 0)
        indicator_layout.setSpacing(5)
        
        lbl_ind = QLabel("INDICATORS")
        lbl_ind.setFont(font)
        
        self.td_checkbox = QCheckBox("TD Sequential")
        self.td_checkbox.setChecked(True)
        self.td_checkbox.stateChanged.connect(self.td_toggle_changed.emit)
        
        indicator_layout.addWidget(lbl_ind)
        indicator_layout.addWidget(self.td_checkbox)
        self.layout.addWidget(indicator_group)
        
        # TD Settings (Form Layout)
        self.td_settings_container = QWidget()
        self.td_settings_layout = QFormLayout(self.td_settings_container)
        self.td_settings_layout.setContentsMargins(0, 0, 0, 0)
        self.td_settings_layout.setLabelAlignment(Qt.AlignLeft)
        
        self.lookback_spin = self._create_spin_setting(1, 20, 4)
        self.setup_spin = self._create_spin_setting(2, 50, 9)
        self.countdown_spin = self._create_spin_setting(2, 100, 13)
        
        self.td_settings_layout.addRow("Lookback:", self.lookback_spin)
        self.td_settings_layout.addRow("Setup:", self.setup_spin)
        self.td_settings_layout.addRow("Countdown:", self.countdown_spin)
        
        self.layout.addWidget(self.td_settings_container)
        self.layout.addStretch()

    def _create_spin_setting(self, min_v: int, max_v: int, default: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(min_v, max_v)
        spin.setValue(default)
        spin.valueChanged.connect(lambda: self.setting_changed.emit())
        return spin

    def set_td_settings_visible(self, visible: bool):
        self.td_settings_container.setVisible(visible)
        self.td_settings_container.setEnabled(visible)

    def apply_theme_styles(self, theme: dict):
        # We will move towards Palette-based styling in the main controller,
        # but for now we keep minimal styling to respect the existing theme system
        # without overriding native shapes excessively.
        self.setStyleSheet(f"background-color: {theme['widget_bg']}; color: {theme['text_main']};")
