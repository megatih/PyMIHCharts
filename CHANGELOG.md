# Changelog

All notable changes to this project will be documented in this file.

## [2.2.0] - 2026-01-09

### Added
- **Global Tooltip System**: Implemented a comprehensive tooltip system across the entire Sidebar Property Browser.
- **Detailed Component Descriptions**: Added descriptive tooltips to all sidebar widgets (Checkboxes, SpinBoxes, ComboBoxes) and their corresponding labels to explain technical parameters (e.g., TD Lookback, BB Standard Deviations).
- **Collapsible Section Tooltips**: Enhanced `CollapsibleSection` with tooltips on headers and toggle buttons to improve discoverability.
- **Tooltip Toggle**: Added a "Show Tooltips" checkable menu item in the **View** menu to allow users to enable or disable tooltips globally (enabled by default).

### Changed
- **Sidebar UX**: Refactored sidebar layouts to use explicit labels for all form rows, ensuring that hovering over a label provides the same descriptive context as the widget itself.

## [2.1.0] - 2026-01-09

### Added
- **Property Browser Sidebar**: Transformed the sidebar into a modern "Accordion" style Property Browser using collapsible sections.
- **CollapsibleSection Widget**: Created a custom, theme-aware widget that provides clickable headers with chevron icons to manage UI complexity.

### Changed
- **Sidebar Organization**: Reorganized settings into three distinct collapsible groups: **CHART TYPE**, **INDICATORS**, and **FONT SIZES**.
- **Indicator UI Logic**: Grouped all technical indicator settings (TD Sequential and Bollinger Bands) under a single section. Removed automatic visibility toggling for these settings to provide a consistent "Property Grid" experience.
- **Styling**: Enhanced sidebar headers with theme-integrated backgrounds and interactive cursor feedback.

## [2.0.0] - 2026-01-09

### Added
- **Dynamic Font Management**: Introduced a new "FONT SIZES (RELATIVE)" section in the sidebar, allowing users to dynamically adjust the application's base font size and specific offsets for chart elements (Header, Labels, TD Setup, and TD Countdown).
- **Explicit Symbol Search**: Added a dedicated "Search" button to the main toolbar next to the "Load" button. This allows users to manually trigger the `yfinance` search engine for partial ticker matches or company names.
- **Improved Controller Signaling**: Added new signals and slots (`search_requested`, `font_settings_changed`, `on_font_settings_changed`) to coordinate font and search updates across the MVC architecture.

### Changed
- **Indicator Visuals**: Updated the default font offset for TD Sequential Setup numbers from -5 to -3 for improved legibility on modern displays.
- **Toolbar UI**: Updated `set_loading_state` to synchronized all toolbar actions (Load, Search, Input) during background network operations.

## [1.9.0] - 2026-01-08

### Changed
- **System Font Integration**: Removed all hardcoded font families (like "Arial" and "sans-serif") to strictly adhere to OS-level typography settings.
- **Dynamic Font Hierarchy**: Implemented a fully relative font sizing system based on the system's default `QApplication.font()`:
    - **Main Header**: Scaled to `base + 2` for better visual prominence.
    - **Sidebar Headers**: Normalized to `base` (Bold) to match UI standards.
    - **Axis & Legend Labels**: Optimized to `base - 3` for improved legibility on high-DPI screens.
- **Indicator Precision**: Refined internal font caching in `CandlestickChart` to separate axis labels from technical indicator numbers, ensuring that TD Sequential markers remain at their specialized compact sizes (8pt and 10pt) while the rest of the UI scales.

## [1.8.0] - 2026-01-08

### Added
- **Project Evolution**: Officially expanded the project scope from a single-indicator tool to a general-purpose technical analysis platform. More indicators will be added in subsequent releases.
- **Bollinger Bands Indicator**: Implemented a new technical indicator with customizable parameters:
    - Period adjustment (default 20).
    - Moving Average type selection (SMA or EMA).
    - Multi-band support (Toggle 1, 2, and 3 Standard Deviations).
- **Native BB Rendering**: Integrated Bollinger Bands into the `QPainter` engine with theme-aware colors and dynamic legend items.
- **Enhanced Documentation**: Added comprehensive PEP 257 docstrings and PEP 484 type hints across the entire codebase to improve maintainability and developer onboarding.

### Changed
- **Indicator Architecture**: Refactored `models/indicators.py` to use a centralized `calculate_indicators` function, streamlining the data processing pipeline.
- **Controller Logic**: Updated `MainController` to synchronize indicator visibility and parameter changes between the sidebar and the chart engine in real-time.

## [1.7.0] - 2026-01-08

### Added
- **Native Toolbar**: Implemented `QToolBar` with "Unified Title and Toolbar" behavior on macOS for a modern system-integrated look.
- **Resizable Layout**: Replaced static layouts with `QSplitter`, allowing users to resize the sidebar and chart areas dynamically.
- **High DPI Support**: Enabled `Qt.HighDpiScaleFactorRoundingPolicy.PassThrough` for crisp rendering on Retina and high-resolution displays.

