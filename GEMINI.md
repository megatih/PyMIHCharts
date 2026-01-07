# PyMIHCharts - Developer Context

PyMIHCharts is a high-performance, native Python desktop application for technical analysis, specifically implementing Tom DeMark's **TD Sequential** indicator. It features a custom-built rendering engine for interactive candlestick charting using native Qt technologies.

## Project Overview

- **Purpose**: To provide traders with a fast, interactive tool for downloading historical stock data and visualizing TD Sequential patterns.
- **Main Technologies**:
  - **Python 3**: Core language.
  - **PySide6 (Qt for Python)**: Native GUI, high-performance `QPainter` rendering, and `QThread` async management.
  - **yfinance**: Historical data source.
  - **Pandas/NumPy**: Data manipulation and vectorized indicator calculations.

## Architecture & Logic (MVC Pattern)

The application follows a strict Model-View-Controller (MVC) pattern combined with asynchronous workers to ensure a clean separation of concerns and a non-blocking UI.

### Model Layer (`models/`)
- **`data_manager.py`**: Manages data state and coordinates asynchronous processing.
    - **`DataWorker`**: A `QObject` designed to run in a separate `QThread`. It handles ticker downloads and heavy technical indicator math.
    - **`DataManager`**: Controls worker lifecycles and emits signals (`data_ready`, `loading_error`) to the Controller.
- **`indicators.py`**: Contains the core technical analysis logic.
    - **TD Sequential**: Vectorized calculation of Price Flips, Setups, and Countdowns.
    - **Heiken-Ashi**: Vectorized trend-filtering candle calculations.

### View Layer (`views/`)
- **`chart_view.py`**: The core rendering engine.
    - Uses native PySide6 `QPainter` for high-frame-rate interactive drawing.
    - Dynamically calculates margins and axis spacing using cached `QFontMetrics`.
- **`sidebar_view.py`**: Contains control widgets for indicator settings and chart type selection.
- **`main_view.py`**: The primary container that manages the application's overall layout and menu system.
- **`themes.py`**: Centralized repository for UI color schemes.

### Controller Layer (`controllers/`)
- **`main_controller.py`**: The application's orchestrator.
    - Connects View signals to Model requests.
    - Safely bridges background worker results back to the Main UI Thread.
    - Manages application-wide states (Active Ticker, Theme, Visibility).

## Features & UI Interactions

- **Asynchronous Workflow**: All data-heavy operations are offloaded to background threads, keeping the UI responsive even during long downloads.
- **Responsive Layout**: Adheres strictly to PySide6 Layout Managers (`QVBoxLayout`, `QHBoxLayout`), ensuring consistent widget arrangement across different resolutions.
- **Dynamic Scaling**: The chart engine automatically adjusts vertical scaling and horizontal bar width based on viewport constraints.

## Development Conventions

- **Thread Safety**: Never update the UI directly from a background thread. Always use Signals to pass data to the Controller/Main Thread.
- **Passive Views**: View components should never contain business logic. They should only emit intent signals and display provided data.
- **Layout Managers**: Always use `QLayout` subclasses instead of hardcoded `resize()` or `setGeometry()` calls.
- **Vectorization**: Performance-critical math must remain vectorized using NumPy.
