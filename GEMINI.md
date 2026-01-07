# PyMIHCharts - Developer Context

PyMIHCharts is a high-performance, native Python desktop application for technical analysis, specifically implementing Tom DeMark's **TD Sequential** indicator. It features a custom-built rendering engine for interactive candlestick charting without relying on heavy web technologies.

## Project Overview

- **Purpose**: To provide traders with a fast, interactive tool for downloading historical stock data and visualizing TD Sequential patterns.
- **Main Technologies**:
  - **Python 3**: Core language.
  - **PySide6 (Qt for Python)**: Native GUI and high-performance `QPainter` rendering.
  - **yfinance**: Historical data source.
  - **Pandas/NumPy**: Data manipulation and vectorized indicator calculations.

## Architecture & Logic (MVC Pattern)

The application follows a strict Model-View-Controller (MVC) pattern to ensure a clean separation of concerns and maintainability.

### Model Layer (`models/`)
- **`data_manager.py`**: Handles asynchronous fetching of historical market data and metadata via `yfinance`.
- **`indicators.py`**: Contains the core technical analysis logic.
    - **TD Sequential**: Vectorized calculation of Price Flips, Setups (1-9), and Countdowns (1-13). Implements 13-vs-8 qualifiers and TDST level management.
    - **Heiken-Ashi**: Vectorized trend-filtering candle calculations.
- **Performance**: Heavy mathematical operations are offloaded to NumPy arrays to ensure O(n) performance.

### View Layer (`views/`)
- **`chart_view.py`**: The core rendering engine.
    - Uses native PySide6 `QPainter` for high-performance interactive drawing.
    - Dynamically calculates margins and axis spacing using `QFontMetrics`.
    - Handles multi-path rendering for Candlestick, OHLC, Line, and Heiken-Ashi styles.
- **`sidebar_view.py`**: Contains control widgets for indicator settings and chart type selection.
- **`main_view.py`**: The primary `QMainWindow` container that assembles the chart and sidebar layouts.
- **`themes.py`**: Centralized dictionary of color schemes (Default, Lilac, Dracula).

### Controller Layer (`controllers/`)
- **`main_controller.py`**: The "brain" of the application.
    - Orchestrates the data flow between the `DataManager` and the `MainView`.
    - Routes UI signals (button clicks, menu selection, zoom events) to the appropriate model logic or view updates.
    - Manages application-wide states like the active theme and loaded ticker data.

## Features & UI Interactions

- **Dynamic Scaling**: The chart engine automatically adjusts vertical scaling and horizontal bar width based on zoom levels and active chart types.
- **Interactive Navigation**: Fully supports mouse wheel zoom, click-drag panning, and native pinch gestures for touch devices.
- **Responsive Layout**: Uses PySide6 automatic layout strategies combined with dynamic margin calculations to ensure a consistent experience across different resolutions.
- **Rich Status Bar**: Displays real-time, color-coded price data (O, H, L, C) for the hovered bar.

## Development Conventions

- **MVC Isolation**: Never put business logic in the View or UI code in the Model. Use the Controller to bridge the two.
- **Signal-Slot Communication**: Components should communicate via signals to maintain decoupling.
- **Vectorization**: Prefer NumPy vectorization over Pandas `.apply()` or raw Python loops for performance-critical logic.
- **Theme Consistency**: All new UI elements must use the `THEMES` dictionary for color assignments.
- **Documentation**: All modules must maintain PEP 257 docstrings and PEP 484 type hints.
- **Setup**: Use the provided `setup.sh` (Linux), `setup_macos.sh`, or `setup.ps1/bat` (Windows) scripts for environment management.