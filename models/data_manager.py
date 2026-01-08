"""
Model component for fetching and managing market data with threading support.

The DataManager coordinates between the View/Controller and background workers
to ensure that networking and heavy math operations do not freeze the UI.
"""

from typing import Optional, Dict, Any, Tuple, List
import yfinance as yf
import pandas as pd
from PySide6.QtCore import QObject, Signal, QThread
from models.indicators import calculate_indicators


class DataWorker(QObject):
    """
    Worker to handle data fetching and indicator calculation in a separate thread.
    
    This object is moved to a QThread to execute its 'run' method asynchronously.
    """
    finished = Signal(pd.DataFrame, dict)
    error = Signal(str)

    def __init__(self, symbol: str, settings: dict):
        """
        Initializes the worker with target symbol and indicator settings.
        
        Args:
            symbol: The ticker symbol to fetch (e.g., 'AAPL').
            settings: Dictionary of indicator parameters.
        """
        super().__init__()
        self.symbol = symbol
        self.settings = settings

    def run(self):
        """
        Executes the long-running data tasks: fetching from yfinance and 
        calculating technical indicators.
        """
        try:
            ticker = yf.Ticker(self.symbol)
            # Fetch maximum available daily history
            df = ticker.history(period="max", interval="1d")

            if df.empty:
                self.error.emit(f"No data found for symbol: {self.symbol}")
                return

            # Flatten MultiIndex columns if present (common in recent yfinance versions)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Perform indicator calculation in the worker thread to keep UI responsive
            processed_df = calculate_indicators(df, self.settings)

            # Fetch metadata for display
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
    
    Triggered when a direct lookup fails, suggesting similar symbols to the user.
    """
    results_ready = Signal(list)
    error = Signal(str)

    def __init__(self, query: str):
        super().__init__()
        self.query = query

    def run(self):
        """Executes the search query using yfinance's search API."""
        try:
            search = yf.Search(self.query, news_count=0)
            # Accessing .quotes triggers the actual web request
            quotes = search.quotes
            self.results_ready.emit(quotes)
        except Exception as e:
            self.error.emit(str(e))


class DataManager(QObject):
    """
    Manages data states and coordinates threading for data operations.
    
    The DataManager maintains the 'raw' (undownloaded) state of data and
    orchestrates QThread lifecycles for both fetching and searching.
    """
    data_ready = Signal(pd.DataFrame, dict)
    loading_error = Signal(str)
    search_results = Signal(list)

    def __init__(self):
        super().__init__()
        self.raw_df: Optional[pd.DataFrame] = None
        self.metadata: Dict[str, str] = {}
        
        # Thread and worker management attributes
        self._thread: Optional[QThread] = None
        self._worker: Optional[DataWorker] = None
        self._search_thread: Optional[QThread] = None
        self._search_worker: Optional[SearchWorker] = None

    def request_data(self, symbol: str, settings: dict):
        """
        Starts a new thread to fetch and process data for a symbol.
        
        Args:
            symbol: Ticker symbol to load.
            settings: Indicator parameters to apply during calculation.
        """
        # Cleanup previous thread if it's still running to avoid race conditions
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait()

        self._thread = QThread()
        self._worker = DataWorker(symbol, settings)
        self._worker.moveToThread(self._thread)

        # Connect signals between worker and manager/thread
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._handle_finished)
        self._worker.error.connect(self._handle_error)
        
        # Ensure thread cleanup on finish or error
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        
        self._thread.start()

    def search_symbol(self, query: str):
        """
        Starts a new thread to search for symbols matching the query.
        
        Args:
            query: The search string (e.g., 'APPLE' instead of 'AAPL').
        """
        if self._search_thread and self._search_thread.isRunning():
            self._search_thread.quit()
            self._search_thread.wait()

        self._search_thread = QThread()
        self._search_worker = SearchWorker(query)
        self._search_worker.moveToThread(self._search_thread)
        
        self._search_thread.started.connect(self._search_worker.run)
        self._search_worker.results_ready.connect(self.search_results.emit)
        
        # Cleanup connections
        self._search_worker.results_ready.connect(self._search_thread.quit)
        self._search_worker.error.connect(self._search_thread.quit)
        
        self._search_thread.start()

    def _handle_finished(self, df: pd.DataFrame, metadata: dict):
        """Internal handler for successful data loading."""
        self.raw_df = df
        self.metadata = metadata
        self.data_ready.emit(df, metadata)

    def _handle_error(self, message: str):
        """Internal handler for data loading errors."""
        self.loading_error.emit(message)
