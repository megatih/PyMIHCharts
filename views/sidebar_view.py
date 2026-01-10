"""
Sidebar component for chart settings and indicators.

This view provides a control panel for users to toggle indicators, 
switch chart types, and adjust technical parameters.
"""

from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import (QVBoxLayout, QWidget, QCheckBox, QFrame, 
                             QSizePolicy, QSpinBox, QComboBox, QLabel, QFormLayout, 
                             QApplication, QHBoxLayout, QToolButton, QScrollArea)
from PySide6.QtCore import Qt, Signal


class CollapsibleSection(QWidget):
    """
    A custom widget that provides a clickable header to toggle visibility of its content.
    Used to build the property browser style sidebar.
    """
    def __init__(self, title: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._is_expanded = True
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Header Widget
        self.header = QWidget()
        self.header.setCursor(Qt.PointingHandCursor)
        self.header_layout = QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(5, 5, 5, 5)
        self.header_layout.setSpacing(10)

        # Chevron Icon (using QToolButton for simple arrow handling)
        self.toggle_btn = QToolButton()
        self.toggle_btn.setStyleSheet("border: none; background: transparent;")
        self.toggle_btn.setArrowType(Qt.DownArrow)
        self.toggle_btn.setFixedSize(20, 20)
        
        # Title Label
        self.title_label = QLabel(title.upper())
        font = self.title_label.font()
        font.setBold(True)
        self.title_label.setFont(font)

        self.header_layout.addWidget(self.toggle_btn)
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()

        # Content Widget
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(25, 5, 5, 10) # Indent content
        self.content_layout.setSpacing(10)

        self.main_layout.addWidget(self.header)
        self.main_layout.addWidget(self.content)

        # Make header clickable
        self.header.mousePressEvent = self._on_header_clicked

    def _on_header_clicked(self, event):
        self.toggle()

    def toggle(self):
        self._is_expanded = not self._is_expanded
        self.content.setVisible(self._is_expanded)
        self.toggle_btn.setArrowType(Qt.DownArrow if self._is_expanded else Qt.RightArrow)

    def set_tooltips_enabled(self, enabled: bool):
        """Toggles tooltips for the header and toggle button."""
        if enabled:
            self.header.setToolTip("Click to expand or collapse this section")
            self.toggle_btn.setToolTip("Expand or collapse this section")
        else:
            self.header.setToolTip("")
            self.toggle_btn.setToolTip("")

    def add_widget(self, widget: QWidget):
        self.content_layout.addWidget(widget)

    def add_layout(self, layout: QVBoxLayout):
        self.content_layout.addLayout(layout)

    def set_header_style(self, style_str: str):
        self.header.setStyleSheet(style_str)


class SidebarView(QFrame):
    """
    View component containing control widgets for indicators and chart styling.
    
    Organized as a Property Browser with collapsible sections and a scroll area.
    """
    
    # Signals for the controller to handle application state changes
    interval_changed = Signal(str)
    chart_type_changed = Signal(str)
    td_toggle_changed = Signal(int)
    bb_toggle_changed = Signal(int)
    setting_changed = Signal()
    font_settings_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setFrameShape(QFrame.NoFrame)
        self.setMinimumWidth(250) # Ensure enough space for descriptive names
        
        self._tooltips = {}
        self._init_ui()
        self._define_tooltips()
        self.set_tooltips_enabled(True)

    def _define_tooltips(self):
        """Defines tooltip text for all sidebar components."""
        self._tooltips = {
            self.interval_combo: "Specify the time interval for historical data (e.g., 1m for minutes, 1d for daily). Changing this will trigger a reload.",
            self.chart_type_combo: "Select the visual representation of price data (Candlestick, OHLC, Line, or Heiken-Ashi).",
            self.td_label: "Tom DeMark Sequential: A technical indicator used to identify exhaustion in price trends.",
            self.td_checkbox: "Toggle Tom DeMark (TD) Sequential indicator display.",
            self.lookback_label: "Number of periods to look back for price flip calculation.",
            self.lookback_spin: "Number of periods to look back for price flip calculation.",
            self.setup_label: "Number of consecutive bars required for a completed TD Setup.",
            self.setup_spin: "Number of consecutive bars required for a completed TD Setup.",
            self.countdown_label: "Number of bars required for a completed TD Countdown.",
            self.countdown_spin: "Number of bars required for a completed TD Countdown.",
            self.bb_label: "Bollinger Bands: A volatility indicator consisting of a moving average and two standard deviation bands.",
            self.bb_checkbox: "Toggle Bollinger Bands indicator display.",
            self.bb_period_label: "Number of periods used for Moving Average and Standard Deviation calculations.",
            self.bb_period_spin: "Number of periods used for Moving Average and Standard Deviation calculations.",
            self.bb_ma_type_label: "Type of Moving Average (Simple or Exponential) for the center band.",
            self.bb_ma_type_combo: "Type of Moving Average (Simple or Exponential) for the center band.",
            self.bb_bands_label: "Select which standard deviation bands to display.",
            self.bb_std_1_check: "Show band at 1 standard deviation.",
            self.bb_std_2_check: "Show band at 2 standard deviations.",
            self.bb_std_3_check: "Show band at 3 standard deviations.",
            self.base_font_label: "Base font size for the entire application UI.",
            self.base_font_spin: "Base font size for the entire application UI.",
            self.header_offset_label: "Relative size adjustment for chart headers and titles.",
            self.header_offset_spin: "Relative size adjustment for chart headers and titles.",
            self.labels_offset_label: "Relative size adjustment for axis labels and timestamps.",
            self.labels_offset_spin: "Relative size adjustment for axis labels and timestamps.",
            self.td_setup_offset_label: "Relative size adjustment for TD Setup numbers.",
            self.td_setup_offset_spin: "Relative size adjustment for TD Setup numbers.",
            self.td_countdown_offset_label: "Relative size adjustment for TD Countdown numbers.",
            self.td_countdown_offset_spin: "Relative size adjustment for TD Countdown numbers."
        }

    def set_tooltips_enabled(self, enabled: bool):
        """Enables or disables tooltips for all components in the sidebar."""
        # Toggle section tooltips
        self.data_section.set_tooltips_enabled(enabled)
        self.chart_section.set_tooltips_enabled(enabled)
        self.indicator_section.set_tooltips_enabled(enabled)
        self.font_section.set_tooltips_enabled(enabled)

        # Toggle widget tooltips
        for widget, tooltip in self._tooltips.items():
            widget.setToolTip(tooltip if enabled else "")

    def _init_ui(self):
        """Builds the layout and initializes widgets."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Scroll Area to handle overflow
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(1) # Minimal spacing between sections

        # --- Section 0: Data Settings ---
        self.data_section = CollapsibleSection("Data Settings")
        
        self.interval_combo = QComboBox()
        self.interval_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        intervals = [
            ("1 Minute", "1m"), ("2 Minutes", "2m"), ("5 Minutes", "5m"),
            ("15 Minutes", "15m"), ("30 Minutes", "30m"), ("60 Minutes", "60m"),
            ("90 Minutes", "90m"), ("1 Hour", "1h"), ("1 Day", "1d"),
            ("5 Days", "5d"), ("1 Week", "1wk"), ("1 Month", "1mo"),
            ("3 Months", "3mo")
        ]
        for text, data in intervals:
            self.interval_combo.addItem(text, data)
            
        self.interval_combo.setCurrentIndex(8) # Default to 1 Day
        self.interval_combo.currentTextChanged.connect(lambda: self.interval_changed.emit(self.interval_combo.currentData()))
        
        self.data_settings_layout = QFormLayout()
        self.data_settings_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.data_settings_layout.addRow("Interval:", self.interval_combo)
        self.data_section.add_layout(self.data_settings_layout)
        self.layout.addWidget(self.data_section)
        
        # --- Section 1: Chart Type ---
        self.chart_section = CollapsibleSection("Chart Type")
        
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.chart_type_combo.addItems(["Candlestick", "OHLC", "Line", "Heiken-Ashi"])
        self.chart_type_combo.currentTextChanged.connect(self.chart_type_changed.emit)
        
        self.chart_section.add_widget(self.chart_type_combo)
        self.layout.addWidget(self.chart_section)
        
        # --- Section 2: Indicators ---
        self.indicator_section = CollapsibleSection("Indicators")
        
        # 1. TD Sequential Sub-section
        self.td_label = QLabel("TD SEQUENTIAL")
        font = self.td_label.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() - 1)
        self.td_label.setFont(font)
        self.indicator_section.add_widget(self.td_label)

        self.td_checkbox = QCheckBox("Show TD Sequential")
        self.td_checkbox.setChecked(True)
        self.td_checkbox.stateChanged.connect(self.td_toggle_changed.emit)
        self.indicator_section.add_widget(self.td_checkbox)
        
        self.td_settings_layout = QFormLayout()
        self.td_settings_layout.setLabelAlignment(Qt.AlignLeft)
        self.td_settings_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        self.lookback_spin = self._create_spin_setting(1, 20, 4)
        self.setup_spin = self._create_spin_setting(2, 50, 9)
        self.countdown_spin = self._create_spin_setting(2, 100, 13)
        
        self.lookback_label = QLabel("Lookback:")
        self.setup_label = QLabel("Setup:")
        self.countdown_label = QLabel("Countdown:")
        
        self.td_settings_layout.addRow(self.lookback_label, self.lookback_spin)
        self.td_settings_layout.addRow(self.setup_label, self.setup_spin)
        self.td_settings_layout.addRow(self.countdown_label, self.countdown_spin)
        self.indicator_section.add_layout(self.td_settings_layout)

        # Separator inside section
        self.indicator_sep = QFrame()
        self.indicator_sep.setFrameShape(QFrame.HLine)
        self.indicator_sep.setFrameShadow(QFrame.Sunken)
        self.indicator_section.add_widget(self.indicator_sep)

        # 2. Bollinger Bands Sub-section
        self.bb_label = QLabel("BOLLINGER BANDS")
        self.bb_label.setFont(font)
        self.indicator_section.add_widget(self.bb_label)

        self.bb_checkbox = QCheckBox("Show Bollinger Bands")
        self.bb_checkbox.setChecked(False)
        self.bb_checkbox.stateChanged.connect(self.bb_toggle_changed.emit)
        self.indicator_section.add_widget(self.bb_checkbox)

        self.bb_settings_layout = QFormLayout()
        self.bb_settings_layout.setLabelAlignment(Qt.AlignLeft)
        self.bb_settings_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        self.bb_period_spin = self._create_spin_setting(1, 200, 20)
        self.bb_ma_type_combo = QComboBox()
        self.bb_ma_type_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.bb_ma_type_combo.addItem("Simple Moving Average", "SMA")
        self.bb_ma_type_combo.addItem("Exponential Moving Average", "EMA")
        self.bb_ma_type_combo.currentTextChanged.connect(lambda: self.setting_changed.emit())
        
        self.bb_std_1_check = QCheckBox("1 SD")
        self.bb_std_2_check = QCheckBox("2 SD")
        self.bb_std_3_check = QCheckBox("3 SD")
        self.bb_std_2_check.setChecked(True)
        
        for cb in [self.bb_std_1_check, self.bb_std_2_check, self.bb_std_3_check]:
            cb.stateChanged.connect(lambda: self.setting_changed.emit())

        self.bb_period_label = QLabel("Period:")
        self.bb_ma_type_label = QLabel("MA Type:")
        self.bb_bands_label = QLabel("Bands:")

        self.bb_settings_layout.addRow(self.bb_period_label, self.bb_period_spin)
        self.bb_settings_layout.addRow(self.bb_ma_type_label, self.bb_ma_type_combo)
        
        std_layout = QVBoxLayout()
        std_layout.addWidget(self.bb_std_1_check)
        std_layout.addWidget(self.bb_std_2_check)
        std_layout.addWidget(self.bb_std_3_check)
        self.bb_settings_layout.addRow(self.bb_bands_label, std_layout)

        self.indicator_section.add_layout(self.bb_settings_layout)
        self.layout.addWidget(self.indicator_section)

        # --- Section 3: Font Sizes ---
        self.font_section = CollapsibleSection("Font Sizes (Relative)")

        self.font_settings_layout = QFormLayout()
        self.font_settings_layout.setLabelAlignment(Qt.AlignLeft)
        self.font_settings_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        base_font = QApplication.font()
        base_size = base_font.pointSize()
        if base_size <= 0: base_size = 13

        self.base_font_spin = self._create_font_spin(6, 32, base_size)
        self.header_offset_spin = self._create_font_spin(-10, 10, 2)
        self.labels_offset_spin = self._create_font_spin(-10, 10, -3)
        self.td_setup_offset_spin = self._create_font_spin(-10, 10, -3)
        self.td_countdown_offset_spin = self._create_font_spin(-10, 10, -3)

        self.base_font_label = QLabel("Base Size:")
        self.header_offset_label = QLabel("Header Offset:")
        self.labels_offset_label = QLabel("Labels Offset:")
        self.td_setup_offset_label = QLabel("TD Setup Off:")
        self.td_countdown_offset_label = QLabel("TD Count Off:")

        self.font_settings_layout.addRow(self.base_font_label, self.base_font_spin)
        self.font_settings_layout.addRow(self.header_offset_label, self.header_offset_spin)
        self.font_settings_layout.addRow(self.labels_offset_label, self.labels_offset_spin)
        self.font_settings_layout.addRow(self.td_setup_offset_label, self.td_setup_offset_spin)
        self.font_settings_layout.addRow(self.td_countdown_offset_label, self.td_countdown_offset_spin)

        self.font_section.add_layout(self.font_settings_layout)
        self.layout.addWidget(self.font_section)
        
        # Push all content to the top
        self.layout.addStretch()

        self.scroll_area.setWidget(self.container)
        self.main_layout.addWidget(self.scroll_area)

    def _create_spin_setting(self, min_v: int, max_v: int, default: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(min_v, max_v)
        spin.setValue(default)
        spin.valueChanged.connect(lambda: self.setting_changed.emit())
        return spin

    def _create_font_spin(self, min_v: int, max_v: int, default: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(min_v, max_v)
        spin.setValue(default)
        spin.valueChanged.connect(lambda: self.font_settings_changed.emit())
        return spin

    def apply_theme_styles(self, theme: Dict[str, str]):
        """Applies theme colors via QSS (Qt Style Sheets)."""
        self.setStyleSheet(f"background-color: {theme['widget_bg']}; color: {theme['text_main']}; border: none;")
        
        header_style = f"""
            QWidget {{ 
                background-color: {theme['status_bg']}; 
                color: {theme['status_text']};
                border-bottom: 1px solid {theme['window_bg']};
            }}
            QLabel {{ border: none; background: transparent; }}
            QToolButton {{ border: none; background: transparent; color: {theme['status_text']}; }}
        """
        self.data_section.set_header_style(header_style)
        self.chart_section.set_header_style(header_style)
        self.indicator_section.set_header_style(header_style)
        self.font_section.set_header_style(header_style)

        if hasattr(self, 'indicator_sep'):
            self.indicator_sep.setStyleSheet(f"background-color: {theme['window_bg']}; max-height: 1px; border: none;")