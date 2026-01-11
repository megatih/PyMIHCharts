"""
The primary chart pane for rendering price action and overlays.
"""

from typing import Optional, Dict, Any, Tuple, List
import math
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics, QBrush
from PySide6.QtCore import Qt, QRectF, QPointF
import pandas as pd
import numpy as np
from views.chart.chart_pane import ChartPane
from models.enums import ChartType
from models.data_models import TDSequentialSettings, BollingerBandsSettings

class PricePane(ChartPane):
    """
    Renders Candlesticks, OHLC, or Line charts along with TD Sequential 
    and Bollinger Band overlays.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.metadata: Dict[str, str] = {}
        self.chart_type = ChartType.CANDLESTICK
        
        # Indicator Settings
        self.td_settings = TDSequentialSettings()
        self.bb_settings = BollingerBandsSettings()
        self.show_td = True
        self.show_bb = False
        self.bb_std_devs: List[float] = [2.0]
        
        # Fonts
        self.font_main = QFont()
        self.font_labels = QFont()
        self.font_td_setup = QFont()
        self.font_td_cd = QFont()
        self.fm_main = QFontMetrics(self.font_main)
        self.fm_labels = QFontMetrics(self.font_labels)

        # Interaction
        self.mouse_pos: Optional[QPointF] = None

    def update_fonts(self, font_settings: Any):
        """Updates font objects based on relative settings."""
        base_font = self.font()
        bs = font_settings.base_size
        
        self.font_main = QFont(base_font)
        self.font_main.setPointSize(bs + font_settings.header_offset)
        self.font_main.setBold(True)
        
        self.font_labels = QFont(base_font)
        self.font_labels.setPointSize(bs + font_settings.labels_offset)
        
        self.font_td_setup = QFont(base_font)
        self.font_td_setup.setPointSize(bs + font_settings.td_setup_offset)
        
        self.font_td_cd = QFont(base_font)
        self.font_td_cd.setPointSize(bs + font_settings.td_countdown_offset)
        self.font_td_cd.setBold(True)
        
        self.fm_main = QFontMetrics(self.font_main)
        self.fm_labels = QFontMetrics(self.font_labels)
        self.update()

    def paintEvent(self, event):
        if self.df is None or self.df.empty:
            painter = QPainter(self)
            painter.setPen(Qt.white)
            painter.drawText(self.rect(), Qt.AlignCenter, "No Data Loaded")
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. Prepare Viewport & Data
        visible_df, start_idx, end_idx = self._get_visible_data()
        if visible_df.empty: return
        
        self._calculate_ranges(visible_df)
        self._update_mapper()
        
        # 2. Background
        painter.fillRect(self.rect(), QColor(self.theme.get("chart_bg", "#1e1e1e")))
        
        # 3. Grid & Axis
        self._draw_grid(painter, visible_df, start_idx, end_idx)
        
        # 4. Overlays (Background Layer)
        if self.show_bb:
            self._draw_bollinger_bands(painter, visible_df)
            
        # 5. Main Price Series
        self._draw_price_series(painter, visible_df)
        
        # 6. Overlays (Foreground Layer)
        if self.show_td:
            self._draw_td_sequential(painter, visible_df)
            
        # 7. Metadata & UI Overlays
        self._draw_header(painter)
        if self.mouse_pos:
            self._draw_crosshairs(painter)

    def _calculate_ranges(self, visible_df: pd.DataFrame):
        """Finds min/max prices to fit the viewport."""
        if self.chart_type == ChartType.HEIKEN_ASHI:
            min_p, max_p = visible_df['HA_Low'].min(), visible_df['HA_High'].max()
        elif self.chart_type == ChartType.LINE:
            min_p, max_p = visible_df['Close'].min(), visible_df['Close'].max()
        else:
            min_p, max_p = visible_df['Low'].min(), visible_df['High'].max()
            
        if self.show_bb:
            for std in self.bb_std_devs:
                if f'bb_upper_{std}' in visible_df.columns:
                    max_p = max(max_p, visible_df[f'bb_upper_{std}'].max())
                if f'bb_lower_{std}' in visible_df.columns:
                    min_p = min(min_p, visible_df[f'bb_lower_{std}'].min())
                    
        buf = (max_p - min_p) * 0.1 if max_p != min_p else 1.0
        self.min_p, self.max_p = min_p - buf, max_p + buf

    def _update_mapper(self):
        """Synchronizes mapper with current state."""
        p_right = self.fm_labels.horizontalAdvance("00000.00") + 10
        p_top = self.fm_main.height() + 40
        p_bottom = self.fm_labels.height() + 15
        
        self.mapper.update_view_dims(self.width(), self.height(), p_top, p_bottom, 10, p_right)
        self.mapper.update_data_range(self.min_p, self.max_p, self.visible_bars, self.scroll_offset)

    def _draw_grid(self, painter: QPainter, visible_df, start_idx, end_idx):
        painter.setPen(QPen(QColor(self.theme.get("grid", "#3c3c3c")), 1))
        painter.setFont(self.font_labels)
        
        # Vertical Price Axis
        h = self.height() - self.mapper.p_top - self.mapper.p_bottom
        p_range = self.max_p - self.min_p
        max_ticks = max(1, h // 50)
        raw_inc = p_range / max_ticks if p_range > 0 else 1
        p10 = 10 ** math.floor(math.log10(raw_inc)) if raw_inc > 0 else 1
        nice_inc = min([p10, 2*p10, 5*p10, 10*p10], key=lambda x: abs(x - raw_inc))
        precision = 0 if nice_inc >= 1 and nice_inc == int(nice_inc) else max(0, math.ceil(-math.log10(nice_inc)))
        
        curr_tick = math.ceil(self.min_p / nice_inc) * nice_inc
        while curr_tick <= self.max_p:
            y = self.mapper.price_to_y(curr_tick)
            painter.setPen(QPen(QColor(self.theme.get("grid", "#3c3c3c")), 1))
            painter.drawLine(self.mapper.p_left, int(y), self.width() - self.mapper.p_right, int(y))
            painter.setPen(QColor(self.theme.get("text_label", "#808080")))
            painter.drawText(self.width() - self.mapper.p_right + 5, int(y + 5), f"{curr_tick:.{precision}f}")
            curr_tick += nice_inc

        # Horizontal Date Axis
        last_year, last_month = -1, -1
        for i, idx in enumerate(range(start_idx, end_idx)):
            d = self.df.index[idx]
            if d.year != last_year or d.month != last_month:
                x = self.mapper.index_to_x(i)
                painter.setPen(QPen(QColor(self.theme.get("grid", "#3c3c3c")), 1))
                painter.drawLine(int(x), self.mapper.p_top, int(x), self.height() - self.mapper.p_bottom)
                is_year = d.year != last_year
                painter.setPen(QColor(self.theme.get("text_main" if is_year else "text_label", "#ffffff")))
                painter.drawText(int(x - 15), int(self.height() - self.mapper.p_bottom + 15), d.strftime('%Y' if is_year else '%b'))
                last_year, last_month = d.year, d.month

    def _draw_price_series(self, painter: QPainter, visible_df):
        bw = self.mapper.get_bar_width()
        is_ha = self.chart_type == ChartType.HEIKEN_ASHI
        opens = visible_df['HA_Open' if is_ha else 'Open'].values
        highs = visible_df['HA_High' if is_ha else 'High'].values
        lows = visible_df['HA_Low' if is_ha else 'Low'].values
        closes = visible_df['HA_Close' if is_ha else 'Close'].values
        
        if self.chart_type == ChartType.LINE:
            painter.setPen(QPen(QColor(self.theme.get("cd_buy", "#00ffff")), 2))
            for i in range(len(visible_df) - 1):
                p1 = QPointF(self.mapper.index_to_x(i), self.mapper.price_to_y(closes[i]))
                p2 = QPointF(self.mapper.index_to_x(i+1), self.mapper.price_to_y(closes[i+1]))
                painter.drawLine(p1, p2)
        else:
            for i in range(len(visible_df)):
                x = self.mapper.index_to_x(i)
                color = QColor(self.theme.get("bull" if closes[i] >= opens[i] else "bear", "#00c800"))
                painter.setPen(QPen(color, 1))
                painter.setBrush(color)
                
                yh, yl = self.mapper.price_to_y(highs[i]), self.mapper.price_to_y(lows[i])
                yo, yc = self.mapper.price_to_y(opens[i]), self.mapper.price_to_y(closes[i])
                
                if self.chart_type == ChartType.OHLC:
                    painter.drawLine(QPointF(x, yh), QPointF(x, yl))
                    painter.drawLine(QPointF(x - bw * 0.3, yo), QPointF(x, yo))
                    painter.drawLine(QPointF(x, yc), QPointF(x + bw * 0.3, yc))
                else:
                    painter.drawLine(QPointF(x, yh), QPointF(x, yl))
                    painter.drawRect(QRectF(x - bw * 0.35, min(yo, yc), bw * 0.7, max(1, abs(yo - yc))))

    def _draw_bollinger_bands(self, painter: QPainter, visible_df):
        if 'bb_middle' not in visible_df.columns: return
        
        # Middle
        painter.setPen(QPen(QColor(self.theme.get("bb_mid", "#ffaa00")), 1, Qt.DashLine))
        for i in range(len(visible_df) - 1):
            v1, v2 = visible_df['bb_middle'].iloc[i], visible_df['bb_middle'].iloc[i+1]
            if not np.isnan(v1) and not np.isnan(v2):
                painter.drawLine(QPointF(self.mapper.index_to_x(i), self.mapper.price_to_y(v1)),
                                 QPointF(self.mapper.index_to_x(i+1), self.mapper.price_to_y(v2)))
        
        # Upper/Lower
        for std in self.bb_std_devs:
            for suffix, col_key in [('upper', 'bb_upper'), ('lower', 'bb_lower')]:
                col = f"{col_key}_{std}"
                if col in visible_df.columns:
                    painter.setPen(QPen(QColor(self.theme.get(f"bb_{suffix}", "#00aaff")), 1))
                    for i in range(len(visible_df) - 1):
                        v1, v2 = visible_df[col].iloc[i], visible_df[col].iloc[i+1]
                        if not np.isnan(v1) and not np.isnan(v2):
                            painter.drawLine(QPointF(self.mapper.index_to_x(i), self.mapper.price_to_y(v1)),
                                             QPointF(self.mapper.index_to_x(i+1), self.mapper.price_to_y(v2)))

    def _draw_td_sequential(self, painter: QPainter, visible_df):
        scs = visible_df['setup_count'].values
        sts = visible_df['setup_type'].values
        perfs = visible_df['perfected'].values
        ccs = visible_df['countdown_count'].values
        cts = visible_df['countdown_type'].values
        rhs, rls = visible_df['High'].values, visible_df['Low'].values
        
        for i in range(len(visible_df)):
            x = self.mapper.index_to_x(i)
            yhr, ylr = self.mapper.price_to_y(rhs[i]), self.mapper.price_to_y(rls[i])
            
            if scs[i] > 0:
                painter.setFont(self.font_td_setup)
                color = self.theme.get("perfected", "#ff00ff") if perfs[i] else \
                        self.theme.get("setup_buy" if sts[i] == 'buy' else "setup_sell", "#00ff00")
                painter.setPen(QColor(color))
                painter.drawText(QRectF(x - 10, (ylr + 5 if sts[i] == 'buy' else yhr - 20), 20, 15), Qt.AlignCenter, str(scs[i]))
            
            if ccs[i] > 0:
                painter.setFont(self.font_td_cd)
                color = self.theme.get("cd_buy" if cts[i] == 'buy' else "cd_sell", "#00ffff")
                painter.setPen(QColor(color))
                painter.drawText(QRectF(x - 15, (ylr + 20 if cts[i] == 'buy' else yhr - 40), 30, 20), 
                                 Qt.AlignCenter, "13+" if ccs[i] == 12.5 else str(int(ccs[i])))

    def _draw_header(self, painter: QPainter):
        if self.df is None or self.df.empty:
            return
            
        last_row = self.df.iloc[-1]
        painter.setPen(QColor(self.theme.get("text_main", "#ffffff")))
        painter.setFont(self.font_main)
        
        # Main Header with Interval
        symbol = self.metadata.get('symbol', '')
        name = self.metadata.get('full_name', '')
        exchange = self.metadata.get('exchange', '')
        currency = self.metadata.get('currency', '')
        interval = self.metadata.get('interval', '')
        
        header_txt = f"{name} ({symbol}) - {exchange} - {currency}"
        if interval:
            header_txt += f" - [{interval}]"
            
        painter.drawText(20, 25, header_txt)

        # Indicator Legend
        painter.setFont(self.font_labels)
        curr_x = 20
        y_pos = 45
        
        # OHLC Latest
        o, h, l, c = last_row['Open'], last_row['High'], last_row['Low'], last_row['Close']
        is_bull = c >= o
        
        for label, val, color_key in [
            ("O", o, "text_main"),
            ("H", h, "bull"),
            ("L", l, "bear"),
            ("C", c, "bull" if is_bull else "bear")
        ]:
            painter.setPen(QColor(self.theme.get("text_label", "#808080")))
            painter.drawText(curr_x, y_pos, f"{label}:")
            curr_x += self.fm_labels.horizontalAdvance(f"{label}:")
            
            painter.setPen(QColor(self.theme.get(color_key, "#ffffff")))
            val_txt = f"{val:.2f} "
            painter.drawText(curr_x, y_pos, val_txt)
            curr_x += self.fm_labels.horizontalAdvance(val_txt)

        if self.show_bb or self.show_td:
            painter.setPen(QColor(self.theme.get("text_label", "#808080")))
            painter.drawText(curr_x, y_pos, "• ")
            curr_x += self.fm_labels.horizontalAdvance("• ")
        
        if self.show_bb:
            painter.setPen(QColor(self.theme.get("text_label", "#808080")))
            painter.drawText(curr_x, y_pos, "BB: ")
            curr_x += self.fm_labels.horizontalAdvance("BB: ")
            
            # Basis
            val = last_row.get('bb_middle', np.nan)
            txt = f"Basis {val:.2f} " if not np.isnan(val) else "Basis - "
            painter.setPen(QColor(self.theme.get("bb_mid", "#ffffff")))
            painter.drawText(curr_x, y_pos, txt)
            curr_x += self.fm_labels.horizontalAdvance(txt)
            
            # Bands (all enabled stds)
            for std in self.bb_std_devs:
                u_val = last_row.get(f'bb_upper_{std}', np.nan)
                u_txt = f"Up({std}) {u_val:.2f} " if not np.isnan(u_val) else f"Up({std}) - "
                painter.setPen(QColor(self.theme.get("bb_upper", "#ffffff")))
                painter.drawText(curr_x, y_pos, u_txt)
                curr_x += self.fm_labels.horizontalAdvance(u_txt)
                
                l_val = last_row.get(f'bb_lower_{std}', np.nan)
                l_txt = f"Lo({std}) {l_val:.2f} " if not np.isnan(l_val) else f"Lo({std}) - "
                painter.setPen(QColor(self.theme.get("bb_lower", "#ffffff")))
                painter.drawText(curr_x, y_pos, l_txt)
                curr_x += self.fm_labels.horizontalAdvance(l_txt)
            
            if self.show_td:
                painter.setPen(QColor(self.theme.get("text_label", "#808080")))
                painter.drawText(curr_x, y_pos, "• ")
                curr_x += self.fm_labels.horizontalAdvance("• ")

        if self.show_td:
            painter.setPen(QColor(self.theme.get("text_label", "#808080")))
            painter.drawText(curr_x, y_pos, "TD: ")
            curr_x += self.fm_labels.horizontalAdvance("TD: ")
            
            s_count = last_row.get('setup_count', 0)
            s_type = last_row.get('setup_type')
            if s_count > 0:
                txt = f"Setup({s_type}) {s_count} "
                color_key = "setup_buy" if s_type == 'buy' else "setup_sell"
                painter.setPen(QColor(self.theme.get(color_key, "#ffffff")))
                painter.drawText(curr_x, y_pos, txt)
                curr_x += self.fm_labels.horizontalAdvance(txt)
                
            c_count = last_row.get('countdown_count', 0)
            c_type = last_row.get('countdown_type')
            if c_count > 0:
                disp_c = "13+" if c_count == 12.5 else str(int(c_count))
                txt = f"CD({c_type}) {disp_c} "
                color_key = "cd_buy" if c_type == 'buy' else "cd_sell"
                painter.setPen(QColor(self.theme.get(color_key, "#ffffff")))
                painter.drawText(curr_x, y_pos, txt)
                curr_x += self.fm_labels.horizontalAdvance(txt)

    def _draw_crosshairs(self, painter: QPainter):
        x = self.mouse_pos.x()
        if self.mapper.p_left <= x <= self.width() - self.mapper.p_right:
            bw = self.mapper.get_bar_width()
            idx_rel = int((x - self.mapper.p_left) / bw)
            idx_act = max(0, len(self.df) - self.scroll_offset - self.visible_bars) + idx_rel
            
            if 0 <= idx_act < len(self.df):
                sx = self.mapper.index_to_x(idx_rel)
                sy = self.mapper.price_to_y(self.df['Close'].iloc[idx_act])
                painter.setPen(QPen(QColor(self.theme.get("crosshair", "#969696")), 1, Qt.DashLine))
                painter.drawLine(QPointF(sx, self.mapper.p_top), QPointF(sx, self.height() - self.mapper.p_bottom))
                painter.drawLine(QPointF(self.mapper.p_left, sy), QPointF(self.width() - self.mapper.p_right, sy))