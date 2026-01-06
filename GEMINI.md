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
- **Strict Adherence**: 
  - Setups (1-9) require consecutive conditions and start with a Price Flip.
  - Countdowns (1-13) are non-sequential and require a matching Setup phase.
  - Implements **13-vs-8 qualifier**; failed qualifiers result in a "Deferred" state (represented as `12.5` internally and `13+` visually).
  - **Cancellation**: Countdowns are cancelled by opposite Setup 9s or TDST level violations.

### `native_chart.py` (The View)
- **Rendering**: Uses a single `paintEvent` with cached GDI objects (Pens, Fonts, Colors) to minimize allocation overhead.
- **Visuals**:
  - Highlights **Perfected Setup bars** in Magenta.
  - Features a dynamic legend with indicator descriptions.
- **Smart Date Axis**: 
  - Scans visible data for Month/Year transitions.
  - Calculates an optimal `month_step` (1, 2, 3, 6) based on pixel density.
  - Prioritizes Year labels (Bold White) over Month labels (Gray).
- **Price Axis**: 
  - Uses **1-2-5 logic** to find "nice" mathematical increments.
  - Dynamically calculates decimal precision based on the current increment size.
- **Interaction**:
  - **Crosshairs**: Snaps horizontal line to `Close` and vertical line to `Bar Center`.
  - **Hover**: Emits rich-text compatible data for the status bar.

### `main.py` (The Controller)
- Manages the top-level layout and styling.
- Connects the asynchronous-like data loading to the UI.
- Implements the **HTML-formatted Status Bar** for color-coded data visualization.

## Features & UI Interactions

- **Zoom/Pan**: Fully supported via mouse wheel and drag interactions.
- **Status Bar**: Bolded and color-coded (White: Date, Orange: Open, Green: High, Red: Low, Cyan: Close).
- **Native Experience**: Bypasses GPU/WebEngine issues common on Linux.

## Development Conventions

- **Performance**: Prefer NumPy vectorization over Pandas `.apply()` or raw Python loops.
- **Documentation**: All modules must maintain PEP 257 docstrings and PEP 484 type hints.
- **Setup**: Use `setup.sh` for managing the Linux environment and checking system-level Qt dependencies.
- **UI**: Keep rendering logic inside `native_chart.py` and coordinate logic in `main.py`.
- **Logic**: All technical indicator rules must be isolated in `td_sequential.py`.
