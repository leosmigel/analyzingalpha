from datetime import datetime, timedelta
import math
import backtrader as bt
from positions.securities import get_security_data, get_securities_data,\
                                                    get_sp500_tickers
from indicators.momentum import momentum

START_DATE = '2010-01-01'
END_DATE = '2019-12-31'
START = datetime.strptime(START_DATE, '%Y-%m-%d')
END = datetime.strptime(END_DATE, '%Y-%m-%d')
BENCHMARK_TICKER = 'SPY'

EXCLUDE_WINDOW = 10
MOMENTUM_WINDOW = 90
MINIMUM_PERIOD = MOMENTUM_WINDOW + EXCLUDE_WINDOW
POSITIONS = 20
USE_ATR = False

class Momentum(bt.ind.OperationN):
    lines = ('trend',)
    params = dict(period=MINIMUM_PERIOD,
                  exclude_window=EXCLUDE_WINDOW)
    func = momentum

    def __init__(self):
        self.addminperiod(self.p.period)
        self.exclude_window = self.p.exclude_window


class Strategy(bt.Strategy):
    params = dict(
        num_positions=POSITIONS,
        use_atr=USE_ATR,
        rrr=2.0,
        stop_loss=0.05,
        atr_factor=3.0,
        when=bt.timer.SESSION_START,
        timer=True,
        weekdays=[1],
        weekcarry=True,
        momentum=Momentum,
        momentum_period=MINIMUM_PERIOD
    )

    def __init__(self):
        self.d_with_len = []
        self.orders = {}
        self.inds = {}
        self.rebalance_date = None
        self.add_timer(
            when=self.p.when,
            weekdays=self.p.weekdays,
            weekcarry=self.p.weekcarry
        )
        for d in self.datas[1:]:
            self.orders[d] = []
            self.inds[d] = {}
            self.inds[d]['momentum'] = self.p.momentum(d,
                                                       period=MINIMUM_PERIOD,
                                                       plot=False)
            self.inds[d]['atr'] = bt.indicators.ATR(d,
                                                    period=14)

    def prenext(self):
        # Add data for datas that meet preprocessing requirements
        # And call next even though data is not available for all tickers
        self.d_with_len = [d for d in self.datas[1:] if len(d)]

        if len(self.d_with_len) >= self.p.num_positions:
            self.next()

    def nextstart(self):
        # This is only called once when all data is present
        # So we are not unnecessarily calculating d_with_len
        self.d_with_len = self.datas[1:]
        self.next()
        print("All datas loaded")
    
    def next(self):
        if self.rebalance_date:
            today = self.data.datetime.date(ago=0)
            buy_date = self.rebalance_date + timedelta(days=1)
            if today == buy_date:
                self.rebalance_buy()

    def notify_timer(self, timer, when, *args, **kwargs):
        if len(self.d_with_len) >= self.p.num_positions:
            self.rebalance_sell()

    def rebalance_sell(self):
        self.rebalance_date = self.data.datetime.date(ago=0)
        self.rankings = list(self.d_with_len)
        self.rankings.sort(key=lambda s: self.inds[s]['momentum'][0],
              
                           reverse=True)
        for i, d in enumerate(self.rankings):
            if self.getposition(d).size != 0:
                if i >= self.p.num_positions:
                    self.close(d, ticker=d.p.name)
                    for o in self.orders[d]:
                        if o and o.status == o.Accepted and \
                                (o.getordername() == 'Stop' or
                                 o.getordername() == 'Limit'):
                            self.cancel(o)

        # Rank according to momentum and return stock list
        # Buy stocks with remaining cash

    def rebalance_buy(self):
        positions = 0
        for d in self.datas:
            if self.getposition(d).size != 0:
                positions += 1
        
        if positions < self.p.num_positions:
            pos_value = self.broker.get_cash() / (self.p.num_positions - positions)
            for i, d in enumerate(self.rankings[:self.p.num_positions]):
                if self.getposition(d).size == 0 and \
                        not math.isnan(self.inds[d]['momentum'][0]) > 0 and \
                        pos_value > d.close[0]:
                    buy_size = pos_value // d.close[0]

                    buy_order = self.buy(d,
                                         size=buy_size,
                                         transmit=False,
                                         ticker=d.p.name)
                    
                    if self.p.use_atr:
                        sell_price = d.close[0] + self.inds[d]['atr'][0] * self.p.atr_factor * self.p.rrr
                        stop_price = d.close[0] - self.inds[d]['atr'][0] * self.p.atr_factor
                        stop_loss = (self.inds[d]['atr'][0] * self.p.atr_factor) / d.close[0]
                    else:
                        sell_price = (1.0 + self.p.stop_loss * self.p.rrr) * d.close[0]
                        stop_price = (1.0 - self.p.stop_loss) * d.close[0]
                        stop_loss = self.p.stop_loss

                    sell_order = self.sell(d,
                                            price=sell_price,
                                            size=buy_order.size,
                                            exectype=bt.Order.Limit,
                                            transmit=False,
                                            parent=buy_order,
                                            ticker=d.p.name)

                    stop_order = self.sell(d,
                                            price=stop_price,
                                            size=buy_order.size,
                                            exectype=bt.Order.Stop,
                                            transmit=True,
                                            parent=buy_order,
                                            ticker=d.p.name)
                    
                    self.orders[d].append(sell_order)
                    self.orders[d].append(stop_order)

    def stop(self):
        self.ending_value = round(self.broker.get_value(), 2)
        self.PnL = round(self.ending_value - startcash, 2)
 
