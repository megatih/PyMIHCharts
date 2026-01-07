"""
Sidebar component for chart settings and indicators.
"""

from PySide6.QtWidgets import (QVBoxLayout, QWidget, QCheckBox, QFrame, 
                             QSizePolicy, QSpinBox, QComboBox, QLabel, QHBoxLayout)
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
        self._init_ui()

    def _init_ui(self):
        self.layout = QVBoxLayout(self)
        
        # Chart Type
        self.layout.addWidget(QLabel("CHART TYPE"))
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["Candlestick", "OHLC", "Line", "Heiken-Ashi"])
        self.chart_type_combo.currentTextChanged.connect(self.chart_type_changed.emit)
        self.layout.addWidget(self.chart_type_combo)
        
        self.layout.addWidget(QLabel("INDICATORS"))
        
        self.td_checkbox = QCheckBox("TD Sequential")
        self.td_checkbox.setChecked(True)
        self.td_checkbox.stateChanged.connect(self.td_toggle_changed.emit)
        self.layout.addWidget(self.td_checkbox)
        
        # TD Settings
        self.td_settings_container = QWidget()
        self.td_settings_layout = QVBoxLayout(self.td_settings_container)
        
        self.lookback_spin = self._create_spin_setting("Lookback:", 1, 20, 4)
        self.setup_spin = self._create_spin_setting("Setup:", 2, 50, 9)
        self.countdown_spin = self._create_spin_setting("Countdown:", 2, 100, 13)
        
        self.layout.addWidget(self.td_settings_container)
        self.layout.addStretch()

    def _create_spin_setting(self, label: str, min_v: int, max_v: int, default: int) -> QSpinBox:
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label))
        spin = QSpinBox()
        spin.setRange(min_v, max_v)
        spin.setValue(default)
        spin.valueChanged.connect(lambda: self.setting_changed.emit())
        layout.addWidget(spin)
        self.td_settings_layout.addLayout(layout)
        return spin

    def set_td_settings_visible(self, visible: bool):
        self.td_settings_container.setVisible(visible)
        self.td_settings_container.setEnabled(visible)

    def apply_theme_styles(self, theme: dict):
        self.setStyleSheet(
            f"QFrame {{ background-color: {theme['widget_bg']}; border-right: 1px solid {theme['grid']}; padding: 10px; }} "
            f"QLabel {{ color: {theme['text_main']}; border: none; font-weight: bold; }} "
            f"QCheckBox {{ color: {theme['text_main']}; }} "
            f"QSpinBox, QComboBox {{ background-color: {theme['button_bg']}; color: {theme['text_main']}; border: 1px solid {theme['grid']}; }}"
        )
