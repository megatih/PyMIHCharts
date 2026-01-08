"""
Color scheme definitions for PyMIHCharts.

This module acts as a centralized repository for UI color palettes. 
Each theme defines colors for the window, widgets, buttons, and specific 
technical indicators on the chart.
"""

from typing import Dict

# Dictionary containing all available color schemes.
# Keys are theme names used in the 'View -> Color Scheme' menu.
THEMES: Dict[str, Dict[str, str]] = {
    "Default": {
        # UI Elements
        "window_bg": "#1e1e1e",
        "widget_bg": "#333333",
        "button_bg": "#444444",
        "button_hover": "#555555",
        "status_bg": "#222222",
        "status_text": "#aaaaaa",
        "text_main": "#ffffff",
        "text_label": "#808080",
        
        # Chart Elements
        "chart_bg": "#1e1e1e",
        "grid": "#3c3c3c",
        "bull": "#00c800",
        "bear": "#c80000",
        "crosshair": "#969696",
        
        # TD Sequential Indicator
        "setup_buy": "#00ff00",
        "setup_sell": "#ff3232",
        "cd_buy": "#00ffff",
        "cd_sell": "#ffff00",
        "perfected": "#ff00ff",
        
        # Bollinger Bands Indicator
        "bb_mid": "#ffaa00",
        "bb_upper": "#00aaff",
        "bb_lower": "#ff00aa"
    },
    "Lilac": {
        "window_bg": "#2c2433",
        "widget_bg": "#3d3245",
        "button_bg": "#4f4159",
        "button_hover": "#62526e",
        "status_bg": "#241d29",
        "status_text": "#b39ddb",
        "text_main": "#f3e5f5",
        "text_label": "#b39ddb",
        "chart_bg": "#2c2433",
        "grid": "#463d4d",
        "bull": "#b39ddb",
        "bear": "#f48fb1",
        "setup_buy": "#9575cd",
        "setup_sell": "#f06292",
        "cd_buy": "#81d4fa",
        "cd_sell": "#fff176",
        "perfected": "#ce93d8",
        "crosshair": "#7e57c2",
        "bb_mid": "#b39ddb",
        "bb_upper": "#81d4fa",
        "bb_lower": "#f48fb1"
    },
    "Dracula": {
        "window_bg": "#282a36",
        "widget_bg": "#44475a",
        "button_bg": "#6272a4",
        "button_hover": "#7384b5",
        "status_bg": "#191a21",
        "status_text": "#6272a4",
        "text_main": "#f8f8f2",
        "text_label": "#6272a4",
        "chart_bg": "#282a36",
        "grid": "#44475a",
        "bull": "#50fa7b",
        "bear": "#ff5555",
        "setup_buy": "#50fa7b",
        "setup_sell": "#ff5555",
        "cd_buy": "#8be9fd",
        "cd_sell": "#f1fa8c",
        "perfected": "#ff79c6",
        "crosshair": "#6272a4",
        "bb_mid": "#ffb86c",
        "bb_upper": "#8be9fd",
        "bb_lower": "#ff79c6"
    }
}