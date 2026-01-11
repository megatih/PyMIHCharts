# Changelog

All notable changes to this project will be documented in this file.

## [3.0.0] - 2026-01-11

### Added
- **Modular Indicator Architecture**: Refactored technical analysis into a registry-based system using `BaseIndicator` and `IndicatorRegistry`. Adding new indicators now requires minimal core code changes.
- **Multi-Pane View System**: Rebuilt the chart engine into a container-based architecture (`ChartContainer` and `ChartPane`). This allows for independent vertical scaling and prepares the app for sub-pane indicators like RSI/MACD.
- **Coordinate Mapping Engine**: Extracted all data-to-pixel transformations into a dedicated `CoordinateMapper` class for better precision and architectural separation.
- **AppState Management**: Introduced a centralized `AppState` dataclass to manage application-wide configuration and ensure synchronization between the UI and rendering engine.
- **JSON Data Persistence**: Migrated `RecentSymbolsManager` from XML to JSON for better structure and future support for nested user preferences.
- **Dynamic Sidebar Visibility**: Configured indicator setting groups to automatically show/hide based on their respective "Show" checkbox state, decluttering the UI.

### Changed
- **Indicator Engine**: Refactored TD Sequential, Bollinger Bands, and Heiken-Ashi into specialized modular classes.
- **Recalculation Logic**: Updated the controller to store `raw_df`, allowing for mathematically accurate indicator recalculations when parameters are changed without re-downloading data.
- **Type Safety**: Applied comprehensive PEP 484 type hints and PEP 585/604 syntax across all new modules.

### Removed
- **Legacy XML Storage**: Removed `recentsymbols.xml` in favor of the new JSON format.
- **Legacy Indicators Module**: Deleted the monolithic `models/indicators.py`.

## [2.4.1] - 2026-01-10
... (rest of the file remains same)