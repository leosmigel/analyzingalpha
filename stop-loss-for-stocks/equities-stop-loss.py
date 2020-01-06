from datetime import datetime
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
        stop_loss=0.05,
        atr_factor=3.0,
        trail=True,
        when=bt.timer.SESSION_START,
        timer=True,
        monthdays=[1],
        monthcarry=True,
        momentum=Momentum,
        momentum_period=MINIMUM_PERIOD
    )

    def __init__(self):
        self.d_with_len = []
        self.orders = {}
        self.inds = {}
        self.add_timer(
            when=self.p.when,
            weekdays=self.p.monthdays,
            weekcarry=self.p.monthcarry
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

    def notify_timer(self, timer, when, *args, **kwargs):
        if len(self.d_with_len) >= self.p.num_positions:
            self.rebalance()

    def rebalance(self):
        self.rankings = list(self.d_with_len)
        self.rankings.sort(key=lambda s: self.inds[s]['momentum'][0],
                           reverse=True)

        # Close all positions and cancel associated stop losses
        # that are no longer a top N momentum position
        positions = 0
        for i, d in enumerate(self.rankings):
            if self.getposition(d).size != 0:
                positions += 1
                if i >= self.p.num_positions:
                    self.close(d, ticker=d.p.name)
                    positions -= 1
                    for o in self.orders[d]:
                        if o and o.status == o.Accepted and \
                                (o.getordername() == 'Stop' or
                                 o.getordername() == 'StopTrail'):
                            self.cancel(o)

        # Rank according to momentum and return stock list
        # Buy stocks with remaining cash

        # todo buying top N vs X
        if positions < self.p.num_positions:
            pos_value = self.broker.get_cash() / (self.p.num_positions - positions)
            for i, d in enumerate(self.rankings[:self.p.num_positions]):
                if self.getposition(d).size == 0 and \
                        self.inds[d]['momentum'][0] > 0 and \
                        pos_value > d.close[0]:
                    buy_size = pos_value // d.close[0]

                    buy_order = self.buy(d,
                                         size=buy_size,
                                         transmit=False,
                                         ticker=d.p.name)
                    
                    if self.p.use_atr:
                        stop_price = d.close[0] - self.inds[d]['atr'][0] * self.p.atr_factor
                        stop_loss = (self.inds[d]['atr'][0] * self.p.atr_factor) / d.close[0]
                    else:
                        stop_price = (1.0 - self.p.stop_loss) * d.close[0]
                        stop_loss = self.p.stop_loss
                    

                    if self.p.trail:
                        stop_order = self.sell(d,
                                               size=buy_order.size,
                                               exectype=bt.Order.StopTrail,
                                               trailpercent=stop_loss,
                                               transmit=True,
                                               parent=buy_order,
                                               ticker=d.p.name)
                    else:
                        stop_order = self.sell(d,
                                               price=stop_price,
                                               size=buy_order.size,
                                               exectype=bt.Order.Stop,
                                               transmit=True,
                                               parent=buy_order,
                                               ticker=d.p.name)
                    
                    self.orders[d].append(stop_order)

    def stop(self):
        self.ending_value = round(self.broker.get_value(), 2)
        self.PnL = round(self.ending_value - startcash, 2)
    

if __name__ == '__main__':
    startcash = 10000
    #cerebro = bt.Cerebro(stdstats=False, optreturn=False, maxcpus=4)
    cerebro = bt.Cerebro(stdstats=False, optreturn=False)

    # Add Benchmark (datas[0])
    benchmark = get_security_data(BENCHMARK_TICKER, START, END)
    benchdata = bt.feeds.PandasData(dataname=benchmark, name='SPY', plot=False)
    cerebro.adddata(benchdata)

    # Add Securities (datas[1:])
    tickers = get_sp500_tickers()
    securities = get_securities_data(tickers, START_DATE, END_DATE)

    # Add securities as datas1:
    for ticker, data in securities.groupby(level=0):
        if len(data) < MINIMUM_PERIOD:
            print(f"Skipping: ticker {ticker} with length {len(data)} does not meet the minimum length of {MINIMUM_PERIOD}.")
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
    #cerebro.addstrategy(Strategy)
    if USE_ATR:
        cerebro.optstrategy(Strategy, atr_factor=(1, 2, 3, 4, 5))
    else:
        cerebro.optstrategy(Strategy, stop_loss=(0.95))

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
            drawdown = strategy.analyzers.drawdown.get_analysis()['max']['drawdown']
            final_results_list.append([stop_loss, PnL, drawdown])
            print(f"Strategy Total Return: {strategy.analyzers.returns.get_analysis()['rtot']}")

    #Sort Results List
    by_stop = sorted(final_results_list, key=lambda x: x[0])
    by_PnL = sorted(final_results_list, key=lambda x: x[1], reverse=True)

    #Print results
    print('Results: Ordered by Stop Loss:')
    for result in by_stop:
        print('Stop: {}, PnL: {}, Drawdown: {}'.format(result[0], result[1], result[2]))
    print('Results: Ordered by Profit:')
    for result in by_PnL:
        print('Stop: {}, PnL: {} Drawdown: {}'.format(result[0], result[1], result[2]))