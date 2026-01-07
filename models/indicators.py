"""
Technical analysis module implementing Tom DeMark's TD Sequential indicator.

This module provides high-performance, vectorized calculations for TD Sequential phases:
1. Price Flip: A change in price momentum.
2. TD Setup: A series of 9 consecutive bars meeting specific criteria.
3. TD Countdown: A 13-bar sequence following a completed Setup.
4. TDST Levels: Support and resistance levels derived from the Setup phase.
"""

from typing import Optional, Tuple

import numpy as np
import pandas as pd


def calculate_td_sequential(
    df: pd.DataFrame,
    flip_lookback: int = 4,
    setup_max: int = 9,
    countdown_max: int = 13
) -> pd.DataFrame:
    """
    Calculates Tom DeMark's TD Sequential indicator on a price DataFrame.

    This implementation is optimized using NumPy vectorization where possible and
    efficient single-pass loops for state-dependent logic.

    Args:
        df: A pandas DataFrame containing 'Open', 'High', 'Low', and 'Close' columns.
        flip_lookback: The lookback period for Price Flip and Setup comparisons (default 4).
        setup_max: The number of bars required to complete a Setup (default 9).
        countdown_max: The number of bars required to complete a Countdown (default 13).

    Returns:
        pd.DataFrame: The input DataFrame enriched with TD Sequential columns.
    """
    df = df.copy()
    # Ensure data is clean for technical calculations
    df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])
    n = len(df)
    if n == 0:
        return df

    # Extract numpy arrays for high-performance access during iteration
    close = df['Close'].values
    high = df['High'].values
    low = df['Low'].values

    # True High / True Low calculation
    true_high, true_low = _calculate_true_range_bounds(high, low, close)

    # Pre-allocate result arrays
    setup_count_arr = np.zeros(n, dtype=int)
    setup_type_arr = np.full(n, None, dtype=object)
    cd_count_arr = np.zeros(n, dtype=float)
    cd_type_arr = np.full(n, None, dtype=object)
    tdst_res_arr = np.full(n, np.nan)
    tdst_sup_arr = np.full(n, np.nan)
    perfected_arr = np.zeros(n, dtype=bool)

    # State variables
    active_setup_count = 0
    active_setup_type: Optional[str] = None
    last_completed_setup_type: Optional[str] = None

    active_cd_count = 0
    active_cd_type: Optional[str] = None
    cd_bar_8_close = np.nan

    current_tdst_res = np.nan
    current_tdst_sup = np.nan

    for i in range(n):
        # --- 1. Price Flip & Setup Phase ---
        active_setup_count, active_setup_type = _process_setup_phase(
            i, close, flip_lookback, active_setup_count, active_setup_type
        )

        if active_setup_count > 0:
            if active_setup_count <= setup_max:
                setup_count_arr[i] = active_setup_count
            setup_type_arr[i] = active_setup_type

            if active_setup_count == setup_max:
                last_completed_setup_type = active_setup_type
                current_tdst_res, current_tdst_sup, perfected_arr[i] = _on_setup_completion(
                    i, active_setup_type, setup_max, true_high, true_low, close, high, low,
                    current_tdst_res, current_tdst_sup
                )
                active_cd_type = active_setup_type
                active_cd_count = 0
            elif active_setup_count > setup_max:
                current_tdst_res, current_tdst_sup = _update_dynamic_tdst(
                    i, active_setup_type, true_high, true_low, current_tdst_res, current_tdst_sup
                )

        # --- 2. Countdown Phase ---
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

    # Assign optimized arrays back to DataFrame
    df['setup_count'] = setup_count_arr
    df['setup_type'] = setup_type_arr
    df['countdown_count'] = cd_count_arr
    df['countdown_type'] = cd_type_arr
    df['tdst_res'] = tdst_res_arr
    df['tdst_sup'] = tdst_sup_arr
    df['perfected'] = perfected_arr
    df['true_high'] = true_high
    df['true_low'] = true_low

    return calculate_heiken_ashi(df)


