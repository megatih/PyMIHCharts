# PyMIHCharts

A high-performance, native Python desktop application for professional technical analysis using Tom DeMark's **TD Sequential** indicator.

![PyMIHCharts Screenshot](PyMIHCharts_Screenshot.png)

## Key Features

- **Advanced TD Sequential Logic**: Full implementation including Price Flips, Setup (1-9), Setup Perfection, TDST levels, and Countdown (1-13) with the 13-vs-8 qualifier and deferral (+).
- **Setup Perfection Visuals**: "Perfected" Setup bars are automatically highlighted in **Magenta** for immediate identification of key price exhaustion points.
- **Professional Charting Engine**:
    - **Native Rendering**: High-performance candlestick chart drawn using PySide6 `QPainter`.
    - **Enriched Metadata**: Chart title now includes Full Name, Exchange, and Currency for each symbol.
    - **Smart Crosshairs**: Fine dotted lines that automatically snap to the **Close** price and bar center.
    - **Adaptive Date Axis**: Intelligently labels Years and Months based on zoom level, using contextual formatting to reduce clutter.
    - **"Nice Number" Price Axis**: Dynamic gridlines that snap to clean mathematical increments (1-2-5 logic) with adaptive decimal precision.
- **Interactive UI**:
    - **Smooth Navigation**: Mouse wheel or **Pinch-to-Zoom** (touchscreens) for zooming, and click-drag for panning.
    - **Enhanced Status Bar**: Real-time, color-coded price data (O, H, L, C) displayed in a bolded, right-justified format.
- **Data Integration**: Automatic historical daily data downloads via `yfinance`.

## Installation

### Prerequisites
- Python 3.8+
- Linux (X11/Wayland), Windows, or macOS

#### Quick Start (Linux)
1. Run the automated setup script: `./setup.sh`
2. Launch: `./run.sh`

### Quick Start (macOS)
1. Run the automated setup script: `./setup_macos.sh`
2. Launch: `./run.sh`

### Quick Start (Windows)
**Using Command Prompt:**
1. Run: `setup.bat`
2. Launch: `run.bat`

**Using PowerShell:**
1. Run: `./setup.ps1`
2. Launch: `./run.ps1`

*Manual Setup:*
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

## How to Use
1. Enter a stock or crypto ticker (e.g., `AAPL`, `BTC-USD`) in the input field.
2. Click **Load Chart**.
3. Use the **Mouse Wheel** to zoom and **Left-Click + Drag** to scroll.
4. Hover over any bar to trigger the **Snapping Crosshair** and see detailed price info at the bottom right.

## TD Sequential Trading Strategy

TD Sequential is designed to identify price exhaustion points and potential reversals based on Tom DeMark's research.

### 1. The Setup (9 Counts)
- **Goal**: Identifies a short-term overextended trend.
- **Signal**: A completed **Green 9 (Buy Setup)** or **Red 9 (Sell Setup)** suggests a momentary pause or reversal (typically for 1-4 bars).
- **Perfection**: A Setup is "Perfected" (highlighted in **Magenta**) when the high/low of bar 8 or 9 exceeds the extreme of bars 6 and 7. DeMark suggests waiting for perfection before anticipating a reversal.

### 2. TDST Levels (Support/Resistance)
- **Definition**: The highest high (for Buy Setups) or lowest low (for Sell Setups) occurring within a completed Setup 1-9.
- **Usage**: These levels act as critical support or resistance lines.
    - **Reversal**: If price respects the TDST level, the counter-trend signal is reinforced.
    - **Continuation**: If price closes decisively beyond the TDST level, the current trend is strong, and the Setup signal is likely invalid (suggesting trend continuation).

### 3. The Countdown (13 Counts)
- **Goal**: Identifies longer-term trend exhaustion (major top or bottom).
- **Signal**: A completed **13 Countdown** indicates the trend has likely depleted its momentum.
- **Qualifier**: This app enforces the "13 vs 8" qualifier (Close of bar 13 must be better than Close of bar 8) and displays a "13+" (deferred) if the condition isn't met yet.

## License
Parity Public License 7.0.0 (See LICENSE.md for details)