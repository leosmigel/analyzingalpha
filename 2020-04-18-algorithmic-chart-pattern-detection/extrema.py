import pandas as pd
import numpy as np
import backtrader as bt
from scipy.signal import argrelextrema
from positions.securities import get_security_data


class Extrema(bt.Indicator):
    '''
    Find local price extrema. Also known as highs and lows.

        Formula:
        - https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.argrelextrema.html

        See also:
        - https://analyzingalpha.com/algorithmic-pattern-detection

        Aliases: None
        Inputs: high, low
        Outputs: he, le
        Params:
        - period N/A
    '''
    lines = 'lmax',  'lmin'

    def next(self):

        past_highs = np.array(self.data.high.get(ago=0, size=len(self)))
        past_lows = np.array(self.data.low.get(ago=0, size=len(self)))

        last_high_days = argrelextrema(past_highs, np.greater)[0] \
            if past_highs.size > 0 else None
        last_low_days = argrelextrema(past_lows, np.less)[0] \
            if past_lows.size > 0 else None

        last_high_day = last_high_days[-1] \
            if last_high_days.size > 0 else None
        last_low_day = last_low_days[-1] \
            if last_low_days.size > 0 else None

        last_high_price = past_highs[last_high_day] \
            if last_high_day else None
        last_low_price = past_lows[last_low_day] \
            if last_low_day else None

        if last_high_price:
            self.l.lmax[0] = last_high_price

        if last_low_price:
            self.l.lmin[0] = last_low_price
