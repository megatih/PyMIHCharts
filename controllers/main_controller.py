"""
Main controller coordinating Model and View using AppState.
"""

from typing import Optional, List, Dict, Any
import pandas as pd
from PySide6.QtWidgets import QMessageBox, QApplication
from PySide6.QtCore import Qt, QObject, Slot

from models.data_manager import DataManager
from models.data_models import AppState, ChartData
from models.recent_symbols import RecentSymbolsManager
from models.enums import ChartType, Interval, MAType
from models.indicators.registry import IndicatorManager
from views.main_view import MainView
from views.search_dialog import SymbolSearchDialog
from views.themes import THEMES

class MainController(QObject):
    """
    The orchestrator that bridges UI intent to Model actions.
    """

    def __init__(self, model: DataManager, view: MainView):
        super().__init__()
        self.model = model
        self.view = view
        self.state = AppState()
        self.recent_manager = RecentSymbolsManager()
        self.indicator_manager = IndicatorManager()
        
        self._setup_connections()
        
        # Initial Bootstrapping
        self._apply_theme("Default")
        self._on_indicator_settings_changed()
        self._sync_font_settings()
        self._refresh_recent_symbols_ui()
        self._load_initial_data()

    def _setup_connections(self):
        # View -> Controller
        self.view.sidebar.interval_changed.connect(self._on_interval_changed)
        self.view.sidebar.chart_type_changed.connect(self._on_chart_type_changed)
        self.view.load_requested.connect(self._on_load_requested)
        self.view.search_requested.connect(self._on_search_requested)
        self.view.sidebar_toggled.connect(self._on_toggle_sidebar)
        self.view.theme_requested.connect(self._apply_theme)
        self.view.tooltips_toggled.connect(self._on_toggle_tooltips)
        
        # Sidebar Settings -> Controller
        self.view.sidebar.setting_changed.connect(self._on_indicator_settings_changed)
        self.view.sidebar.font_settings_changed.connect(self._on_font_settings_changed)

        # Model -> Controller
        self.model.data_ready.connect(self._on_data_ready)
        self.model.loading_error.connect(self._on_loading_error)
        self.model.search_results.connect(self._on_search_results)
        
        # Chart Interactions
        self.view.chart.hovered_data_changed.connect(self._on_chart_hover)

    def _load_initial_data(self):
        """Loads default ticker on startup."""
        self._on_load_requested("AAPL", is_manual=False)

    @Slot(str)
    def _on_load_requested(self, symbol: str, is_manual: bool = True):
        symbol = symbol.upper().strip()
        if not symbol: return

        self.state.symbol = symbol
        self.view.set_loading_state(True)
        
        if is_manual:
            self.recent_manager.increment_symbol(symbol)
            self._refresh_recent_symbols_ui()

        self.model.request_data(symbol, self.state)

    @Slot(str)
    def _on_interval_changed(self, interval_val: str):
        """Triggered when the interval combo box changes."""
        self.state.interval = Interval(interval_val)
        if self.state.symbol:
            self._on_load_requested(self.state.symbol, is_manual=False)

    @Slot(str)
    def _on_chart_type_changed(self, type_str: str):
        """Updates the rendering style of the main price pane."""
        self.state.chart_type = ChartType(type_str)
        self.view.chart.price_pane.chart_type = self.state.chart_type
        self.view.chart.price_pane.update()

    @Slot()
    def _on_indicator_settings_changed(self):
        """Updates AppState from UI and refreshes calculation if data exists."""
        # Sync UI -> State
        s = self.view.sidebar
        self.state.td_settings.visible = s.td_checkbox.isChecked()
        self.state.td_settings.lookback = s.lookback_spin.value()
        self.state.td_settings.setup_max = s.setup_spin.value()
        self.state.td_settings.countdown_max = s.countdown_spin.value()
        
        self.state.bb_settings.visible = s.bb_checkbox.isChecked()
        self.state.bb_settings.period = s.bb_period_spin.value()
        self.state.bb_settings.ma_type = MAType(s.bb_ma_type_combo.currentData())
        
        stds = []
        if s.bb_std_1_check.isChecked(): stds.append(1.0)
        if s.bb_std_2_check.isChecked(): stds.append(2.0)
        if s.bb_std_3_check.isChecked(): stds.append(3.0)
        self.state.bb_settings.std_devs = stds
        
        # Update View properties
        self.view.chart.price_pane.show_td = self.state.td_settings.visible
        self.view.chart.price_pane.show_bb = self.state.bb_settings.visible
        self.view.chart.price_pane.bb_std_devs = stds
        self.view.chart.price_pane.td_settings = self.state.td_settings
        self.view.chart.price_pane.bb_settings = self.state.bb_settings
        
        # If we have raw data, recalculate indicators
        if self.model.current_data:
            raw_df = self.model.current_data.raw_df
            # Re-run pipeline on the original raw data
            processed_df = self.indicator_manager.calculate_all(raw_df.copy(), self.state)
            self.model.current_data.df = processed_df
            
            # Update the main chart container's data so hover emitting works
            self.view.chart.df = processed_df
            
            # Synchronize the new dataframe back to the panes
            self.view.chart.price_pane.set_data(
                processed_df, 
                self.view.chart.visible_bars, 
                self.view.chart.scroll_offset
            )

    @Slot()
    def _on_font_settings_changed(self):
        """Syncs font settings from UI to AppState and View."""
        s = self.view.sidebar
        self.state.font_settings.base_size = s.base_font_spin.value()
        self.state.font_settings.header_offset = s.header_offset_spin.value()
        self.state.font_settings.labels_offset = s.labels_offset_spin.value()
        self.state.font_settings.td_setup_offset = s.td_setup_offset_spin.value()
        self.state.font_settings.td_countdown_offset = s.td_countdown_offset_spin.value()
        
        self._sync_font_settings()

    def _sync_font_settings(self):
        # 1. App Font
        app_font = QApplication.font()
        app_font.setPointSize(self.state.font_settings.base_size)
        QApplication.setFont(app_font)
        
        # 2. View Internal Fonts
        self.view.chart.update_font_settings(self.state.font_settings)

    def _on_data_ready(self, chart_data: ChartData):
        self.view.set_loading_state(False)
        self.view.chart.set_data(chart_data.df, {
            'symbol': chart_data.metadata.symbol,
            'full_name': chart_data.metadata.full_name,
            'exchange': chart_data.metadata.exchange,
            'currency': chart_data.metadata.currency,
            'interval': self.state.interval.value
        })

    def _on_loading_error(self, msg: str):
        self.view.set_loading_state(False)
        if "No data found" in msg and self.state.symbol:
            self._on_search_requested(self.state.symbol)
        else:
            QMessageBox.critical(self.view, "Data Error", msg)

    def _on_search_requested(self, query: str):
        if not query.strip(): return
        self.view.set_loading_state(True)
        self.model.search_symbol(query)

    def _on_search_results(self, results: List[Dict]):
        self.view.set_loading_state(False)
        if not results:
            QMessageBox.information(self.view, "Search", "No symbols found.")
            return
        
        dialog = SymbolSearchDialog(self.view, results)
        if dialog.exec():
            self.view.symbol_input.setCurrentText(dialog.selected_symbol)
            self._on_load_requested(dialog.selected_symbol)

    def _on_chart_hover(self, data: Optional[Dict]):
        if not data:
            self.view.update_status_bar("Hover over chart to see price data")
            return
            
        theme = THEMES.get(self.state.theme_name, THEMES["Default"])
        
        # 1. Base OHLC
        html = (
            f"<span style='color: {theme['text_main']};'>{data['Date']}</span> | "
            f"O <span style='color: {theme['text_main']};'>{data['Open']:.2f}</span>  "
            f"H <span style='color: {theme['bull']};'>{data['High']:.2f}</span>  "
            f"L <span style='color: {theme['bear']};'>{data['Low']:.2f}</span>  "
            f"C <span style='color: {theme['bull'] if data['Close'] >= data['Open'] else theme['bear']};'>{data['Close']:.2f}</span>"
        )
        
        # 2. Bollinger Bands
        if self.state.bb_settings.visible:
            bb_parts = []
            mid_v = data.get('bb_middle')
            if mid_v is not None and not pd.isna(mid_v):
                bb_parts.append(f"M <span style='color: {theme['bb_mid']};'>{mid_v:.2f}</span>")
            
            for std in self.state.bb_settings.std_devs:
                up_v = data.get(f'bb_upper_{std}')
                lo_v = data.get(f'bb_lower_{std}')
                std_lbl = int(std) if std == int(std) else std
                
                if up_v is not None and not pd.isna(up_v):
                    bb_parts.append(f"U({std_lbl}) <span style='color: {theme['bb_upper']};'>{up_v:.2f}</span>")
                if lo_v is not None and not pd.isna(lo_v):
                    bb_parts.append(f"L({std_lbl}) <span style='color: {theme['bb_lower']};'>{lo_v:.2f}</span>")
            
            if bb_parts:
                html += f" | BB({self.state.bb_settings.period}) " + "  ".join(bb_parts)
                
        # 3. TD Sequential
        if self.state.td_settings.visible:
            td_parts = []
            sc, st = data.get('setup_count', 0), data.get('setup_type')
            if sc > 0:
                color = theme['setup_buy'] if st == 'buy' else theme['setup_sell']
                td_parts.append(f"S({'B' if st == 'buy' else 'S'}) <span style='color: {color};'>{int(sc)}</span>")
            
            cc, ct = data.get('countdown_count', 0), data.get('countdown_type')
            if cc > 0:
                disp_c = "13+" if cc == 12.5 else str(int(cc))
                color = theme['cd_buy'] if ct == 'buy' else theme['cd_sell']
                td_parts.append(f"C({'B' if ct == 'buy' else 'S'}) <span style='color: {color};'>{disp_c}</span>")
                
            if td_parts:
                html += " | TD " + "  ".join(td_parts)

        self.view.update_status_bar(html)

    def _apply_theme(self, name: str):
        if name in THEMES:
            self.state.theme_name = name
            self.view.apply_theme_styles(THEMES[name])

    def _on_toggle_sidebar(self):
        self.state.sidebar_visible = not self.view.sidebar.isVisible()
        self.view.sidebar.setVisible(self.state.sidebar_visible)
        self.view.toggle_action.setChecked(self.state.sidebar_visible)

    def _on_toggle_tooltips(self, enabled: bool):
        self.state.tooltips_enabled = enabled
        self.view.sidebar.set_tooltips_enabled(enabled)

    def _refresh_recent_symbols_ui(self):
        self.view.update_symbol_list(self.recent_manager.get_top_symbols())