### Changed
- **Sidebar Refactor**: Converted sidebar settings to use `QFormLayout` for standardized alignment and adherence to Qt Human Interface Guidelines.
- **System Fonts**: Updated the custom chart rendering engine to inherit `QApplication.font()` instead of using hardcoded Arial, ensuring visual consistency with the OS.
- **Dialog Polishing**: Improved margins, spacing, and messaging in the `SymbolSearchDialog`.

## [1.6.0] - 2026-01-08

### Added
- **Smart Symbol Search**: Implemented a fallback mechanism where entering an invalid symbol triggers a search via `yfinance`.
- **Search Dialog**: Created a dedicated `SymbolSearchDialog` to present matching symbols, companies, and exchange details to the user for selection.
- **Search Architecture**: Added `SearchWorker` in `models/data_manager.py` to handle search queries asynchronously without blocking the UI.

### Changed
- **Error Handling**: Enhanced the "No data found" error flow to automatically initiate a search instead of just displaying an error message.
- **Font Rendering**: Switched the default application font to "sans-serif" to prevent "missing font family" warnings on macOS.

### Fixed
- **NameError Regression**: Fixed a `NameError` in `models/data_manager.py` caused by a missing pandas import.
- **Class Definition**: Restored the `DataWorker` class which was accidentally removed during the search feature implementation.

## [1.5.0] - 2026-01-07

### Added
- **Multi-Threaded Data Engine**: Implemented a dedicated `DataWorker` and `QThread` system to handle market data fetching and indicator calculations. This ensures the GUI remains 100% responsive during intensive processing.
- **MVC Architecture**: Completely refactored the application to follow the Model-View-Controller pattern for better maintainability and scalability.
- **Modular Project Structure**: Decomposed monolithic files into a specialized directory structure (`models/`, `views/`, `controllers/`).
- **Dynamic Layout Management**: Switched to 100% PySide6 layout managers (`QVBoxLayout`, `QHBoxLayout`) and font-aware dynamic margin calculations, ensuring a pixel-perfect responsive experience across all operating systems.

### Changed
- **Async Signal Flow**: Standardized internal communication using asynchronous signal-slot connections between the Model workers and the Controller.
- **Performance Optimization**: 
    - Cached high-frequency objects like `QFontMetrics`.
    - Improved coordinate transformation efficiency in the rendering engine.
- **Entry Point**: Streamlined `main.py` to handle application bootstrapping.

### Fixed
- **UI Responsiveness**: Eliminated GUI "freezing" during ticker data downloads.
- **Layout Consistency**: Resolved an issue where toggling the sidebar would cause inconsistent vertical shifts.
- **Runtime Errors**: Fixed multiple `AttributeError` and `NameError` bugs related to missing imports and initialization race conditions.

## [1.4.0] - 2026-01-07

### Added
- **Multi-Chart Type Support**: Introduced a selection menu in the sidebar to toggle between different chart visualizations.
- **Chart Styles**:
    - **OHLC**: Standard Open-High-Low-Close bars.
    - **Line**: A continuous line connecting Close prices.
    - **Heiken-Ashi**: Trend-filtering candles with dedicated vectorized calculation.
- **Vectorized Heiken-Ashi**: Implemented high-performance Heiken-Ashi math in `td_sequential.py` to ensure smooth rendering even with large datasets.
- **Enhanced Render Logic**: Updated `native_chart.py` to handle different price ranges and rendering paths for each chart type while maintaining TD Sequential indicator visibility.

### Fixed
- **Data Robustness**: Added automatic NaN removal in `calculate_td_sequential` to prevent calculation errors from incomplete yfinance data.
- **UI Initialization**: Fixed an `AttributeError` in `main.py` caused by improper initialization order of UI components and signal connections.

## [1.3.0] - 2026-01-07

### Added
- **Dynamic Theme Engine**: Introduced a centralized theme management system (`themes.py`) supporting real-time GUI color scheme switching.
- **New Color Schemes**:
    - **Lilac**: A soft, non-work-oriented aesthetic using lilac and lavender tones.
    - **Dracula**: Implementation of the popular high-contrast dark theme.
- **Theme Selection Menu**: Added a "View > Color Scheme" menu for seamless theme toggling.
- **Themed UI Components**: Buttons, input fields, status bar, and all chart elements (grid, candles, indicators, legend) now dynamically adapt to the selected theme.

## [1.2.0] - 2026-01-06

### Added
- **Enriched Chart Header**: The chart now displays the asset's full name, exchange, and currency, fetched dynamically via `yfinance`.
- **Touchscreen Support**: Implemented **Pinch-to-Zoom** functionality using PySide6's native gesture framework.
- **Horizontal Legend**: Redesigned the legend as a compact horizontal bar located at the top-left for better chart visibility and space efficiency.

### Fixed
- **PySide6 Compatibility**: Resolved `AttributeError` by correctly referencing `QEvent.Gesture` and `Qt.GestureType.PinchGesture`.
- **Code Optimization**: Removed duplicate method definitions and refined the rendering pipeline padding.

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
- **Initial Release of PyMIHCharts**: A high-performance, native desktop application for professional technical analysis, featuring a robust initial implementation of Tom DeMark's TD Sequential logic.
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
