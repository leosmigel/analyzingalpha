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
            self.inds[security] = self.p.momentum(security, period=self.p.momentum_period)

    def notify_timer(self, timer, when, *args, **kwargs):
        if self._getminperstatus() < 0:
            self.rebalance()

    def rebalance(self):
        rankings = list(self.securities)
        rankings.sort(key=lambda s: self.inds[s][0])
        num_securities = len(rankings)
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
                 (self.p.momentum_period, self.p.num_positions,  self.broker.getvalue()), doprint=True)




class trade_list(bt.Analyzer):

    def get_analysis(self):

        return self.trades

    def __init__(self):

        self.trades = []
        self.cumprofit = 0.0

    def notify_trade(self, trade):

        if trade.isclosed:

            brokervalue = self.strategy.broker.getvalue()

            dir = 'short'
            if trade.history[0].event.size > 0: dir = 'long'

            pricein = trade.history[len(trade.history) - 1].status.price
            priceout = trade.history[len(trade.history) - 1].event.price
            datein = bt.num2date(trade.history[0].status.dt)
            dateout = bt.num2date(trade.history[len(trade.history) - 1].status.dt)
            if trade.data._timeframe >= bt.TimeFrame.Days:
                datein = datein.date()
                dateout = dateout.date()

            pcntchange = 100 * priceout / pricein - 100
            pnl = trade.history[len(trade.history) - 1].status.pnlcomm
            pnlpcnt = 100 * pnl / brokervalue
            barlen = trade.history[len(trade.history) - 1].status.barlen
            pbar = pnl / barlen
            self.cumprofit += pnl

            size = value = 0.0
            for record in trade.history:
                if abs(size) < abs(record.status.size):
                    size = record.status.size
                    value = record.status.value

            highest_in_trade = max(trade.data.high.get(ago=0, size=barlen + 1))
            lowest_in_trade = min(trade.data.low.get(ago=0, size=barlen + 1))
            hp = 100 * (highest_in_trade - pricein) / pricein
            lp = 100 * (lowest_in_trade - pricein) / pricein
            if dir == 'long':
                mfe = hp
                mae = lp
            if dir == 'short':
                mfe = -lp
                mae = -hp

            self.trades.append({'ref': trade.ref, 'ticker': trade.data._name, 'dir': dir,
                                'datein': datein, 'pricein': pricein, 'dateout': dateout, 'priceout': priceout,
                                'chng%': round(pcntchange, 2), 'pnl': pnl, 'pnl%': round(pnlpcnt, 2),
                                'size': size, 'value': value, 'cumpnl': self.cumprofit,
                                'nbars': barlen, 'pnl/bar': round(pbar, 2),
                                'mfe%': round(mfe, 2), 'mae%': round(mae, 2)})




if __name__ == '__main__':
    cerebro = bt.Cerebro()
    #cerebro.runonce = False
    #cerebro.preload = False

    # Create an SQLAlchemy conneciton to PostgreSQL and get ETF data
    db = setup_psql_environment.get_database()
    session = setup_psql_environment.get_session()

    query = session.query(SecurityPrice, Security.ticker).join(Security). \
        filter(SecurityPrice.date >= START_DATE). \
        filter(SecurityPrice.date <= END_DATE). \
        filter(Security.code == 'ETF').statement

    dataframe = pd.read_sql(query, db, index_col=['ticker', 'date'], parse_dates=['date'])
    dataframe.sort_index(inplace=True)
    dataframe = dataframe[['adj_open', 'adj_high', 'adj_low', 'adj_close', 'adj_volume']]
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
            data = bt.feeds.PandasData(dataname=data.droplevel(level=0), name=ticker, plot=False)
            data.plotinfo.plotmaster = benchdata
            cerebro.adddata(data)

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Add Strategy
    #cerebro.addstrategy(Strategy)
    stop = len(ETF_TICKERS) + 1
    cerebro.optstrategy(Strategy, momentum_period=range(50,300,50), num_positions=range(1,len(ETF_TICKERS) + 1))

    # Add analyzers
    #cerebro.addanalyzer(trade_list, _name='trade_list')

    cerebro.addanalyzer(bt.analyzers.Returns)
    cerebro.addanalyzer(bt.analyzers.TimeReturn, timeframe=bt.TimeFrame.Years, _name='strategy')
    cerebro.addanalyzer(bt.analyzers.TimeReturn, timeframe=bt.TimeFrame.Years, _name='spy', data=benchdata)
    cerebro.addobserver(bt.observers.Benchmark, timeframe=bt.TimeFrame.NoTimeFrame)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, riskfreerate=0.0, timeframe=bt.TimeFrame.Years)
    cerebro.addanalyzer(bt.analyzers.DrawDown)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer)
    cerebro.addanalyzer(bt.analyzers.SQN)
    cerebro.addanalyzer(bt.analyzers.Transactions)

    results = cerebro.run(stdstats=True, tradehistory=True)
    #trade_list = results[0].analyzers.trade_list.get_analysis()

    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    print(f"SQN: {results[0].analyzers.sqn.get_analysis()}")
    print(f"Sharpe: {results[0].analyzers.sharperatio.get_analysis()['sharperatio']:.3f}")
    print(f"Max Drawdown: {results[0].analyzers.drawdown.get_analysis()['max']['drawdown']:.2f}%")
    print(f"Annual Return: {results[0].analyzers.returns.get_analysis()['rnorm100']}")
    print(f"Total Return: {results[0].analyzers.returns.get_analysis()['rtot']}")
    # print(tabulate(trade_list, headers="keys"))

    strategy_return = results[0].analyzers.getbyname('strategy').get_analysis()
    benchmark_return = results[0].analyzers.getbyname('spy').get_analysis()

    #figure(num=0, figsize=(18, 9), dpi=80, facecolor='w', edgecolor='k')
    #cerebro.plot(iplot=False)
