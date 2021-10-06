import os, sys

sys.path.append('/home/leosmigel/Development/workspace')
import pandas as pd
import numpy as np
import backtrader as bt
import setup_psql_environment
from models import Security, SecurityPrice
from scipy.stats import linregress
from collections import defaultdict
from tabulate import tabulate
import PyQt5
import matplotlib

matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import backtrader.plot
from matplotlib.pyplot import figure
from datetime import datetime

START_DATE = '1999-01-01'
START = datetime.strptime(START_DATE, '%Y-%m-%d')
END_DATE = '2018-12-31'
END = datetime.strptime(END_DATE, '%Y-%m-%d')
ETF_TICKERS = ['XLB', 'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLU', 'XLV', 'XLY']


def momentum_func(self, price_array):
    r = np.log(price_array)
    slope, _, rvalue, _, _ = linregress(np.arange(len(r)), r)
    annualized = (1 + slope) ** 252
    return (annualized * (rvalue ** 2))


class Momentum(bt.ind.OperationN):
    lines = ('trend',)
    params = dict(period=90)
    func = momentum_func


class Strategy(bt.Strategy):
    params = dict(
        momentum=Momentum,
        momentum_period=180,
        num_positions=2,
        when=bt.timer.SESSION_START,
        timer=True,
        monthdays=[1],
        monthcarry=True,
        printlog=True
    )

    def log(self, txt, dt=None, doprint=False):
        ''' Logging function fot this strategy'''
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.i = 0
        self.securities = self.datas[1:]
        self.inds = {}

        self.add_timer(
            when=self.p.when,
            monthdays=self.p.monthdays,
            monthcarry=self.p.monthcarry
        )

        for security in self.securities:
            self.inds[security] = self.p.momentum(security,
                                                  period=self.p.momentum_period)

    def notify_timer(self, timer, when, *args, **kwargs):
        if self._getminperstatus() < 0:
            self.rebalance()

    def rebalance(self):
        rankings = list(self.securities)
        rankings.sort(key=lambda s: self.inds[s][0], reverse=True)
        pos_size = 1 / self.p.num_positions

        # Sell stocks no longer meeting ranking filter.
        for i, d in enumerate(rankings):
            if self.getposition(d).size:
                if i > self.p.num_positions:
                    self.close(d)

        # Buy and rebalance stocks with remaining cash
        for i, d in enumerate(rankings[:self.p.num_positions]):
            self.order_target_percent(d, target=pos_size)

    def next(self):
        self.notify_timer(self, self.p.timer, self.p.when)

    def stop(self):
        self.log('| %2d | %2d |  %.2f |' %
                 (self.p.momentum_period,
                  self.p.num_positions,
                  self.broker.getvalue()),
                 doprint=True)


if __name__ == '__main__':
    cerebro = bt.Cerebro()

    # Create an SQLAlchemy conneciton to PostgreSQL and get ETF data
    db = setup_psql_environment.get_database()
    session = setup_psql_environment.get_session()

    query = session.query(SecurityPrice, Security.ticker).join(Security). \
        filter(SecurityPrice.date >= START_DATE). \
        filter(SecurityPrice.date <= END_DATE). \
        filter(Security.code == 'ETF').statement

    dataframe = pd.read_sql(query,
                            db,
                            index_col=['ticker', 'date'],
                            parse_dates=['date'])
    dataframe.sort_index(inplace=True)
    dataframe = dataframe[['adj_open',
                           'adj_high',
                           'adj_low',
                           'adj_close',
                           'adj_volume']]
    dataframe.columns = ['open', 'high', 'low', 'close', 'volume']

    # Add Spy as datas0
    spy = dataframe.loc['SPY']
    benchdata = bt.feeds.PandasData(dataname=spy, name='spy', plot=True)
    cerebro.adddata(benchdata)
    dataframe.drop('SPY', level='ticker', inplace=True)

    # Add securities as datas1:
    for ticker, data in dataframe.groupby(level=0):
        if ticker in ETF_TICKERS:
            print(f"Adding ticker: {ticker}")
            data = bt.feeds.PandasData(dataname=data.droplevel(level=0),
                                       name=ticker,
                                       plot=False)
            data.plotinfo.plotmaster = benchdata
            cerebro.adddata(data)

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Add Strategy
    stop = len(ETF_TICKERS) + 1
    cerebro.optstrategy(Strategy,
                        momentum_period=range(50, 300, 50),
                        num_positions=range(1, len(ETF_TICKERS) + 1))

    # Run the strategy. Results will be output from stop.
    cerebro.run(stdstats=False, tradehistory=False)
