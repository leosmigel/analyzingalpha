from datetime import datetime, timedelta
import backtrader as bt
from positions.securities import get_security_data, get_securities_data,\
                                                    get_sector_tickers

# todo merge get_security_data and get_securities_data

START_DATE = '2010-01-01'
END_DATE = '2019-12-31'
START = datetime.strptime(START_DATE, '%Y-%m-%d')
END = datetime.strptime(END_DATE, '%Y-%m-%d')
BENCHMARK_TICKER = 'SPY'


class Strategy(bt.Strategy):
    params = dict(
        num_positions=2.0,
        stop_loss=0.05,
        trail=False,
        when=bt.timer.SESSION_START,
        timer=True,
        monthdays=[1],
        monthcarry=True,
    )

    def __init__(self):
        self.d_with_len = []
        self.orders = {}
        self.securities = self.datas[1:]
        self.rebalance_date = None
        self.add_timer(
            when=self.p.when,
            monthdays=self.p.monthdays,
            monthcarry=self.p.monthcarry
        )
        for d in self.datas:
            self.orders[d] = []

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
        # Sell all securities that are above their target allocation
        # but cancel associated stop losses first
        self.rebalance_date = self.data.datetime.date(ago=0)
        positions = len(self.d_with_len)
        target = (self.broker.get_value() / positions)
        for d in self.d_with_len:
            value = self.getposition(d).size * d.close[0]

            if value > target:
                sell_size = (value - target) // d.close[0]
                if sell_size >= 1:
                    stop_size = 0
                    for o in self.orders[d]:
                        if o and o.status == o.Accepted and \
                                (o.getordername() == 'Stop' or
                                 o.getordername() == 'StopTrail') and \
                                stop_size < sell_size:
                            self.cancel(o)
                            stop_size += o.size
                    if stop_size == sell_size:
                        sell_order = self.sell(d,
                                               size=sell_size,
                                               exectype=bt.Order.Market,
                                               transmit=True,
                                               ticker=d.p.name)
                    else:
                        sell_order = self.sell(d,
                                               size=sell_size,
                                               exectype=bt.Order.Market,
                                               transmit=False,
                                               ticker=d.p.name)
                        stop_price = (1.0 - self.p.stop_loss) * d.close[0]

                        # stop_size is negative and sell_size is postive
                        stop_delta = stop_size * -1 - sell_size
                        if self.p.trail:
                            stop_order = self.sell(d,
                                                   size=stop_delta,
                                                   exectype=bt.Order.StopTrail,
                                                   trailpercent=self.p.stop_loss,
                                                   transmit=True,
                                                   parent=sell_order,
                                                   ticker=d.p.name)
                        else:
                            stop_order = self.sell(d,
                                                   price=stop_price,
                                                   size=stop_delta,
                                                   exectype=bt.Order.Stop,
                                                   transmit=True,
                                                   parent=sell_order,
                                                   ticker=d.p.name)

                        self.orders[d].append(sell_order)
                        self.orders[d].append(stop_order)


    def rebalance_buy(self):
        # Buy all securities that are below their target allocation
        # and attach a stop loss.
        positions = len(self.d_with_len)
        target = (self.broker.get_value() / positions)
        for d in self.d_with_len:
            value = self.getposition(d).size * d.close[0]
            if target > value:
                buy_size = (target - value) // d.close[0]
                stop_price = (1.0 - self.p.stop_loss) * d.close[0]
                buy_order = self.buy(d,
                                     size=buy_size,
                                     exectype=bt.Order.Market,
                                     transmit=False,
                                     ticker=d.p.name)
                if self.p.trail:
                    stop_order = self.sell(d,
                                           size=buy_size,
                                           exectype=bt.Order.StopTrail,
                                           trailpercent=self.p.stop_loss,
                                           transmit=True,
                                           parent=buy_order,
                                           ticker=d.p.name)
                else:
                    stop_order = self.sell(d,
                                           price=stop_price,
                                           size=buy_size,
                                           exectype=bt.Order.Stop,
                                           transmit=True,
                                           parent=buy_order,
                                           ticker=d.p.name)

                self.orders[d].append(buy_order)
                self.orders[d].append(stop_order)

    def stop(self):
        self.ending_value = round(self.broker.get_value(), 2)
        self.PnL = round(self.ending_value - startcash, 2)

startcash = 10000
cerebro = bt.Cerebro(stdstats=False, optreturn=False)

# Add Benchmark (datas[0])
benchmark = get_security_data(BENCHMARK_TICKER, START, END)
benchdata = bt.feeds.PandasData(dataname=benchmark, name='SPY', plot=False)
cerebro.adddata(benchdata)

# Add Securities (datas[1:])
tickers = get_sector_tickers()
# tickers = get_sp500_tickers()
securities = get_securities_data(tickers, START_DATE, END_DATE)

# Add securities as datas1:
for ticker, data in securities.groupby(level=0):
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
cerebro.optstrategy(Strategy, stop_loss=(0.05))


# Add observers

cerebro.addobserver(bt.observers.CashValue)
cerebro.addobserver(bt.observers.Benchmark,
                     data=benchdata,
                     _doprenext=True,
                     timeframe=bt.TimeFrame.NoTimeFrame)
cerebro.addobserver(bt.observers.Trades)
cerebro.addobserver(bt.observers.BuySell)

# Add analyzers
cerebro.addanalyzer(bt.analyzers.Returns)
cerebro.addanalyzer(bt.analyzers.DrawDown)

# Run cerebro
opt_results = cerebro.run(tradehistory=False)

# Generate results list
final_results_list = []
    
for run in opt_results:
    for strategy in run:
        value = strategy.ending_value
        PnL = strategy.PnL
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

cerebro.plot()