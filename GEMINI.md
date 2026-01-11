# PyMIHCharts - Developer Context

PyMIHCharts is a high-performance, native Python desktop application for professional technical analysis. It features a custom-built rendering engine for interactive candlestick charting using native Qt technologies and provides a modular, registry-based framework for implementing various technical indicators.

## Project Overview

- **Purpose**: To provide traders with a fast, interactive tool for downloading historical stock data and visualizing technical patterns. The architecture is designed for extreme modularity, allowing for easy expansion of indicators and chart types.
- **Main Technologies**:
  - **Python 3**: Core language.
  - **PySide6 (Qt for Python)**: Native GUI, high-performance `QPainter` rendering, and `QThread` async management.
  - **yfinance**: Historical data source.
  - **Pandas/NumPy**: Data manipulation and vectorized indicator calculations.

## Architecture & Logic (Strict MVC Pattern)

The application follows a strict Model-View-Controller (MVC) pattern combined with asynchronous workers to ensure a clean separation of concerns and a non-blocking UI.

### Model Layer (`models/`)
- **`data_models.py`**: Defines structured dataclasses (`AppState`, `ChartData`, `IndicatorSettings`) for type-safe data passing.
- **`enums.py`**: Centralized type definitions for `ChartType`, `Interval`, and `MAType`.
- **`data_manager.py`**: Manages data state and coordinates asynchronous processing via `DataWorker` and `SearchWorker`.
- **`indicators/`**: Modular indicator system.
    - **`base.py`**: Abstract base class `BaseIndicator`.
    - **`registry.py`**: `IndicatorRegistry` and `IndicatorManager` for orchestrating the calculation pipeline.
    - **Implementations**: `td_sequential.py`, `bollinger_bands.py`, `heiken_ashi.py`.
- **`recent_symbols.py`**: Handles persistent JSON storage of user-entered symbols with popularity-based sorting.

### View Layer (`views/`)
- **`chart/`**: Advanced multi-pane rendering engine.
    - **`chart_pane.py`**: Base class for individual drawing areas.
    - **`price_pane.py`**: specialized pane for price action and overlays (TD, BB).
    - **`coordinate_mapper.py`**: Handles mathematical data-to-pixel transformations.
- **`chart_view.py`**: The `ChartContainer` that manages multiple panes and handles global input (zoom/pan).
- **`sidebar_view.py`**: A modern Property Browser with dynamic visibility for indicator settings.
- **`main_view.py`**: The primary container with a unified macOS-style toolbar and recent symbols dropdown.

### Controller Layer (`controllers/`)
- **`main_controller.py`**: The application's orchestrator. Synchronizes the `AppState` between the Model and View. Manages recalculation logic using cached raw data to ensure responsiveness.

## Features & UI Interactions

- **Asynchronous Workflow**: Background threads handle all data-heavy operations.
- **Dynamic Legend Engine**: Real-time, color-coded legend and status bar system with professional abbreviations (O, H, L, C, M, U, L, S, C).
- **Interactive Synchronization**: Specialized controller logic ensures parent container and child panes maintain data parity for immediate hover feedback.
- **Multi-Pane Architecture**: Ready for sub-pane indicators (RSI/MACD) through the `ChartPane` system.
- **JSON Persistence**: Modernized configuration storage.
- **Dynamic Scaling**: Smart vertical scaling and coordinate mapping for pixel-perfect rendering.

## Development Conventions

- **Modularity**: New indicators should inherit from `BaseIndicator` and be added to the registry.
- **Multi-Pane Logic**: New oscillators should inherit from `ChartPane` and be added to the `ChartContainer` layout.
- **Thread Safety**: Always use Signals/Slots to communicate between background workers and the UI.
- **Vectorization**: Technical indicator math must remain vectorized using NumPy for performance.