def _calculate_true_range_bounds(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Calculates vectorized True High and True Low."""
    n = len(close)
    true_high = np.zeros(n)
    true_low = np.zeros(n)
    true_high[0] = high[0]
    true_low[0] = low[0]
    if n > 1:
        true_high[1:] = np.maximum(high[1:], close[:-1])
        true_low[1:] = np.minimum(low[1:], close[:-1])
    return true_high, true_low


def _process_setup_phase(
    i: int, close: np.ndarray, flip_lookback: int, 
    active_count: int, active_type: Optional[str]
) -> Tuple[int, Optional[str]]:
    """Handles Price Flip and Setup counting logic."""
    if i < flip_lookback + 1:
        return active_count, active_type

    bearish_flip = (close[i-1] > close[i-(flip_lookback+1)]) and (close[i] < close[i-flip_lookback])
    bullish_flip = (close[i-1] < close[i-(flip_lookback+1)]) and (close[i] > close[i-flip_lookback])

    if bearish_flip:
        return 1, 'buy'
    if bullish_flip:
        return 1, 'sell'

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
    """Handles logic when a Setup phase completes (e.g., bar 9)."""
    perfected = False
    res, sup = current_tdst_res, current_tdst_sup

    if active_type == 'buy':
        res = np.max(true_high[i-(setup_max-1):i+1])
        if i >= 3:
            if close[i] <= min(low[i-2], low[i-3]) or close[i-1] <= min(low[i-2], low[i-3]):
                perfected = True
    else:
        sup = np.min(true_low[i-(setup_max-1):i+1])
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
    """Handles Countdown counting, cancellation, and qualification logic."""
    if not active_cd_type or active_cd_type != last_completed_setup_type:
        return active_cd_count, active_cd_type, cd_bar_8_close, 0.0

    # Cancellation Rules
    if active_setup_type != active_cd_type and active_setup_count == setup_max:
        return 0, None, np.nan, 0.0
    
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
                if low[i] <= cd_bar_8_close:
                    cd_val = float(countdown_max)
                    active_cd_type = None # Completed
                else:
                    active_cd_count = countdown_max - 1
                    cd_val = countdown_max - 0.5 # Visual 13+
    else: # sell
        if close[i] >= high[i-2]:
            active_cd_count += 1
            if active_cd_count == 8:
                cd_bar_8_close = close[i]
            
            if active_cd_count < countdown_max:
                cd_val = float(active_cd_count)
            elif active_cd_count == countdown_max:
                if high[i] >= cd_bar_8_close:
                    cd_val = float(countdown_max)
                    active_cd_type = None # Completed
                else:
                    active_cd_count = countdown_max - 1
                    cd_val = countdown_max - 0.5 # Visual 13+

    return active_cd_count, active_cd_type, cd_bar_8_close, cd_val


def calculate_heiken_ashi(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates Heiken-Ashi candles for the given DataFrame.
    
    Formula:
    HA_Close = (Open + High + Low + Close) / 4
    HA_Open = (Previous HA_Open + Previous HA_Close) / 2
    HA_High = max(High, HA_Open, HA_Close)
    HA_Low = min(Low, HA_Open, HA_Close)
    """
    df = df.copy()
    n = len(df)
    if n == 0:
        return df
    
    ha_open = np.zeros(n)
    ha_close = (df['Open'].values + df['High'].values + df['Low'].values + df['Close'].values) / 4.0
    
    # Initialize first HA_Open
    ha_open[0] = (df['Open'].values[0] + df['Close'].values[0]) / 2.0
    
    # Calculate HA_Open iteratively as it depends on previous values
    for i in range(1, n):
        ha_open[i] = (ha_open[i-1] + ha_close[i-1]) / 2.0
        
    df['HA_Open'] = ha_open
    df['HA_Close'] = ha_close
    df['HA_High'] = np.maximum(df['High'].values, np.maximum(ha_open, ha_close))
    df['HA_Low'] = np.minimum(df['Low'].values, np.minimum(ha_open, ha_close))
    
    return df
