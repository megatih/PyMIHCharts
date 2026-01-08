"""
Technical analysis module implementing TD Sequential and Bollinger Bands.

This module provides high-performance, vectorized calculations for:
1. TD Sequential: A trend exhaustion indicator by Tom DeMark.
2. Bollinger Bands: Volatility-based bands around a moving average.
3. Heiken-Ashi: A candlestick charting technique for trend filtering.
"""

from typing import Optional, Tuple, List, Dict, Any

import numpy as np
import pandas as pd


def calculate_indicators(df: pd.DataFrame, settings: Dict[str, Any]) -> pd.DataFrame:
    """
    Master function to calculate all requested technical indicators.
    
    This function serves as the primary entry point for the data processing pipeline,
    coordinating multiple technical analysis calculations in a specific order.

    Args:
        df: A pandas DataFrame containing at least 'Open', 'High', 'Low', 'Close'.
        settings: A dictionary containing configuration for various indicators.
                 Expected keys: 'td_lookback', 'td_setup_max', 'td_countdown_max',
                 'bb_period', 'bb_ma_type', 'bb_std_devs'.

    Returns:
        pd.DataFrame: The input DataFrame enriched with all calculated indicator columns.
    """
    # 1. TD Sequential: Calculate trend exhaustion phases
    df = calculate_td_sequential(
        df,
        flip_lookback=settings.get('td_lookback', 4),
        setup_max=settings.get('td_setup_max', 9),
        countdown_max=settings.get('td_countdown_max', 13)
    )

    # 2. Bollinger Bands: Calculate volatility bands
    df = calculate_bollinger_bands(
        df,
        period=settings.get('bb_period', 20),
        ma_type=settings.get('bb_ma_type', 'SMA'),
        std_devs=settings.get('bb_std_devs', [2.0])
    )

    # 3. Heiken-Ashi: Always calculated to support the HA chart type view
    df = calculate_heiken_ashi(df)

    return df


