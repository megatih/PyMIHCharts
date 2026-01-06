# PyMIHCharts

A high-performance, native Python desktop application for professional technical analysis using Tom DeMark's **TD Sequential** indicator.

## Key Features

- **Advanced TD Sequential Logic**: Full implementation including Price Flips, Setup (1-9), Setup Perfection, TDST levels, and Countdown (1-13) with the 13-vs-8 qualifier and deferral (+).
- **Setup Perfection Visuals**: "Perfected" Setup bars are automatically highlighted in **Magenta** for immediate identification of key price exhaustion points.
- **Professional Charting Engine**:
    - **Native Rendering**: High-performance candlestick chart drawn using PySide6 `QPainter`.
    - **Smart Crosshairs**: Fine dotted lines that automatically snap to the **Close** price and bar center.
    - **Adaptive Date Axis**: Intelligently labels Years and Months based on zoom level, using contextual formatting to reduce clutter.
    - **"Nice Number" Price Axis**: Dynamic gridlines that snap to clean mathematical increments (1-2-5 logic) with adaptive decimal precision.
- **Interactive UI**:
    - **Smooth Navigation**: Mouse wheel for zooming and click-drag for panning.
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

## License
Parity Public License 7.0.0 (See LICENSE.md for details)