# Changelog

All notable changes to this project will be documented in this file.

## [3.1.0] - 2026-01-11

### Added
- **Dynamic Chart Legend**: Implemented a 1-line color-coded legend below the chart header that displays real-time values for all enabled indicators (Bollinger Bands, TD Sequential).
- **Latest OHLC Data**: Integrated color-coded Open, High, Low, and Close values for the rightmost bar directly into the chart's primary legend line.
- **Interval Awareness**: The main chart header now dynamically displays the active data interval (e.g., `[1d]`, `[1h]`) alongside the security metadata.

### Changed
- **Legend Logic**: Shifted from displaying static indicator parameters to real-time, data-driven values from the most recent bar.
- **Header Rendering**: Enhanced `PricePane` header rendering to support multi-color text segments for better visual clarity.

## [3.0.0] - 2026-01-11

## [2.4.1] - 2026-01-10
... (rest of the file remains same)