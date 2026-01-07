"""
Main entry point for the PyMIHCharts application.

This module initializes the PySide6 application, sets up the main window,
and coordinates data flow between the yfinance data source, the
TD Sequential model, and the native rendering view.
"""

import sys
from typing import Optional, Dict, Any

import yfinance as yf
import pandas as pd
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLineEdit, QPushButton, QLabel, QMessageBox,
                             QCheckBox, QFrame, QSizePolicy, QSpinBox, QComboBox)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from td_sequential import calculate_td_sequential
from native_chart import CandlestickChart
from themes import THEMES


class TDChartsApp(QMainWindow):
    """
    The main window controller for PyMIHCharts.

    Manages the lifecycle of the application, including:
    - UI layout and styling.
    - User input handling for ticker symbols.
    - Orchestrating data fetching and indicator calculation.
    - Synchronizing chart interactions with the status bar.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyMIHCharts - Native TD Sequential")
        self.resize(1200, 800)
        
        self.current_theme_name = "Default"
        self.raw_df: Optional[pd.DataFrame] = None
        self.asset_metadata: Dict[str, str] = {}

        # --- UI Construction ---
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)

        # 0. Menu Bar
        self.menu_bar = self.menuBar()
        self.view_menu = self.menu_bar.addMenu("View")
        self.theme_menu = self.view_menu.addMenu("Color Scheme")
        
        for theme_name in THEMES.keys():
            action = self.theme_menu.addAction(theme_name)
            action.triggered.connect(lambda checked=False, name=theme_name: self.change_theme(name))

        # 1. Header Control Panel (Ticker input and Load button)
        self.header_widget = QWidget()
        self.header_layout = QHBoxLayout(self.header_widget)
        
        # Sidebar toggle button
        self.sidebar_toggle_btn = QPushButton("☰")
        self.sidebar_toggle_btn.setToolTip("Toggle Side Panel")
        self.sidebar_toggle_btn.clicked.connect(self.toggle_sidebar)
        self.header_layout.addWidget(self.sidebar_toggle_btn)

        self.controls = QHBoxLayout()
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("Enter Ticker (e.g., AAPL, BTC-USD)")
        self.symbol_input.setText("AAPL")
        self.symbol_input.returnPressed.connect(self.load_data)
        
        self.load_button = QPushButton("Load Chart")
        self.load_button.clicked.connect(self.load_data)
        
        self.controls.addWidget(QLabel("Ticker:"))
        self.controls.addWidget(self.symbol_input)
        self.controls.addWidget(self.load_button)
        self.header_layout.addLayout(self.controls)
        
        self.main_layout.addWidget(self.header_widget)

        # 2. Content Area (Sidebar + Chart)
        self.content_area = QWidget()
        self.content_layout = QHBoxLayout(self.content_area)

        # The Native Chart Widget (Initialized before Sidebar for signal connections)
        self.chart = CandlestickChart()
        self.chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        
        # Chart Type Setting
        self.sidebar_layout.addWidget(QLabel("CHART TYPE"))
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["Candlestick", "OHLC", "Line", "Heiken-Ashi"])
        self.chart_type_combo.currentTextChanged.connect(self.chart.set_chart_type)
        self.sidebar_layout.addWidget(self.chart_type_combo)
        
        self.sidebar_layout.addSpacing(15)

        self.sidebar_label = QLabel("INDICATORS")
        self.sidebar_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        self.sidebar_layout.addWidget(self.sidebar_label)
        
        self.td_checkbox = QCheckBox("TD Sequential")
        self.td_checkbox.setChecked(True)
        self.td_checkbox.stateChanged.connect(self.on_td_toggle)
        self.sidebar_layout.addWidget(self.td_checkbox)
        
        # TD Settings Container
        self.td_settings_container = QWidget()
        self.td_settings_layout = QVBoxLayout(self.td_settings_container)
        self.td_settings_layout.setContentsMargins(10, 5, 0, 5)
        
        # Lookback Setting
        self.lookback_layout = QHBoxLayout()
        self.lookback_layout.addWidget(QLabel("Lookback:"))
        self.lookback_spin = QSpinBox()
        self.lookback_spin.setRange(1, 20)
        self.lookback_spin.setValue(4)
        self.lookback_spin.valueChanged.connect(self.refresh_chart)
        self.lookback_layout.addWidget(self.lookback_spin)
        self.td_settings_layout.addLayout(self.lookback_layout)
        
        # Setup Max Setting
        self.setup_layout = QHBoxLayout()
        self.setup_layout.addWidget(QLabel("Setup:"))
        self.setup_spin = QSpinBox()
        self.setup_spin.setRange(2, 50)
        self.setup_spin.setValue(9)
        self.setup_spin.valueChanged.connect(self.refresh_chart)
        self.setup_layout.addWidget(self.setup_spin)
        self.td_settings_layout.addLayout(self.setup_layout)
        
        # Countdown Max Setting
        self.countdown_layout = QHBoxLayout()
        self.countdown_layout.addWidget(QLabel("Countdown:"))
        self.countdown_spin = QSpinBox()
        self.countdown_spin.setRange(2, 100)
        self.countdown_spin.setValue(13)
        self.countdown_spin.valueChanged.connect(self.refresh_chart)
        self.countdown_layout.addWidget(self.countdown_spin)
        self.td_settings_layout.addLayout(self.countdown_layout)
        
        self.sidebar_layout.addWidget(self.td_settings_container)
        
        self.sidebar_layout.addStretch()
        self.content_layout.addWidget(self.sidebar)
        self.content_layout.addWidget(self.chart)

        # Sync initial state (Must happen after chart and td_settings_container are defined)
        self.on_td_toggle(self.td_checkbox.checkState().value)
        
        # Use stretch factors to give more space to the chart
        self.content_layout.setStretchFactor(self.sidebar, 0)
        self.content_layout.setStretchFactor(self.chart, 1)
        
        self.main_layout.addWidget(self.content_area)

        # 3. Status Bar (HTML-formatted for color-coded data)
        self.status_label = QLabel("Hover over chart to see price data")
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.main_layout.addWidget(self.status_label)

        # --- Signal Connections ---
        # Update status bar when user hovers over the chart
        self.chart.hovered_data_changed.connect(self.update_status_bar)

        # Apply initial theme
        self.change_theme("Default")

        # Initial data load
        self.load_data()

    def change_theme(self, theme_name: str):
        """Updates the application and chart colors to the selected theme."""
        self.current_theme_name = theme_name
        theme = THEMES[theme_name]
        
        # Update Window/Main Stylesheet
        self.setStyleSheet(f"QMainWindow {{ background-color: {theme['window_bg']}; color: {theme['text_main']}; }}")
        
        self.sidebar_toggle_btn.setStyleSheet(
            f"QPushButton {{ background-color: {theme['button_bg']}; color: {theme['text_main']}; border: none; font-size: 18px; }} "
            f"QPushButton:hover {{ background-color: {theme['button_hover']}; }}"
        )

        self.sidebar.setStyleSheet(
            f"QFrame {{ background-color: {theme['widget_bg']}; border-right: 1px solid {theme['grid']}; padding: 10px; }} "
            f"QLabel {{ color: {theme['text_main']}; border: none; font-weight: bold; }} "
            f"QCheckBox {{ color: {theme['text_main']}; }} "
            f"QSpinBox, QComboBox {{ background-color: {theme['button_bg']}; color: {theme['text_main']}; border: 1px solid {theme['grid']}; }}"
        )

        self.symbol_input.setStyleSheet(
            f"background-color: {theme['widget_bg']}; color: {theme['text_main']}; "
            f"border: 1px solid {theme['grid']}; padding: 5px;"
        )
        
        self.load_button.setStyleSheet(
            f"QPushButton {{ background-color: {theme['button_bg']}; color: {theme['text_main']}; padding: 5px 15px; border: none; }} "
            f"QPushButton:hover {{ background-color: {theme['button_hover']}; }}"
        )
        
        self.status_label.setStyleSheet(
            f"background-color: {theme['status_bg']}; color: {theme['status_text']}; padding: 2px 10px; "
            "font-family: monospace; border-top: 1px solid #333;"
        )
        
        # Update Chart Widget
        self.chart.apply_theme(theme)

    def toggle_sidebar(self):
        """Shows or hides the left side panel."""
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def on_td_toggle(self, state: int):
        """Toggles the TD Sequential indicator on the chart."""
        is_checked = state == Qt.CheckState.Checked.value
        self.chart.set_show_td_sequential(is_checked)
        self.td_settings_container.setVisible(is_checked)
        self.td_settings_container.setEnabled(is_checked)

    def refresh_chart(self):
        """Recalculates indicators and refreshes the chart without re-downloading data."""
        if self.raw_df is not None:
            # Re-calculate indicators with current settings
            processed_df = calculate_td_sequential(
                self.raw_df,
                flip_lookback=self.lookback_spin.value(),
                setup_max=self.setup_spin.value(),
                countdown_max=self.countdown_spin.value()
            )
            # Update chart
            self.chart.set_data(
                processed_df, 
                self.asset_metadata.get('symbol', ''),
                self.asset_metadata.get('full_name', ''),
                self.asset_metadata.get('exchange', ''),
                self.asset_metadata.get('currency', '')
            )

    def update_status_bar(self, data: Optional[Dict[str, Any]]):
        """
        Updates the bottom status label with formatted OHLC data from the chart.

        Args:
            data: A dictionary containing 'Date', 'Open', 'High', 'Low', 'Close',
                  or None if the mouse is not over a valid bar.
        """
        if data:
            # Use HTML for rich formatting and color-coding prices
            status = (
                f"<b>DATE:</b> <span style='color: #ffffff;'>{data['Date']}</span> | "
                f"<b>O:</b> <span style='color: #ffaa00;'>{data['Open']:.2f}</span> | "
                f"<b>H:</b> <span style='color: #00ff00;'>{data['High']:.2f}</span> | "
                f"<b>L:</b> <span style='color: #ff5555;'>{data['Low']:.2f}</span> | "
                f"<b>C:</b> <span style='color: #00ccff;'>{data['Close']:.2f}</span>"
            )
            self.status_label.setText(status)
        else:
            self.status_label.setText("Hover over chart to see price data")

    def load_data(self):
        """
        Fetches historical data, calculates indicators, and updates the view.
        
        This method handles the high-level workflow of:
        1. Validating input.
        2. Fetching data via yfinance.
        3. Calculating TD Sequential values.
        4. Pushing data to the chart widget.
        """
        symbol = self.symbol_input.text().upper().strip()
        if not symbol:
            return

        # UI State Feedback
        self.load_button.setEnabled(False)
        self.load_button.setText("Loading...")
        # Force UI update to show "Loading..." state
        QApplication.processEvents()

        try:
            # 1. Download Historical Data
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="max", interval="1d")
            
            if df.empty:
                QMessageBox.warning(self, "Error", f"No data found for symbol: {symbol}")
                return

            # Fetch Metadata
            info = ticker.info
            self.asset_metadata = {
                'symbol': symbol,
                'full_name': info.get('longName', symbol),
                'exchange': info.get('exchange', 'Unknown Exchange'),
                'currency': info.get('currency', 'USD')
            }

            # 2. Data Cleaning: Flatten columns if they are MultiIndex (common with yfinance)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Store raw data for later re-calculations
            self.raw_df = df

            # 3. Model Logic: Calculate TD Sequential Indicators
            self.refresh_chart()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
        finally:
            # Restore UI State
            self.load_button.setEnabled(True)
            self.load_button.setText("Load Chart")


if __name__ == "__main__":
    # Standard PySide6 application startup
    app = QApplication(sys.argv)
    
    # Set application-wide font
    app.setFont(QFont("Segoe UI", 9))
    
    window = TDChartsApp()
    window.show()
    sys.exit(app.exec())
