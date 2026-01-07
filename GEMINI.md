# PyMIHCharts - Developer Context

PyMIHCharts is a high-performance, native Python desktop application for technical analysis, specifically implementing Tom DeMark's **TD Sequential** indicator. It features a custom-built rendering engine for interactive candlestick charting without relying on heavy web technologies.

## Project Overview

- **Purpose**: To provide traders with a fast, interactive tool for downloading historical stock data and visualizing TD Sequential patterns.
- **Main Technologies**:
  - **Python 3**: Core language.
  - **PySide6 (Qt for Python)**: Native GUI and high-performance `QPainter` rendering.
  - **yfinance**: Historical data source.
  - **Pandas/NumPy**: Data manipulation and vectorized indicator calculations.

## Architecture & Logic

### `td_sequential.py` (The Model)
- **Vectorized Calculation**: Uses NumPy arrays to calculate Price Flips, Setups, and Countdowns, ensuring O(n) performance.
- **Heiken-Ashi Logic**: Implements high-performance vectorized calculation for trend-filtering candles (`HA_Open`, `HA_High`, `HA_Low`, `HA_Close`).
- **Data Integrity**: Automatically cleans incoming daily data by removing incomplete (NaN) rows before indicator processing.
- **Strict Adherence**: 
  - Setups (1-9) require consecutive conditions and start with a Price Flip.
  - Countdowns (1-13) are non-sequential and require a matching Setup phase.
  - Implements **13-vs-8 qualifier**; failed qualifiers result in a "Deferred" state (represented as `12.5` internally and `13+` visually).
  - **Cancellation**: Countdowns are cancelled by opposite Setup 9s or TDST level violations.

### `native_chart.py` (The View)
- **Multi-Path Rendering**: A single `paintEvent` handles dynamic rendering for **Candlesticks**, **OHLC Bars**, **Line Charts**, and **Heiken-Ashi** candles.
- **Interactive Scaling**: Dynamically adjusts price range and vertical scaling based on the active chart type (e.g., using HA extremes or Closing prices).
- **Smart Snap Crosshairs**: Snapping logic automatically adapts to the visual chart state, locking to `Close` prices or `HA_Close` values.
- **Visual Enhancements**:
  - Highlights **Perfected Setup bars** in theme-aware colors.
  - Features a **horizontal legend** and an enriched header with asset metadata.
- **Optimization**: Uses cached GDI objects and avoids high-overhead allocations during redrawn events.

### `main.py` (The Controller)
- **UI Coordination**: Manages a toggleable sidebar containing both Indicator settings (TD Sequential) and Chart Type selection.
- **Initialization & Safety**: Implements strict initialization order to ensure widgets are fully constructed before signal-slot connections.
- **Asynchronous Workflow**: Bridges the gap between data fetching (`yfinance`) and UI updates with state-aware feedback (e.g., "Loading..." status).
- **Theme Management**: Centralizes style application across the entire application and the chart canvas.

### `themes.py` (Theme Definitions)
- Centralized dictionary of color schemes (Default, Lilac, Dracula).
- Defines colors for window backgrounds, widgets, text, and all chart-specific elements.

## Features & UI Interactions
...
- **Zoom/Pan**: Fully supported via mouse wheel and drag interactions.
- **Theme Engine**: Allows switching between dark, Dracula, and soft Lilac schemes at runtime.
- **Status Bar**: Bolded and color-coded (White: Date, Orange: Open, Green: High, Red: Low, Cyan: Close).
- **Native Experience**: Bypasses GPU/WebEngine issues common on Linux.

## Development Conventions

- **Performance**: Prefer NumPy vectorization over Pandas `.apply()` or raw Python loops.
- **Themes**: All new UI elements must use the `THEMES` dictionary for color assignments.
- **Documentation**: All modules must maintain PEP 257 docstrings and PEP 484 type hints.
- **Setup**: Use `setup.sh` for managing the Linux environment and checking system-level Qt dependencies.
- **UI**: Keep rendering logic inside `native_chart.py` and coordinate logic in `main.py`.
- **Logic**: All technical indicator rules must be isolated in `td_sequential.py`.
