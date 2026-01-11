"""
Model component for fetching market data with threading support.
"""

from typing import Optional, Dict, Any, List
import yfinance as yf
import pandas as pd
from PySide6.QtCore import QObject, Signal, QThread
from models.indicators.registry import IndicatorManager
from models.data_models import AppState, ChartMetadata, ChartData

class DataWorker(QObject):
    """
    Background worker for data fetching and technical analysis.
    """
    finished = Signal(ChartData)
    error = Signal(str)

    def __init__(self, symbol: str, app_state: AppState):
        super().__init__()
        self.symbol = symbol
        self.app_state = app_state
        self.indicator_manager = IndicatorManager()

    def _get_safe_period(self) -> str:
        interval = self.app_state.interval.value
        if interval == "1m": return "7d"
        elif interval in ["2m", "5m", "15m", "30m", "90m"]: return "60d"
        elif interval in ["60m", "1h"]: return "730d"
        return "max"

    def run(self):
        try:
            ticker = yf.Ticker(self.symbol)
            df = ticker.history(period=self._get_safe_period(), interval=self.app_state.interval.value)

            if df.empty:
                self.error.emit(f"No data found for symbol: {self.symbol}")
                return

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Perform calculations using the modular manager
            processed_df = self.indicator_manager.calculate_all(df.copy(), self.app_state)

            info = ticker.info
            metadata = ChartMetadata(
                symbol=self.symbol,
                full_name=info.get('longName', self.symbol),
                exchange=info.get('exchange', 'Unknown'),
                currency=info.get('currency', 'USD')
            )

            self.finished.emit(ChartData(df=processed_df, metadata=metadata, raw_df=df))
        except Exception as e:
            self.error.emit(str(e))

class SearchWorker(QObject):
    results_ready = Signal(list)
    error = Signal(str)

    def __init__(self, query: str):
        super().__init__()
        self.query = query

    def run(self):
        try:
            search = yf.Search(self.query, news_count=0)
            self.results_ready.emit(search.quotes)
        except Exception as e:
            self.error.emit(str(e))

class DataManager(QObject):
    """
    Coordinates threading and manages the current dataset.
    """
    data_ready = Signal(ChartData)
    loading_error = Signal(str)
    search_results = Signal(list)

    def __init__(self):
        super().__init__()
        self.current_data: Optional[ChartData] = None
        self._thread: Optional[QThread] = None
        self._worker: Optional[DataWorker] = None
        self._search_thread: Optional[QThread] = None
        self._search_worker: Optional[SearchWorker] = None

    def request_data(self, symbol: str, app_state: AppState):
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait()

        self._thread = QThread()
        self._worker = DataWorker(symbol, app_state)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._handle_finished)
        self._worker.error.connect(self._handle_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        
        self._thread.start()

    def search_symbol(self, query: str):
        if self._search_thread and self._search_thread.isRunning():
            self._search_thread.quit()
            self._search_thread.wait()

        self._search_thread = QThread()
        self._search_worker = SearchWorker(query)
        self._search_worker.moveToThread(self._search_thread)
        
        self._search_thread.started.connect(self._search_worker.run)
        self._search_worker.results_ready.connect(self.search_results.emit)
        self._search_worker.results_ready.connect(self._search_thread.quit)
        self._search_worker.error.connect(self._search_thread.quit)
        
        self._search_thread.start()

    def _handle_finished(self, chart_data: ChartData):
        self.current_data = chart_data
        self.data_ready.emit(chart_data)

    def _handle_error(self, message: str):
        self.loading_error.emit(message)