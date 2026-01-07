"""
Main controller coordinating Model and View.
"""

from typing import Optional, Dict, Any
import pandas as pd
from PySide6.QtWidgets import QMessageBox, QApplication
from PySide6.QtCore import Qt

from models.data_manager import DataManager
from models.indicators import calculate_td_sequential
from views.main_view import MainView
from views.themes import THEMES


class MainController:
    """
    Controller that connects the DataManager (Model) with the MainView (View).
    """

    def __init__(self, model: DataManager, view: MainView):
        self.model = model
        self.view = view
        self._setup_connections()
        
        # Initial State
        self.change_theme("Default")
        self.load_data("AAPL")

    def _setup_connections(self):
        """Wires up view signals to controller slots."""
        self.view.load_requested.connect(self.load_data)
        self.view.sidebar_toggled.connect(self.toggle_sidebar)
        self.view.theme_requested.connect(self.change_theme)
        
        # Sidebar specific connections
        self.view.sidebar.chart_type_changed.connect(self.view.chart.set_chart_type)
        self.view.sidebar.td_toggle_changed.connect(self.on_td_toggle)
        self.view.sidebar.setting_changed.connect(self.refresh_chart)
        
        # Chart specific connections
        self.view.chart.hovered_data_changed.connect(self.update_status_bar)

    def load_data(self, symbol: str):
        """Handles the workflow of downloading data and updating the UI."""
        symbol = symbol.upper().strip()
        if not symbol:
            return

        self.view.set_loading_state(True)
        QApplication.processEvents()

        try:
            df, metadata = self.model.fetch_data(symbol)
            if df is None:
                QMessageBox.warning(self.view, "Error", f"No data found for symbol: {symbol}")
                return

            self.refresh_chart()
            
        except Exception as e:
            QMessageBox.critical(self.view, "Error", f"An error occurred: {str(e)}")
        finally:
            self.view.set_loading_state(False)

    def refresh_chart(self):
        """Recalculates indicators based on current sidebar settings and updates the chart."""
        raw_df = self.model.raw_df
        if raw_df is None:
            return

        # Get settings from sidebar
        lookback = self.view.sidebar.lookback_spin.value()
        setup_max = self.view.sidebar.setup_spin.value()
        countdown_max = self.view.sidebar.countdown_spin.value()

        processed_df = calculate_td_sequential(
            raw_df,
            flip_lookback=lookback,
            setup_max=setup_max,
            countdown_max=countdown_max
        )
        
        metadata = self.model.metadata
        self.view.chart.set_data(
            processed_df, 
            metadata.get('symbol', ''),
            metadata.get('full_name', ''),
            metadata.get('exchange', ''),
            metadata.get('currency', '')
        )

    def on_td_toggle(self, state: int):
        """Toggles indicator visibility and UI settings."""
        is_checked = state == Qt.CheckState.Checked.value
        self.view.chart.set_show_td_sequential(is_checked)
        self.view.sidebar.set_td_settings_visible(is_checked)

    def change_theme(self, theme_name: str):
        """Updates colors across all views."""
        if theme_name in THEMES:
            self.view.apply_theme_styles(THEMES[theme_name])

    def toggle_sidebar(self):
        """Toggles visibility of the settings panel."""
        is_visible = self.view.sidebar.isVisible()
        self.view.sidebar.setVisible(not is_visible)

    def update_status_bar(self, data: Optional[Dict[str, Any]]):
        """Formats and displays OHLC data in the status bar."""
        if not data:
            self.view.update_status_bar("Hover over chart to see price data")
            return

        html = (
            f"<b>DATE:</b> <span style='color: #ffffff;'>{data['Date']}</span> | "
            f"<b>O:</b> <span style='color: #ffaa00;'>{data['Open']:.2f}</span> | "
            f"<b>H:</b> <span style='color: #00ff00;'>{data['High']:.2f}</span> | "
            f"<b>L:</b> <span style='color: #ff5555;'>{data['Low']:.2f}</span> | "
            f"<b>C:</b> <span style='color: #00ccff;'>{data['Close']:.2f}</span>"
        )
        self.view.update_status_bar(html)
