"""
Technical analysis module implementing Tom DeMark's TD Sequential indicator.

This module provides high-performance, vectorized calculations for TD Sequential phases:
1. Price Flip: A change in price momentum.
2. TD Setup: A series of 9 consecutive bars meeting specific criteria.
3. TD Countdown: A 13-bar sequence following a completed Setup.
4. TDST Levels: Support and resistance levels derived from the Setup phase.
"""

import pandas as pd
import numpy as np
from typing import Optional


def calculate_td_sequential(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates Tom DeMark's TD Sequential indicator on a price DataFrame.

    This implementation is optimized using NumPy vectorization where possible and
    efficient single-pass loops for state-dependent logic.

    Args:
        df: A pandas DataFrame containing 'Open', 'High', 'Low', and 'Close' columns.

    Returns:
        pd.DataFrame: The input DataFrame enriched with TD Sequential columns:
            - setup_count: Current count in the Setup phase (1-9).
            - setup_type: 'buy' or 'sell'.
            - countdown_count: Current count in the Countdown phase (1-13).
            - countdown_type: 'buy' or 'sell'.
            - tdst_res: TDST Resistance level.
            - tdst_sup: TDST Support level.
            - perfected: Boolean indicating if a Setup 9 is "perfected".
            - true_high: Vectorized True High (max of current High and previous Close).
            - true_low: Vectorized True Low (min of current Low and previous Close).
    """
    df = df.copy()
    n = len(df)
    
    # Initialize result columns to default values
    df['setup_count'] = 0
    df['setup_type'] = None
    df['countdown_count'] = 0.0
    df['countdown_type'] = None
    df['tdst_res'] = np.nan
    df['tdst_sup'] = np.nan
    df['perfected'] = False

    # Extract numpy arrays for high-performance access during iteration
    close = df['Close'].values
    high = df['High'].values
    low = df['Low'].values
    
    # Vectorized True High / True Low calculation
    # True High is the higher of the current high and the previous close
    # True Low is the lower of the current low and the previous close
    true_high = np.zeros(n)
    true_low = np.zeros(n)
    true_high[0] = high[0]
    true_low[0] = low[0]
    if n > 1:
        true_high[1:] = np.maximum(high[1:], close[:-1])
        true_low[1:] = np.minimum(low[1:], close[:-1])

    # Pre-allocate result arrays for speed
    setup_count_arr = np.zeros(n, dtype=int)
    setup_type_arr = np.full(n, None, dtype=object)
    cd_count_arr = np.zeros(n, dtype=float)
    cd_type_arr = np.full(n, None, dtype=object)
    tdst_res_arr = np.full(n, np.nan)
    tdst_sup_arr = np.full(n, np.nan)
    perfected_arr = np.zeros(n, dtype=bool)

    # State variables to track indicator progress through the time series
    active_setup_count = 0
    active_setup_type: Optional[str] = None
    last_completed_setup_type: Optional[str] = None
    
    active_cd_count = 0
    active_cd_type: Optional[str] = None
    cd_bar_8_close = np.nan  # Used for 13-vs-8 qualifier
    
    current_tdst_res = np.nan
    current_tdst_sup = np.nan

    for i in range(n):
        # --- 1. Price Flip & Setup Phase ---
        # A Setup requires a Price Flip to start.
        # A Buy Price Flip occurs when a close is less than the close 4 bars ago, 
        # preceded by a close greater than or equal to the close 4 bars ago.
        if i >= 5:
            bearish_flip = (close[i-1] > close[i-5]) and (close[i] < close[i-4])
            bullish_flip = (close[i-1] < close[i-5]) and (close[i] > close[i-4])
            
            if bearish_flip:
                active_setup_count = 1
                active_setup_type = 'buy'
            elif bullish_flip:
                active_setup_count = 1
                active_setup_type = 'sell'
            elif active_setup_type == 'buy':
                # Continue Buy Setup if Close < Close[i-4]
                if close[i] < close[i-4]:
                    active_setup_count += 1
                else:
                    active_setup_count = 0
                    active_setup_type = None
            elif active_setup_type == 'sell':
                # Continue Sell Setup if Close > Close[i-4]
                if close[i] > close[i-4]:
                    active_setup_count += 1
                else:
                    active_setup_count = 0
                    active_setup_type = None
        
        # Record Setup progress
        if active_setup_count > 0:
            if active_setup_count <= 9:
                setup_count_arr[i] = active_setup_count
            setup_type_arr[i] = active_setup_type
            
            # Setup Completion Logic (Bar 9)
            if active_setup_count == 9:
                last_completed_setup_type = active_setup_type
                
                if active_setup_type == 'buy':
                    # TDST Resistance is the True High of the entire Setup
                    current_tdst_res = np.max(true_high[i-8:i+1])
                    
                    # Perfection: Bar 8 or 9 Low must be <= Low of Bar 6 AND 7
                    if close[i] <= min(low[i-2], low[i-3]) or close[i-1] <= min(low[i-2], low[i-3]):
                        perfected_arr[i] = True
                    
                    # Prepare for Countdown
                    active_cd_type = 'buy'
                    active_cd_count = 0 
                else:
                    # TDST Support is the True Low of the entire Setup
                    current_tdst_sup = np.min(true_low[i-8:i+1])
                    
                    # Perfection: Bar 8 or 9 High must be >= High of Bar 6 AND 7
                    if high[i] >= max(high[i-2], high[i-3]) or high[i-1] >= max(high[i-2], high[i-3]):
                        perfected_arr[i] = True
                    
                    # Prepare for Countdown
                    active_cd_type = 'sell'
                    active_cd_count = 0

            # Dynamic TDST Level updates (Setup beyond bar 9)
            if active_setup_count > 9:
                if active_setup_type == 'buy':
                    current_tdst_res = max(current_tdst_res, true_high[i])
                else:
                    current_tdst_sup = min(current_tdst_sup, true_low[i])

        # --- 2. Countdown Phase ---
        # Buy Countdown: Close <= Low[i-2]. Requires 13 bars (not necessarily consecutive).
        if active_cd_type == 'buy' and last_completed_setup_type == 'buy':
            # Cancellation Rules:
            # 1. Opposite completed Setup
            if active_setup_type == 'sell' and active_setup_count == 9:
                active_cd_type = None
                active_cd_count = 0
            # 2. Price violation of TDST Resistance
            elif true_low[i] > current_tdst_res:
                active_cd_type = None
                active_cd_count = 0
            
            if active_cd_type == 'buy' and i >= 2:
                if close[i] <= low[i-2]:
                    active_cd_count += 1
                    if active_cd_count == 8:
                        cd_bar_8_close = close[i]
                    
                    if active_cd_count < 13:
                        cd_count_arr[i] = float(active_cd_count)
                    elif active_cd_count == 13:
                        # 13-vs-8 Qualifier: Bar 13 Low must be <= Bar 8 Close
                        if low[i] <= cd_bar_8_close:
                            cd_count_arr[i] = 13.0
                            active_cd_type = None # Countdown completed
                        else:
                            # Deferred 13 (represented as 12.5)
                            active_cd_count = 12 
                            cd_count_arr[i] = 12.5

        # Sell Countdown: Close >= High[i-2].
        elif active_cd_type == 'sell' and last_completed_setup_type == 'sell':
            # Cancellation Rules
            if active_setup_type == 'buy' and active_setup_count == 9:
                active_cd_type = None
                active_cd_count = 0
            elif true_high[i] < current_tdst_sup:
                active_cd_type = None
                active_cd_count = 0
            
            if active_cd_type == 'sell' and i >= 2:
                if close[i] >= high[i-2]:
                    active_cd_count += 1
                    if active_cd_count == 8:
                        cd_bar_8_close = close[i]
                    
                    if active_cd_count < 13:
                        cd_count_arr[i] = float(active_cd_count)
                    elif active_cd_count == 13:
                        # 13-vs-8 Qualifier: Bar 13 High must be >= Bar 8 Close
                        if high[i] >= cd_bar_8_close:
                            cd_count_arr[i] = 13.0
                            active_cd_type = None
                        else:
                            active_cd_count = 12
                            cd_count_arr[i] = 12.5

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

    return df