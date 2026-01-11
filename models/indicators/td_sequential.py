"""
Tom DeMark (TD) Sequential technical indicator implementation.
"""

from typing import Any, Tuple, Optional
import numpy as np
import pandas as pd
from models.indicators.base import BaseIndicator
from models.enums import IndicatorType
from models.data_models import TDSequentialSettings

class TDSequential(BaseIndicator):
    """
    Implements Tom DeMark's trend exhaustion indicator.
    """
    
    def __init__(self):
        super().__init__("TD Sequential", IndicatorType.OVERLAY)

    def calculate(self, df: pd.DataFrame, settings: TDSequentialSettings) -> pd.DataFrame:
        """
        Coordinates the multi-phase TD Sequential calculation.
        """
        df = df.copy()
        df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])
        n = len(df)
        if n == 0:
            return df

        # Configuration
        flip_lookback = settings.lookback
        setup_max = settings.setup_max
        countdown_max = settings.countdown_max

        # Extract arrays for vectorized/loop performance
        close = df['Close'].values
        high = df['High'].values
        low = df['Low'].values

        # 1. Pre-calculate True Range Bounds
        true_high, true_low = self._calculate_true_range_bounds(high, low, close)

        # 2. Sequential Loop (State dependent)
        setup_count_arr, setup_type_arr, cd_count_arr, cd_type_arr, \
        tdst_res_arr, tdst_sup_arr, perfected_arr = self._process_sequential_logic(
            n, close, high, low, true_high, true_low, 
            flip_lookback, setup_max, countdown_max
        )

        # 3. Assign Results
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

    def _calculate_true_range_bounds(self, high, low, close) -> Tuple[np.ndarray, np.ndarray]:
        n = len(close)
        true_high, true_low = np.zeros(n), np.zeros(n)
        true_high[0], true_low[0] = high[0], low[0]
        if n > 1:
            true_high[1:] = np.maximum(high[1:], close[:-1])
            true_low[1:] = np.minimum(low[1:], close[:-1])
        return true_high, true_low

    def _process_sequential_logic(self, n, close, high, low, true_high, true_low, 
                                 flip_lookback, setup_max, countdown_max):
        # Result arrays
        setup_count_arr = np.zeros(n, dtype=int)
        setup_type_arr = np.full(n, None, dtype=object)
        cd_count_arr = np.zeros(n, dtype=float)
        cd_type_arr = np.full(n, None, dtype=object)
        tdst_res_arr = np.full(n, np.nan)
        tdst_sup_arr = np.full(n, np.nan)
        perfected_arr = np.zeros(n, dtype=bool)

        # Iteration State
        a_setup_count, a_setup_type = 0, None
        l_setup_type = None
        a_cd_count, a_cd_type = 0, None
        cd_bar_8_close = np.nan
        c_tdst_res, c_tdst_sup = np.nan, np.nan

        for i in range(n):
            # --- Setup Phase ---
            a_setup_count, a_setup_type = self._update_setup(
                i, close, flip_lookback, a_setup_count, a_setup_type
            )

            if a_setup_count > 0:
                if a_setup_count <= setup_max:
                    setup_count_arr[i] = a_setup_count
                setup_type_arr[i] = a_setup_type

                if a_setup_count == setup_max:
                    l_setup_type = a_setup_type
                    c_tdst_res, c_tdst_sup, perfected_arr[i] = self._on_setup_finished(
                        i, a_setup_type, setup_max, true_high, true_low, close, high, low,
                        c_tdst_res, c_tdst_sup
                    )
                    a_cd_type, a_cd_count = a_setup_type, 0
                elif a_setup_count > setup_max:
                    c_tdst_res, c_tdst_sup = self._update_tdst(
                        i, a_setup_type, true_high, true_low, c_tdst_res, c_tdst_sup
                    )

            # --- Countdown Phase ---
            a_cd_count, a_cd_type, cd_bar_8_close, cd_val = self._update_countdown(
                i, close, high, low, true_high, true_low,
                a_cd_count, a_cd_type, l_setup_type,
                a_setup_count, a_setup_type,
                setup_max, countdown_max,
                c_tdst_res, c_tdst_sup, cd_bar_8_close
            )
            
            cd_count_arr[i] = cd_val
            cd_type_arr[i] = a_cd_type
            tdst_res_arr[i] = c_tdst_res
            tdst_sup_arr[i] = c_tdst_sup

        return setup_count_arr, setup_type_arr, cd_count_arr, cd_type_arr, \
               tdst_res_arr, tdst_sup_arr, perfected_arr

    def _update_setup(self, i, close, lookback, count, s_type):
        if i < lookback + 1: return count, s_type
        b_flip = (close[i-1] > close[i-(lookback+1)]) and (close[i] < close[i-lookback])
        u_flip = (close[i-1] < close[i-(lookback+1)]) and (close[i] > close[i-lookback])

        if b_flip: return 1, 'buy'
        if u_flip: return 1, 'sell'

        if s_type == 'buy' and close[i] < close[i-lookback]: return count + 1, 'buy'
        if s_type == 'sell' and close[i] > close[i-lookback]: return count + 1, 'sell'
        return 0, None

    def _on_setup_finished(self, i, s_type, s_max, t_hi, t_lo, close, high, low, c_res, c_sup):
        perf = False
        res, sup = c_res, c_sup
        if s_type == 'buy':
            res = np.max(t_hi[i-(s_max-1):i+1])
            if i >= 3 and (close[i] <= min(low[i-2], low[i-3]) or close[i-1] <= min(low[i-2], low[i-3])): perf = True
        else:
            sup = np.min(t_lo[i-(s_max-1):i+1])
            if i >= 3 and (high[i] >= max(high[i-2], high[i-3]) or high[i-1] >= max(high[i-2], high[i-3])): perf = True
        return res, sup, perf

    def _update_tdst(self, i, s_type, t_hi, t_lo, c_res, c_sup):
        res, sup = c_res, c_sup
        if s_type == 'buy': res = max(res, t_hi[i])
        else: sup = min(sup, t_lo[i])
        return res, sup

    def _update_countdown(self, i, close, high, low, t_hi, t_lo,
                          cd_count, cd_type, l_s_type,
                          a_s_count, a_s_type,
                          s_max, cd_max, c_res, c_sup, cd_8_close):
        if not cd_type or cd_type != l_s_type: return cd_count, cd_type, cd_8_close, 0.0
        if a_s_type != cd_type and a_s_count == s_max: return 0, None, np.nan, 0.0
        if cd_type == 'buy' and t_lo[i] > c_res: return 0, None, np.nan, 0.0
        if cd_type == 'sell' and t_hi[i] < c_sup: return 0, None, np.nan, 0.0

        if i < 2: return cd_count, cd_type, cd_8_close, 0.0
        cd_val = 0.0
        if cd_type == 'buy':
            if close[i] <= low[i-2]:
                cd_count += 1
                if cd_count == 8: cd_8_close = close[i]
                if cd_count < cd_max: cd_val = float(cd_count)
                elif cd_count == cd_max:
                    if low[i] <= cd_8_close: cd_val, cd_type = float(cd_max), None
                    else: cd_count, cd_val = cd_max - 1, cd_max - 0.5
        else: # sell
            if close[i] >= high[i-2]:
                cd_count += 1
                if cd_count == 8: cd_8_close = close[i]
                if cd_count < cd_max: cd_val = float(cd_count)
                elif cd_count == cd_max:
                    if high[i] >= cd_8_close: cd_val, cd_type = float(cd_max), None
                    else: cd_count, cd_val = cd_max - 1, cd_max - 0.5
        return cd_count, cd_type, cd_8_close, cd_val
