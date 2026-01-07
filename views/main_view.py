"""
Main window view component for PyMIHCharts.
"""

from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLineEdit, QPushButton, QLabel, QSizePolicy)
from PySide6.QtCore import Qt, Signal
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
        self.setWindowTitle("PyMIHCharts - Native TD Sequential")
        self.resize(1200, 800)
        
        self._init_ui()
        self._init_menu()

    def _init_ui(self):
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)

        # Header Container
        self.header_widget = QWidget()
        self.header_layout = QHBoxLayout(self.header_widget)
        
        self.sidebar_toggle_btn = QPushButton("☰")
        self.sidebar_toggle_btn.setToolTip("Toggle Side Panel")
        self.sidebar_toggle_btn.clicked.connect(self.sidebar_toggled.emit)
        
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("Enter Ticker (e.g., AAPL, BTC-USD)")
        self.symbol_input.setText("AAPL")
        self.symbol_input.returnPressed.connect(self._on_load_clicked)
        
        self.load_button = QPushButton("Load Chart")
        self.load_button.clicked.connect(self._on_load_clicked)
        
        self.header_layout.addWidget(self.sidebar_toggle_btn)
        self.header_layout.addWidget(QLabel("Ticker:"))
        self.header_layout.addWidget(self.symbol_input)
        self.header_layout.addWidget(self.load_button)
        self.main_layout.addWidget(self.header_widget)

        # Content Container (Sidebar + Chart)
        self.content_area = QWidget()
        self.content_layout = QHBoxLayout(self.content_area)

        self.sidebar = SidebarView()
        self.chart = CandlestickChart()
        self.chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.content_layout.addWidget(self.sidebar)
        self.content_layout.addWidget(self.chart)
        
        # Priority to the chart
        self.content_layout.setStretchFactor(self.sidebar, 0)
        self.content_layout.setStretchFactor(self.chart, 1)
        
        self.main_layout.addWidget(self.content_area, stretch=1)

        # Status Bar Container
        self.status_label = QLabel("Hover over chart to see price data")
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.main_layout.addWidget(self.status_label)

    def _on_load_clicked(self):
        """Helper to emit load request with current input text."""
        self.load_requested.emit(self.symbol_input.text())

    def _init_menu(self):
        self.menu_bar = self.menuBar()
        self.view_menu = self.menu_bar.addMenu("View")
        self.theme_menu = self.view_menu.addMenu("Color Scheme")
        
        for theme_name in THEMES.keys():
            action = self.theme_menu.addAction(theme_name)
            action.triggered.connect(lambda checked=False, name=theme_name: self.theme_requested.emit(name))

    def update_status_bar(self, html_text: str):
        self.status_label.setText(html_text)

    def set_loading_state(self, is_loading: bool):
        self.load_button.setEnabled(not is_loading)
        self.load_button.setText("Loading..." if is_loading else "Load Chart")

    def apply_theme_styles(self, theme: dict):
        self.setStyleSheet(f"QMainWindow {{ background-color: {theme['window_bg']}; color: {theme['text_main']}; }}")
        
        self.sidebar_toggle_btn.setStyleSheet(
            f"QPushButton {{ background-color: {theme['button_bg']}; color: {theme['text_main']}; border: none; font-size: 18px; }} "
            f"QPushButton:hover {{ background-color: {theme['button_hover']}; }}"
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
        
        self.sidebar.apply_theme_styles(theme)
        self.chart.apply_theme(theme)
