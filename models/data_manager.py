"""
Model component for fetching and managing market data with threading support.
"""

from typing import Optional, Dict, Any, Tuple
import yfinance as yf
import pandas as pd
from PySide6.QtCore import QObject, Signal, QThread
from models.indicators import calculate_td_sequential


class DataWorker(QObject):
    """
    Worker to handle data fetching and indicator calculation in a separate thread.
    """
    finished = Signal(pd.DataFrame, dict)
    error = Signal(str)

    def __init__(self, symbol: str, settings: dict):
        super().__init__()
        self.symbol = symbol
        self.settings = settings

    def run(self):
        """Executes the long-running data tasks."""
        try:
            ticker = yf.Ticker(self.symbol)
            df = ticker.history(period="max", interval="1d")

            if df.empty:
                self.error.emit(f"No data found for symbol: {self.symbol}")
                return

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Perform indicator calculation in the worker thread as well
            processed_df = calculate_td_sequential(
                df,
                flip_lookback=self.settings.get('lookback', 4),
                setup_max=self.settings.get('setup_max', 9),
                countdown_max=self.settings.get('countdown_max', 13)
            )

            info = ticker.info
            metadata = {
                'symbol': self.symbol,
                'full_name': info.get('longName', self.symbol),
                'exchange': info.get('exchange', 'Unknown'),
                'currency': info.get('currency', 'USD')
            }

            self.finished.emit(processed_df, metadata)
        except Exception as e:
            self.error.emit(str(e))


class SearchWorker(QObject):
    """
    Worker to handle symbol search in a separate thread.
    """
    results_ready = Signal(list)
    error = Signal(str)

    def __init__(self, query: str):
        super().__init__()
        self.query = query

    def run(self):
        """Executes the search query using yfinance."""
        try:
            search = yf.Search(self.query, news_count=0)
            # Accessing .quotes triggers the actual request
            quotes = search.quotes
            self.results_ready.emit(quotes)
        except Exception as e:
            self.error.emit(str(e))


class DataManager(QObject):
    """
    Manages data states and coordinates threading for data operations.
    """
    data_ready = Signal(pd.DataFrame, dict)
    loading_error = Signal(str)
    search_results = Signal(list)

    def __init__(self):
        super().__init__()
        self.raw_df: Optional[pd.DataFrame] = None
        self.metadata: Dict[str, str] = {}
        self._thread: Optional[QThread] = None
        self._worker: Optional[DataWorker] = None
        self._search_thread: Optional[QThread] = None
        self._search_worker: Optional[SearchWorker] = None

    def request_data(self, symbol: str, settings: dict):
        """Starts a new thread to fetch and process data."""
        # Cleanup previous thread if still running
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait()

        self._thread = QThread()
        self._worker = DataWorker(symbol, settings)
        self._worker.moveToThread(self._thread)

        # Connections
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._handle_finished)
        self._worker.error.connect(self._handle_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        
        self._thread.start()

    def search_symbol(self, query: str):
        """Starts a new thread to search for symbols."""
        if self._search_thread and self._search_thread.isRunning():
            self._search_thread.quit()
            self._search_thread.wait()

        self._search_thread = QThread()
        self._search_worker = SearchWorker(query)
        self._search_worker.moveToThread(self._search_thread)
        
        self._search_thread.started.connect(self._search_worker.run)
        self._search_worker.results_ready.connect(self.search_results.emit)
        # On error, we might just emit an empty list or log it, but for now let's just clean up
        self._search_worker.results_ready.connect(self._search_thread.quit)
        self._search_worker.error.connect(self._search_thread.quit)
        
        self._search_thread.start()

    def _handle_finished(self, df, metadata):
        self.raw_df = df
        self.metadata = metadata
        self.data_ready.emit(df, metadata)

    def _handle_error(self, message):
        self.loading_error.emit(message)