def calculate_td_sequential(
    df: pd.DataFrame,
    flip_lookback: int = 4,
    setup_max: int = 9,
    countdown_max: int = 13
) -> pd.DataFrame:
    """
    Calculates Tom DeMark's TD Sequential indicator on a price DataFrame.

    TD Sequential consists of three phases:
    1. Price Flip: Signals a potential trend reversal.
    2. TD Setup: A series of 9 (default) consecutive bars where close is 
       compared to the close 4 bars ago.
    3. TD Countdown: A 13-bar (default) sequence following a completed setup.

    Args:
        df: A pandas DataFrame containing 'Open', 'High', 'Low', and 'Close' columns.
        flip_lookback: The lookback period for momentum comparisons (default 4).
        setup_max: The number of bars required to complete a Setup (default 9).
        countdown_max: The number of bars required to complete a Countdown (default 13).

    Returns:
        pd.DataFrame: DataFrame enriched with 'setup_count', 'setup_type', 
                     'countdown_count', 'countdown_type', etc.
    """
    df = df.copy()
    # Clean data to prevent calculation errors on missing price points
    df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])
    n = len(df)
    if n == 0:
        return df

    # Extract numpy arrays for high-performance vectorized access during the main loop
    close = df['Close'].values
    high = df['High'].values
    low = df['Low'].values

    # Pre-calculate True High / True Low (used for TDST levels and cancellation rules)
    true_high, true_low = _calculate_true_range_bounds(high, low, close)

    # Pre-allocate result arrays for efficiency
    setup_count_arr = np.zeros(n, dtype=int)
    setup_type_arr = np.full(n, None, dtype=object)
    cd_count_arr = np.zeros(n, dtype=float)
    cd_type_arr = np.full(n, None, dtype=object)
    tdst_res_arr = np.full(n, np.nan)
    tdst_sup_arr = np.full(n, np.nan)
    perfected_arr = np.zeros(n, dtype=bool)

    # State variables for the sequential calculation loop
    active_setup_count = 0
    active_setup_type: Optional[str] = None
    last_completed_setup_type: Optional[str] = None

    active_cd_count = 0
    active_cd_type: Optional[str] = None
    cd_bar_8_close = np.nan

    current_tdst_res = np.nan
    current_tdst_sup = np.nan

    # TD Sequential is state-dependent, requiring a sequential pass through the data
    for i in range(n):
        # --- 1. Price Flip & Setup Phase ---
        # Detect momentum shifts and count setup bars
        active_setup_count, active_setup_type = _process_setup_phase(
            i, close, flip_lookback, active_setup_count, active_setup_type
        )

        if active_setup_count > 0:
            if active_setup_count <= setup_max:
                setup_count_arr[i] = active_setup_count
            setup_type_arr[i] = active_setup_type

            # On completion of bar 9 (or setup_max), determine TDST levels and perfection
            if active_setup_count == setup_max:
                last_completed_setup_type = active_setup_type
                current_tdst_res, current_tdst_sup, perfected_arr[i] = _on_setup_completion(
                    i, active_setup_type, setup_max, true_high, true_low, close, high, low,
                    current_tdst_res, current_tdst_sup
                )
                active_cd_type = active_setup_type
                active_cd_count = 0
            elif active_setup_count > setup_max:
                # TDST levels can expand if the setup continues beyond bar 9
                current_tdst_res, current_tdst_sup = _update_dynamic_tdst(
                    i, active_setup_type, true_high, true_low, current_tdst_res, current_tdst_sup
                )

        # --- 2. Countdown Phase ---
        # Count bars toward 13, checking for cancellation and qualification rules
        active_cd_count, active_cd_type, cd_bar_8_close, cd_val = _process_countdown_phase(
            i, close, high, low, true_high, true_low,
            active_cd_count, active_cd_type, last_completed_setup_type,
            active_setup_count, active_setup_type,
            setup_max, countdown_max,
            current_tdst_res, current_tdst_sup,
            cd_bar_8_close
        )
        
        cd_count_arr[i] = cd_val
        cd_type_arr[i] = active_cd_type
        tdst_res_arr[i] = current_tdst_res
        tdst_sup_arr[i] = current_tdst_sup

    # Assign optimized result arrays back to the DataFrame
    df['setup_count'] = setup_count_arr
    df['setup_type'] = setup_type_arr
    df['countdown_count'] = cd_count_arr
    df['countdown_type'] = cd_type_arr
    df['tdst_res'] = tdst_res_arr
    df['tdst_sup'] = tdst_sup_arr
    df['perfected'] = perfected_arr
    df['true_high'] = true_high
    df['true_low'] = true_low

    return df


def calculate_bollinger_bands(
    df: pd.DataFrame,
    period: int = 20,
    ma_type: str = 'SMA',
    std_devs: List[float] = [2.0]
) -> pd.DataFrame:
    """
    Calculates Bollinger Bands based on a moving average and standard deviation.

    Formula:
    - Middle Band = SMA or EMA of Close
    - Upper Band = Middle Band + (N * Standard Deviation)
    - Lower Band = Middle Band - (N * Standard Deviation)

    Args:
        df: Input DataFrame with 'Close' column.
        period: Lookback period for the moving average (default 20).
        ma_type: Type of moving average ('SMA' or 'EMA').
        std_devs: List of standard deviations to calculate (e.g., [1.0, 2.0]).

    Returns:
        pd.DataFrame: Enriched DataFrame with 'bb_middle' and 'bb_upper_X' / 'bb_lower_X'.
    """
    df = df.copy()
    
    # Calculate Middle Band based on selected Moving Average type
    if ma_type == 'EMA':
        middle_band = df['Close'].ewm(span=period, adjust=False).mean()
    else:
        middle_band = df['Close'].rolling(window=period).mean()

    # Calculate rolling standard deviation for the given period
    rolling_std = df['Close'].rolling(window=period).std()

    df['bb_middle'] = middle_band
    
    # Generate upper and lower bands for each requested standard deviation
    for std in std_devs:
        df[f'bb_upper_{std}'] = middle_band + (rolling_std * std)
        df[f'bb_lower_{std}'] = middle_band - (rolling_std * std)

    return df


