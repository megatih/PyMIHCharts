"""
Sidebar component for chart settings and indicators.

This view provides a control panel for users to toggle indicators, 
switch chart types, and adjust technical parameters.
"""

from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import (QVBoxLayout, QWidget, QCheckBox, QFrame, 
                             QSizePolicy, QSpinBox, QComboBox, QLabel, QFormLayout)
from PySide6.QtCore import Qt, Signal


class SidebarView(QFrame):
    """
    View component containing control widgets for indicators and chart styling.
    
    Emits signals to the controller whenever a user interaction requires 
    a data recalculation or a view update.
    """
    
    # Signals for the controller to handle application state changes
    chart_type_changed = Signal(str)
    td_toggle_changed = Signal(int)
    bb_toggle_changed = Signal(int)
    setting_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setFrameShape(QFrame.NoFrame)
        self._init_ui()

    def _init_ui(self):
        """Builds the layout and initializes widgets."""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(15)
        
        # --- Section: Chart Type ---
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
        
        # --- Section: Indicators ---
        indicator_group = QWidget()
        indicator_layout = QVBoxLayout(indicator_group)
        indicator_layout.setContentsMargins(0, 0, 0, 0)
        indicator_layout.setSpacing(5)
        
        lbl_ind = QLabel("INDICATORS")
        lbl_ind.setFont(font)
        indicator_layout.addWidget(lbl_ind)
        
        # 1. TD Sequential Indicator
        self.td_checkbox = QCheckBox("TD Sequential")
        self.td_checkbox.setChecked(True)
        self.td_checkbox.stateChanged.connect(self.td_toggle_changed.emit)
        indicator_layout.addWidget(self.td_checkbox)
        
        # 1a. TD Settings (Expandable)
        self.td_settings_container = QWidget()
        self.td_settings_layout = QFormLayout(self.td_settings_container)
        self.td_settings_layout.setContentsMargins(20, 0, 0, 5) # Indent settings
        self.td_settings_layout.setLabelAlignment(Qt.AlignLeft)
        
        self.lookback_spin = self._create_spin_setting(1, 20, 4)
        self.setup_spin = self._create_spin_setting(2, 50, 9)
        self.countdown_spin = self._create_spin_setting(2, 100, 13)
        
        self.td_settings_layout.addRow("Lookback:", self.lookback_spin)
        self.td_settings_layout.addRow("Setup:", self.setup_spin)
        self.td_settings_layout.addRow("Countdown:", self.countdown_spin)
        indicator_layout.addWidget(self.td_settings_container)

        # 2. Bollinger Bands Indicator
        self.bb_checkbox = QCheckBox("Bollinger Bands")
        self.bb_checkbox.setChecked(False)
        self.bb_checkbox.stateChanged.connect(self.bb_toggle_changed.emit)
        indicator_layout.addWidget(self.bb_checkbox)

        # 2a. BB Settings (Expandable)
        self.bb_settings_container = QWidget()
        self.bb_settings_container.setVisible(False) # Hidden until enabled
        self.bb_settings_layout = QFormLayout(self.bb_settings_container)
        self.bb_settings_layout.setContentsMargins(20, 0, 0, 5) # Indent settings
        self.bb_settings_layout.setLabelAlignment(Qt.AlignLeft)

        self.bb_period_spin = self._create_spin_setting(1, 200, 20)
        self.bb_ma_type_combo = QComboBox()
        self.bb_ma_type_combo.addItems(["SMA", "EMA"])
        self.bb_ma_type_combo.currentTextChanged.connect(lambda: self.setting_changed.emit())
        
        # Standard Deviation Toggles
        self.bb_std_1_check = QCheckBox("1 SD")
        self.bb_std_2_check = QCheckBox("2 SD")
        self.bb_std_3_check = QCheckBox("3 SD")
        self.bb_std_2_check.setChecked(True) # Standard default
        
        for cb in [self.bb_std_1_check, self.bb_std_2_check, self.bb_std_3_check]:
            cb.stateChanged.connect(lambda: self.setting_changed.emit())

        self.bb_settings_layout.addRow("Period:", self.bb_period_spin)
        self.bb_settings_layout.addRow("MA Type:", self.bb_ma_type_combo)
        
        # Group Standard Deviation checkboxes in a vertical layout for the form
        std_layout = QVBoxLayout()
        std_layout.addWidget(self.bb_std_1_check)
        std_layout.addWidget(self.bb_std_2_check)
        std_layout.addWidget(self.bb_std_3_check)
        self.bb_settings_layout.addRow("Bands:", std_layout)

        indicator_layout.addWidget(self.bb_settings_container)
        
        self.layout.addWidget(indicator_group)
        
        # Push all content to the top
        self.layout.addStretch()

    def _create_spin_setting(self, min_v: int, max_v: int, default: int) -> QSpinBox:
        """Helper to create a QSpinBox that notifies the controller on value change."""
        spin = QSpinBox()
        spin.setRange(min_v, max_v)
        spin.setValue(default)
        spin.valueChanged.connect(lambda: self.setting_changed.emit())
        return spin

    def set_td_settings_visible(self, visible: bool):
        """Shows or hides the TD Sequential configuration panel."""
        self.td_settings_container.setVisible(visible)
        self.td_settings_container.setEnabled(visible)

    def set_bb_settings_visible(self, visible: bool):
        """Shows or hides the Bollinger Bands configuration panel."""
        self.bb_settings_container.setVisible(visible)
        self.bb_settings_container.setEnabled(visible)

    def apply_theme_styles(self, theme: Dict[str, str]):
        """Applies theme colors via QSS (Qt Style Sheets)."""
        self.setStyleSheet(f"background-color: {theme['widget_bg']}; color: {theme['text_main']};")