if __name__ == '__main__':
    startcash = 10000
    cerebro = bt.Cerebro(stdstats=False, optreturn=False)

    # Add Benchmark (datas[0])
    benchmark = get_security_data(BENCHMARK_TICKER, START, END)
    benchdata = bt.feeds.PandasData(dataname=benchmark,
                                    name='SPY',
                                    plot=False)
    cerebro.adddata(benchdata)

    # Add Securities (datas[1:])
    tickers = get_sp500_tickers()
    securities = get_securities_data(tickers, START_DATE, END_DATE)

    # Add securities as datas1:
    for ticker, data in securities.groupby(level=0):
        if len(data) < MINIMUM_PERIOD:
            print(f"Skipping: ticker {ticker} with length{len(data)} \
                does not meet the minimum length of {MINIMUM_PERIOD}.")
            continue
        
        print(f"Adding ticker: {ticker}.")
        d = bt.feeds.PandasData(dataname=data.droplevel(level=0),
                                name=ticker,
                                plot=False)
        d.plotinfo.plotmaster = benchdata
        d.plotinfo.plotlinelabels = True

        cerebro.adddata(d)

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Add Strategy
    if USE_ATR:
        cerebro.optstrategy(Strategy,
                            rrr=(1, 2, 3, 4),
                            atr_factor=(1, 2, 3, 4, 5))
    else:
        cerebro.optstrategy(Strategy,
                            rrr=(1, 2, 3, 4),
                            stop_loss=(0.05, 0.10, 0.15, 0.20, 0.25))

    # Add observers & analyzers
    cerebro.addobserver(bt.observers.CashValue)
    cerebro.addobserver(bt.observers.Benchmark,
                        data=benchdata,
                        _doprenext=True,
                        timeframe=bt.TimeFrame.NoTimeFrame)
    cerebro.addanalyzer(bt.analyzers.Returns)
    cerebro.addanalyzer(bt.analyzers.DrawDown)

    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.BuySell)

    # Analyze the trades
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
   
    # Run optimization
    opt_results = cerebro.run(tradehistory=False)

    # Generate results list
    final_results_list = []
        
    for run in opt_results:
        for strategy in run:
            value = strategy.ending_value
            PnL = strategy.PnL
            if USE_ATR:
                stop_loss = strategy.p.atr_factor
            else:
                stop_loss = strategy.p.stop_loss
            rrr = strategy.p.rrr
            trades = strategy.analyzers.trades.get_analysis()
            total_trades = trades.total.closed
            total_won = trades.won.total
            perc_win = total_won / total_trades
            drawdown = strategy.analyzers.drawdown.get_analysis()['max']['drawdown']
            final_results_list.append([rrr, perc_win, stop_loss, PnL, drawdown])
            
            print(f"Strategy Total Return: {strategy.analyzers.returns.get_analysis()['rtot']}")



    #Sort Results List
    by_PnL = sorted(final_results_list, key=lambda x: x[3], reverse=True)
    by_win = sorted(final_results_list, key=lambda x: x[1], reverse=True)

    #Print results
    print('Results: Ordered by Profit:')
    for result in by_PnL:
        print('| RRR | Win% | Stop | PnL | Drawdown|')
        print('| {}  | {}%  | {} | {} | {}'.format(
            result[0],
            round(result[1], 2),
            result[2],
            round(result[3], 2),
            round(result[4], 2)))

    print('Results: Ordered by Win%:')
    for result in by_win:
        print('| RRR | Win% | Stop | PnL | Drawdown|')
        print('| {}  | {}%  | {} | {} | {}'.format(
            result[0],
            round(result[1], 2),
            result[2],
            round(result[3], 2),
            round(result[4], 2)))