def calculate_heiken_ashi(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates Heiken-Ashi candles for trend filtering.
    
    HA candles reduce noise by averaging price data, making trends easier to spot.
    
    Formula:
    - HA_Close = (Open + High + Low + Close) / 4
    - HA_Open = (Previous HA_Open + Previous HA_Close) / 2
    - HA_High = max(High, HA_Open, HA_Close)
    - HA_Low = min(Low, HA_Open, HA_Close)
    """
    df = df.copy()
    n = len(df)
    if n == 0:
        return df
    
    ha_open = np.zeros(n)
    ha_close = (df['Open'].values + df['High'].values + df['Low'].values + df['Close'].values) / 4.0
    
    # Initialize the first HA_Open using the average of the first actual bar
    ha_open[0] = (df['Open'].values[0] + df['Close'].values[0]) / 2.0
    
    # HA_Open calculation is recursive, requiring an iterative loop
    for i in range(1, n):
        ha_open[i] = (ha_open[i-1] + ha_close[i-1]) / 2.0
        
    df['HA_Open'] = ha_open
    df['HA_Close'] = ha_close
    df['HA_High'] = np.maximum(df['High'].values, np.maximum(ha_open, ha_close))
    df['HA_Low'] = np.minimum(df['Low'].values, np.minimum(ha_open, ha_close))
    
    return df


# --- Internal Helper Functions (Private) ---

def _calculate_true_range_bounds(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Vectorized calculation of True High and True Low.
    
    True High = max(current High, previous Close)
    True Low = min(current Low, previous Close)
    """
    n = len(close)
    true_high = np.zeros(n)
    true_low = np.zeros(n)
    true_high[0] = high[0]
    true_low[0] = low[0]
    if n > 1:
        # Vectorized comparison with the previous day's close
        true_high[1:] = np.maximum(high[1:], close[:-1])
        true_low[1:] = np.minimum(low[1:], close[:-1])
    return true_high, true_low


def _process_setup_phase(
    i: int, close: np.ndarray, flip_lookback: int, 
    active_count: int, active_type: Optional[str]
) -> Tuple[int, Optional[str]]:
    """
    Handles Price Flip detection and Setup counting logic.
    
    A Price Flip occurs when the momentum shifts relative to a previous point.
    A Setup is a continuation of that momentum.
    """
    if i < flip_lookback + 1:
        return active_count, active_type

    # Price Flip Detection
    bearish_flip = (close[i-1] > close[i-(flip_lookback+1)]) and (close[i] < close[i-flip_lookback])
    bullish_flip = (close[i-1] < close[i-(flip_lookback+1)]) and (close[i] > close[i-flip_lookback])

    if bearish_flip:
        return 1, 'buy'  # Start of a Buy Setup
    if bullish_flip:
        return 1, 'sell' # Start of a Sell Setup

    # Continuation of active Setup
    if active_type == 'buy':
        if close[i] < close[i-flip_lookback]:
            return active_count + 1, 'buy'
    elif active_type == 'sell':
        if close[i] > close[i-flip_lookback]:
            return active_count + 1, 'sell'

    return 0, None


def _on_setup_completion(
    i: int, active_type: str, setup_max: int, 
    true_high: np.ndarray, true_low: np.ndarray,
    close: np.ndarray, high: np.ndarray, low: np.ndarray,
    current_tdst_res: float, current_tdst_sup: float
) -> Tuple[float, float, bool]:
    """
    Logic executed when a Setup phase completes (e.g., at bar 9).
    Calculates TDST Support/Resistance and checks for Setup 'Perfection'.
    """
    perfected = False
    res, sup = current_tdst_res, current_tdst_sup

    if active_type == 'buy':
        # Resistance is the highest true high of the setup
        res = np.max(true_high[i-(setup_max-1):i+1])
        # perfection: close of bar 8 or 9 is below the low of bars 6 and 7
        if i >= 3:
            if close[i] <= min(low[i-2], low[i-3]) or close[i-1] <= min(low[i-2], low[i-3]):
                perfected = True
    else:
        # Support is the lowest true low of the setup
        sup = np.min(true_low[i-(setup_max-1):i+1])
        # perfection: high of bar 8 or 9 is above the high of bars 6 and 7
        if i >= 3:
            if high[i] >= max(high[i-2], high[i-3]) or high[i-1] >= max(high[i-2], high[i-3]):
                perfected = True
    
    return res, sup, perfected


def _update_dynamic_tdst(
    i: int, active_type: str, true_high: np.ndarray, true_low: np.ndarray,
    current_tdst_res: float, current_tdst_sup: float
) -> Tuple[float, float]:
    """Updates TDST levels if a Setup continues beyond its completion point."""
    res, sup = current_tdst_res, current_tdst_sup
    if active_type == 'buy':
        res = max(res, true_high[i])
    else:
        sup = min(sup, true_low[i])
    return res, sup


def _process_countdown_phase(
    i: int, close: np.ndarray, high: np.ndarray, low: np.ndarray, 
    true_high: np.ndarray, true_low: np.ndarray,
    active_cd_count: int, active_cd_type: Optional[str], last_completed_setup_type: Optional[str],
    active_setup_count: int, active_setup_type: Optional[str],
    setup_max: int, countdown_max: int,
    current_tdst_res: float, current_tdst_sup: float,
    cd_bar_8_close: float
) -> Tuple[int, Optional[str], float, float]:
    """
    Handles Countdown counting, cancellation rules, and qualification logic.
    
    Countdown is the final phase of the TD Sequential indicator leading to a 
    potential exhaustion point (bar 13).
    """
    # Countdown only starts if a setup of the same type has completed
    if not active_cd_type or active_cd_type != last_completed_setup_type:
        return active_cd_count, active_cd_type, cd_bar_8_close, 0.0

    # Cancellation Rules:
    # 1. Opposite Setup of the same length completes
    if active_setup_type != active_cd_type and active_setup_count == setup_max:
        return 0, None, np.nan, 0.0
    
    # 2. Price breaks the TDST level of the opposite direction
    if active_cd_type == 'buy' and true_low[i] > current_tdst_res:
        return 0, None, np.nan, 0.0
    if active_cd_type == 'sell' and true_high[i] < current_tdst_sup:
        return 0, None, np.nan, 0.0

    # Counting Logic
    cd_val = 0.0
    if i < 2:
        return active_cd_count, active_cd_type, cd_bar_8_close, cd_val

    if active_cd_type == 'buy':
        if close[i] <= low[i-2]:
            active_cd_count += 1
            if active_cd_count == 8:
                cd_bar_8_close = close[i]
            
            if active_cd_count < countdown_max:
                cd_val = float(active_cd_count)
            elif active_cd_count == countdown_max:
                # Bar 13 qualification rule
                if low[i] <= cd_bar_8_close:
                    cd_val = float(countdown_max)
                    active_cd_type = None # Completed
                else:
                    active_cd_count = countdown_max - 1
                    cd_val = countdown_max - 0.5 # Visual "13+" indicator
    else: # sell
        if close[i] >= high[i-2]:
            active_cd_count += 1
            if active_cd_count == 8:
                cd_bar_8_close = close[i]
            
            if active_cd_count < countdown_max:
                cd_val = float(active_cd_count)
            elif active_cd_count == countdown_max:
                # Bar 13 qualification rule
                if high[i] >= cd_bar_8_close:
                    cd_val = float(countdown_max)
                    active_cd_type = None # Completed
                else:
                    active_cd_count = countdown_max - 1
                    cd_val = countdown_max - 0.5 # Visual "13+" indicator

    return active_cd_count, active_cd_type, cd_bar_8_close, cd_val