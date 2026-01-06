# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-01-06

### Added

- **Cross-Platform Support Scripts**:

    - Created `setup_macos.sh` for macOS users.

    - Created `setup.bat` and `run.bat` for Windows Command Prompt.

    - Created `setup.ps1` and `run.ps1` for Windows PowerShell.

- **Setup Perfection Visuals**:

 "Perfected" TD Setup bars (1-9) are now highlighted in **Magenta** on the chart for better visibility.
- **Legend Update**: Added "Perfected Setup" entry to the chart legend.
- **Automated Setup Script**: Created `setup.sh` for Linux to automate virtual environment creation and dependency installation.
    - Added system-level library checks for PySide6/Qt requirements.
    - Included specific installation instructions for **Debian/Ubuntu**, **Fedora**, and **Arch Linux**.

### Changed
- **Code Documentation**: Added comprehensive Python docstrings (PEP 257) and type hints (PEP 484) across all core modules (`main.py`, `native_chart.py`, `td_sequential.py`).
- **Improved Code Quality**: Refined technical comments to better explain the complex TD Sequential math and rendering pipeline logic.

### Fixed
- **Import Error**: Fixed a `NameError` in `main.py` where `QFont` was not imported.
- **Initial Release of PyMIHCharts**: A high-performance, native desktop application for professional technical analysis.
- **Advanced TD Sequential Implementation**:
    - Full implementation of Tom DeMark's TD Sequential logic (Setup 1-9, Countdown 1-13).
    - Includes Price Flip triggers, Setup Perfection checks, and TDST (Setup Trend) resistance/support levels.
    - Implemented the **13-vs-8 qualifier** for Countdowns with support for **Deferral ("13+")** logic.
- **Professional Native Charting Engine**:
    - High-performance rendering using PySide6 `QPainter`, bypassing the need for heavy web engines.
    - **Smart Snapping Crosshairs**: Interactive dotted lines that automatically snap to the Close price and Bar Center.
    - **Adaptive Date Axis**: Intelligent labeling that prioritizes Year/Month transitions and adjusts granularity based on zoom.
    - **Dynamic Price Axis**: Implemented **1-2-5 "Nice Number" logic** for mathematically clean gridlines and adaptive decimal precision.
- **Interactive User Interface**:
    - Smooth scrolling (Click + Drag) and zooming (Mouse Wheel).
    - **Rich Text Status Bar**: Real-time, color-coded price data display (Open, High, Low, Close, Date) with bold field labels.
    - Dark mode professional aesthetic.
- **Optimized Performance**:
    - Vectorized indicator calculations using NumPy for O(n) efficiency.
    - Cached GDI objects (Pens, Fonts, Brushes) in the rendering engine to minimize allocation overhead.
- **Cross-Platform Compatibility**: Optimized specifically for Linux (X11/Wayland) by using native drawing to avoid GPU acceleration issues.
- **Data Connectivity**: Integrated `yfinance` for automated historical daily price data fetching.
