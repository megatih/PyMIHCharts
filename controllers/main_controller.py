"""
Main controller coordinating Model and View with async support.

This class implements the 'Controller' in the MVC pattern, handling
user interactions from the View and requesting data/processing from the Model.
"""

from typing import Optional, Dict, Any, List
import pandas as pd
from PySide6.QtWidgets import QMessageBox, QApplication
from PySide6.QtCore import Qt, QObject, Slot

from models.data_manager import DataManager
from models.indicators import calculate_indicators
from models.recent_symbols import RecentSymbolsManager
from views.main_view import MainView
from views.search_dialog import SymbolSearchDialog
from views.themes import THEMES


class MainController(QObject):
    """
    Orchestrator for the PyMIHCharts application.
    
    Responsibilities:
    - Bridge View signals to Model requests.
    - Synchronize UI state (toggles, settings) with the rendering engine.
    - Manage asynchronous data loading and search workflows.
    """

    def __init__(self, model: DataManager, view: MainView):
        """
        Initializes the controller and sets up signal-slot connections.
        
        Args:
            model: The DataManager instance.
            view: The MainView (top-level window) instance.
        """
        super().__init__()
        self.model = model
        self.view = view
        self.last_symbol: Optional[str] = None
        self.recent_manager = RecentSymbolsManager()
        
        self._setup_connections()
        
        # Initial Application State
        self.change_theme("Default")
        self.on_font_settings_changed()
        self._refresh_recent_symbols_ui()
        
        # Initial data loading (does not count toward popularity)
        self.load_data("AAPL", is_manual=False)

    def _setup_connections(self):
        """Wires up view signals to controller slots."""
        
        # --- View -> Controller ---
        self.view.sidebar.interval_changed.connect(self.on_interval_changed)
        self.view.load_requested.connect(lambda s: self.load_data(s, is_manual=True))
        self.view.search_requested.connect(self.search_data)
        self.view.sidebar_toggled.connect(self.toggle_sidebar)
        self.view.tooltips_toggled.connect(self.view.sidebar.set_tooltips_enabled)
        self.view.theme_requested.connect(self.change_theme)
        
        # --- Sidebar Controls -> Controller ---
        self.view.sidebar.chart_type_changed.connect(self.view.chart.set_chart_type)
        self.view.sidebar.td_toggle_changed.connect(self.on_td_toggle)
        self.view.sidebar.bb_toggle_changed.connect(self.on_bb_toggle)
        self.view.sidebar.setting_changed.connect(self.refresh_chart)
        self.view.sidebar.font_settings_changed.connect(self.on_font_settings_changed)
        
        # --- Chart Interactions -> Controller ---
        self.view.chart.hovered_data_changed.connect(self.update_status_bar)

        # --- Model -> Controller (Background Thread Callbacks) ---
        self.model.data_ready.connect(self._on_data_ready)
        self.model.loading_error.connect(self._on_loading_error)
        self.model.search_results.connect(self._on_search_results)

    @Slot(str)
    def load_data(self, symbol: str, is_manual: bool = True):
        """
        Initiates a new data fetch for the given ticker.
        
        Args:
            symbol: Ticker symbol string.
            is_manual: Whether the load was triggered by user input (vs startup).
        """
        symbol = symbol.upper().strip()
        if not symbol:
            return

        self.last_symbol = symbol
        self.view.set_loading_state(True)
        
        if is_manual:
            self.recent_manager.increment_symbol(symbol)
            self._refresh_recent_symbols_ui()

        # Capture current sidebar settings to pass to the background calculation
        interval = self.view.sidebar.interval_combo.currentText()
        settings = self._get_current_settings()
        self.model.request_data(symbol, interval, settings)

    @Slot(str)
    def on_interval_changed(self, interval: str):
        """Automatically reloads data when the user selects a new interval."""
        if self.last_symbol:
            # Reload existing symbol with new interval (don't increment popularity)
            self.load_data(self.last_symbol, is_manual=False)

    def _refresh_recent_symbols_ui(self):
        """Updates the dropdown list in the view with the latest top symbols."""
        top_symbols = self.recent_manager.get_top_symbols(limit=20)
        self.view.update_symbol_list(top_symbols)

    def search_data(self, query: str):
        """
        Initiates a symbol search based on the user's query.
        
        Args:
            query: The search string (e.g. name or partial ticker).
        """
        query = query.strip()
        if not query:
            return

        self.last_symbol = query
        self.view.set_loading_state(True)
        self.view.load_action.setText("Searching...")
        self.model.search_symbol(query)

    def _get_current_settings(self) -> Dict[str, Any]:
        """
        Extracts all indicator parameters from UI widgets.
        
        Returns:
            Dictionary containing lookback periods, MA types, and band settings.
        """
        std_devs = []
        if self.view.sidebar.bb_std_1_check.isChecked(): std_devs.append(1.0)
        if self.view.sidebar.bb_std_2_check.isChecked(): std_devs.append(2.0)
        if self.view.sidebar.bb_std_3_check.isChecked(): std_devs.append(3.0)

        return {
            'td_lookback': self.view.sidebar.lookback_spin.value(),
            'td_setup_max': self.view.sidebar.setup_spin.value(),
            'td_countdown_max': self.view.sidebar.countdown_spin.value(),
            'bb_period': self.view.sidebar.bb_period_spin.value(),
            'bb_ma_type': self.view.sidebar.bb_ma_type_combo.currentText(),
            'bb_std_devs': std_devs
        }

    def refresh_chart(self):
        """
        Recalculates technical indicators on the already loaded raw data.
        Useful when settings (e.g. BB period) change but the ticker remains the same.
        """
        if self.model.raw_df is None:
            return

        settings = self._get_current_settings()

        # Recalculate indicators. For large datasets, this could be threaded,
        # but modern vectorized NumPy is efficient enough for local processing.
        processed_df = calculate_indicators(self.model.raw_df, settings)
        
        self._update_view_with_data(processed_df, self.model.metadata)

    def _on_data_ready(self, df: pd.DataFrame, metadata: Dict[str, str]):
        """Callback for when background data loading completes successfully."""
        self.view.set_loading_state(False)
        self._update_view_with_data(df, metadata)

    def _on_loading_error(self, message: str):
        """
        Callback for background thread failures.
        If a ticker isn't found, it automatically triggers a symbol search.
        """
        self.view.set_loading_state(False)
        
        if "No data found" in message and self.last_symbol:
            # Automatically fallback to search if ticker lookup fails
            self.search_data(self.last_symbol)
            return

        QMessageBox.critical(self.view, "Data Error", message)

    def _on_search_results(self, results: List[Dict[str, Any]]):
        """Displays similar symbol suggestions when a direct match fails."""
        self.view.set_loading_state(False)
        if not results:
             QMessageBox.critical(self.view, "Search Error", 
                                f"Symbol '{self.last_symbol}' not found and no similar symbols found.")
             return
             
        dialog = SymbolSearchDialog(self.view, results)
        if dialog.exec():
            # If user picks a suggestion, load it
            self.view.symbol_input.setCurrentText(dialog.selected_symbol)
            self.load_data(dialog.selected_symbol, is_manual=True)

    def _update_view_with_data(self, df: pd.DataFrame, metadata: Dict[str, str]):
        """
        Helper method to push a processed DataFrame to the rendering engine.
        Also synchronizes visibility states from the sidebar to the chart.
        """
        # Synchronize visibility state before the chart repaints
        self.view.chart.show_td_sequential = self.view.sidebar.td_checkbox.isChecked()
        self.view.chart.show_bollinger_bands = self.view.sidebar.bb_checkbox.isChecked()
        
        # Sync standard deviation bands to render
        std_devs = []
        if self.view.sidebar.bb_std_1_check.isChecked(): std_devs.append(1.0)
        if self.view.sidebar.bb_std_2_check.isChecked(): std_devs.append(2.0)
        if self.view.sidebar.bb_std_3_check.isChecked(): std_devs.append(3.0)
        self.view.chart.bb_std_devs = std_devs

        self.view.chart.set_data(
            df, 
            metadata.get('symbol', ''),
            metadata.get('full_name', ''),
            metadata.get('exchange', ''),
            metadata.get('currency', '')
        )

    def on_td_toggle(self, state: int):
        """Handles TD Sequential indicator checkbox changes."""
        is_checked = state == Qt.CheckState.Checked.value
        self.view.chart.set_show_td_sequential(is_checked)

    def on_bb_toggle(self, state: int):
        """Handles Bollinger Bands indicator checkbox changes."""
        is_checked = state == Qt.CheckState.Checked.value
        self.view.chart.show_bollinger_bands = is_checked
        # Recalculate to ensure bands are present in the current data slice
        self.refresh_chart()

    def on_font_settings_changed(self):
        """
        Synchronizes UI font changes with the rendering engine and global application state.
        """
        base_size = self.view.sidebar.base_font_spin.value()
        
        # 1. Update Global Application Font (Affects sidebar, menus, etc.)
        app_font = QApplication.font()
        app_font.setPointSize(base_size)
        QApplication.setFont(app_font)
        
        # 2. Update Specialized Chart Rendering Fonts
        font_settings = {
            'base_size': base_size,
            'header_offset': self.view.sidebar.header_offset_spin.value(),
            'labels_offset': self.view.sidebar.labels_offset_spin.value(),
            'td_setup_offset': self.view.sidebar.td_setup_offset_spin.value(),
            'td_countdown_offset': self.view.sidebar.td_countdown_offset_spin.value()
        }
        self.view.chart.update_font_settings(font_settings)

    def change_theme(self, theme_name: str):
        """Applies a predefined color scheme to the entire application."""
        if theme_name in THEMES:
            self.view.apply_theme_styles(THEMES[theme_name])

    def toggle_sidebar(self):
        """Shows or hides the sidebar panel to maximize chart area."""
        is_visible = self.view.sidebar.isVisible()
        self.view.sidebar.setVisible(not is_visible)
        self.view.toggle_action.setChecked(not is_visible)

    def update_status_bar(self, data: Optional[Dict[str, Any]]):
        """
        Formats and displays price data in the status bar's HTML label.
        
        Args:
            data: Dictionary containing 'Date', 'Open', 'High', 'Low', 'Close'.
        """
        if not data:
            self.view.update_status_bar("Hover over chart to see price data")
            return

        # Use colors from the status bar theme or fixed colors for OHLC clarity
        html = (
            f"<b>DATE:</b> <span style='color: #ffffff;'>{data['Date']}</span> | "
            f"<b>O:</b> <span style='color: #ffaa00;'>{data['Open']:.2f}</span> | "
            f"<b>H:</b> <span style='color: #00ff00;'>{data['High']:.2f}</span> | "
            f"<b>L:</b> <span style='color: #ff5555;'>{data['Low']:.2f}</span> | "
            f"<b>C:</b> <span style='color: #00ccff;'>{data['Close']:.2f}</span>"
        )
        self.view.update_status_bar(html)
