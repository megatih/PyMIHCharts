"""
Main window view component for PyMIHCharts.

This class serves as the top-level container, assembling the Toolbar, 
the interactive Chart, the Sidebar settings panel, and the Status Bar.
"""

from typing import Optional, Dict, Any
from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLineEdit, QSplitter, QStatusBar, QToolBar, QSizePolicy, QLabel)
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt, Signal, QSize
from views.chart_view import CandlestickChart
from views.sidebar_view import SidebarView
from views.themes import THEMES


class MainView(QMainWindow):
    """
    The primary application window responsible for layout management and global UI actions.
    """
    
    # Signals notifying the controller of high-level user intents
    load_requested = Signal(str)
    sidebar_toggled = Signal()
    theme_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyMIHCharts")
        # Default starting resolution
        self.resize(1200, 800)
        
        # Optimize toolbar for macOS native appearance
        self.setUnifiedTitleAndToolBarOnMac(True)
        
        self._init_ui()
        self._init_menu()

    def _init_ui(self):
        """Initializes the central layout and primary widgets."""
        
        # --- 1. Toolbar Configuration ---
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        # Sidebar toggle action
        self.toggle_action = QAction("Sidebar", self)
        self.toggle_action.setCheckable(True)
        self.toggle_action.setChecked(True)
        self.toggle_action.setToolTip("Toggle Settings Panel")
        self.toggle_action.triggered.connect(self.sidebar_toggled.emit)
        self.toolbar.addAction(self.toggle_action)
        
        self.toolbar.addSeparator()

        # Left spacer to center the input field area
        spacer_left = QWidget()
        spacer_left.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(spacer_left)

        # Ticker Input Field
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("Ticker (e.g. AAPL)")
        self.symbol_input.setText("AAPL")
        self.symbol_input.setFixedWidth(150)
        self.symbol_input.returnPressed.connect(self._on_load_clicked)
        self.toolbar.addWidget(self.symbol_input)
        
        # Ticker Load Button
        self.load_action = QAction("Load", self)
        self.load_action.triggered.connect(self._on_load_clicked)
        self.toolbar.addAction(self.load_action)

        # Right spacer
        spacer_right = QWidget()
        spacer_right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(spacer_right)

        # --- 2. Central Area (Splitter for resizing Chart/Sidebar) ---
        self.splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(self.splitter)

        self.sidebar = SidebarView()
        self.chart = CandlestickChart()
        
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.chart)
        
        # Layout weights: Sidebar (0) uses its preferred size, Chart (1) takes remaining space
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        
        self.sidebar.setVisible(True)

        # --- 3. Status Bar ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # HTML-enabled label for detailed OHLC data display
        self.status_lbl_widget = QLabel("Ready")
        self.status_lbl_widget.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.status_lbl_widget.setStyleSheet("padding: 0 10px;")
        # Permanent widgets in status bar persist even when temporary messages are shown
        self.status_bar.addPermanentWidget(self.status_lbl_widget, 1)

    def _on_load_clicked(self):
        """Helper to collect text and emit a request to load a ticker."""
        self.load_requested.emit(self.symbol_input.text())

    def _init_menu(self):
        """Configures the standard application menu bar."""
        self.menu_bar = self.menuBar()
        self.view_menu = self.menu_bar.addMenu("View")
        
        # Mirror the toolbar's sidebar toggle in the menu
        self.view_menu.addAction(self.toggle_action)
        self.view_menu.addSeparator()
        
        # Dynamic theme selection menu
        self.theme_menu = self.view_menu.addMenu("Color Scheme")
        for theme_name in THEMES.keys():
            action = self.theme_menu.addAction(theme_name)
            # Use a lambda to capture the theme name for the signal
            action.triggered.connect(lambda checked=False, name=theme_name: self.theme_requested.emit(name))

    def update_status_bar(self, html_text: str):
        """Updates the persistent OHLC label in the status bar."""
        self.status_lbl_widget.setText(html_text)

    def set_loading_state(self, is_loading: bool):
        """Disables inputs and shows a message during network operations."""
        self.load_action.setEnabled(not is_loading)
        self.symbol_input.setEnabled(not is_loading)
        self.load_action.setText("Loading..." if is_loading else "Load")
        if is_loading:
            self.status_bar.showMessage("Downloading data...", 0)
        else:
            self.status_bar.clearMessage()

    def apply_theme_styles(self, theme: Dict[str, str]):
        """Applies global color definitions from the theme to the UI layout."""
        
        # Set main window background
        self.setStyleSheet(f"QMainWindow {{ background-color: {theme['window_bg']}; color: {theme['text_main']}; }}")
        
        # Style the status bar components
        self.status_bar.setStyleSheet(
            f"QStatusBar {{ background-color: {theme['status_bg']}; color: {theme['status_text']}; }}"
        )
        self.status_lbl_widget.setStyleSheet(f"color: {theme['status_text']};")

        # Propagate theme settings to specialized child views
        self.sidebar.apply_theme_styles(theme)
        self.chart.apply_theme(theme)