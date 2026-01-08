"""
Main window view component for PyMIHCharts.
"""

from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLineEdit, QSplitter, QStatusBar, QToolBar, QSizePolicy)
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt, Signal, QSize
from views.chart_view import CandlestickChart
from views.sidebar_view import SidebarView
from views.themes import THEMES


class MainView(QMainWindow):
    """
    The primary window that assembles the chart and sidebar.
    """
    load_requested = Signal(str)
    sidebar_toggled = Signal()
    theme_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyMIHCharts")
        # Let the OS/WindowManager decide initial size or placement usually, 
        # but a reasonable default is fine.
        self.resize(1200, 800)
        
        # Native Mac Toolbar behavior
        self.setUnifiedTitleAndToolBarOnMac(True)
        
        self._init_ui()
        self._init_menu()

    def _init_ui(self):
        # --- Toolbar ---
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        # Toggle Action
        # Using a standard looking icon or text. 
        # Since we don't have assets, we'll stick to text but in a proper Action.
        self.toggle_action = QAction("Sidebar", self)
        self.toggle_action.setCheckable(True)
        self.toggle_action.setChecked(True)
        self.toggle_action.setToolTip("Toggle Settings Panel")
        self.toggle_action.triggered.connect(self.sidebar_toggled.emit)
        self.toolbar.addAction(self.toggle_action)
        
        self.toolbar.addSeparator()

        # Spacer
        spacer_left = QWidget()
        spacer_left.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(spacer_left)

        # Ticker Input
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("Ticker (e.g. AAPL)")
        self.symbol_input.setText("AAPL")
        self.symbol_input.setFixedWidth(150)
        self.symbol_input.returnPressed.connect(self._on_load_clicked)
        self.toolbar.addWidget(self.symbol_input)
        
        # Load Action
        self.load_action = QAction("Load", self)
        self.load_action.triggered.connect(self._on_load_clicked)
        self.toolbar.addAction(self.load_action)

        # Spacer
        spacer_right = QWidget()
        spacer_right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(spacer_right)

        # --- Central Area (Splitter) ---
        self.splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(self.splitter)

        self.sidebar = SidebarView()
        self.chart = CandlestickChart()
        
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.chart)
        
        # Set stretch factors: Sidebar (0) fixed/preferred, Chart (1) expanding
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        
        # Initialize sidebar visibility
        self.sidebar.setVisible(True)

        # --- Status Bar ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLineEdit() # Using read-only line edit or label? Label is better for status.
        # Actually QStatusBar has its own message method, but for persistent OHLC data, adding a permanent widget is standard.
        # However, a simple label is easiest.
        from PySide6.QtWidgets import QLabel
        self.status_lbl_widget = QLabel("Ready")
        self.status_lbl_widget.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.status_lbl_widget.setStyleSheet("padding: 0 10px;")
        self.status_bar.addPermanentWidget(self.status_lbl_widget, 1)

    def _on_load_clicked(self):
        """Helper to emit load request with current input text."""
        self.load_requested.emit(self.symbol_input.text())

    def _init_menu(self):
        self.menu_bar = self.menuBar()
        self.view_menu = self.menu_bar.addMenu("View")
        
        # Add Sidebar toggle to View menu as well
        self.view_menu.addAction(self.toggle_action)
        self.view_menu.addSeparator()
        
        self.theme_menu = self.view_menu.addMenu("Color Scheme")
        
        for theme_name in THEMES.keys():
            action = self.theme_menu.addAction(theme_name)
            action.triggered.connect(lambda checked=False, name=theme_name: self.theme_requested.emit(name))

    def update_status_bar(self, html_text: str):
        # We use a permanent widget for OHLC data to avoid it being cleared by temporary messages
        self.status_lbl_widget.setText(html_text)

    def set_loading_state(self, is_loading: bool):
        self.load_action.setEnabled(not is_loading)
        self.symbol_input.setEnabled(not is_loading)
        self.load_action.setText("Loading..." if is_loading else "Load")
        if is_loading:
            self.status_bar.showMessage("Downloading data...", 0)
        else:
            self.status_bar.clearMessage()

    def apply_theme_styles(self, theme: dict):
        # Apply theme primarily to the window background and specific components
        # We avoid over-styling standard widgets to keep native look where possible,
        # but since 'theme' dictates colors, we apply them to the Palette if we were using QPalette.
        # For this refactor, we stick to minimal stylesheet application on the container level.
        
        self.setStyleSheet(f"QMainWindow {{ background-color: {theme['window_bg']}; color: {theme['text_main']}; }}")
        
        # Status Bar styling
        self.status_bar.setStyleSheet(
            f"QStatusBar {{ background-color: {theme['status_bg']}; color: {theme['status_text']}; }}"
        )
        self.status_lbl_widget.setStyleSheet(f"color: {theme['status_text']};")

        # Pass theme to sub-views
        self.sidebar.apply_theme_styles(theme)
        self.chart.apply_theme(theme)
