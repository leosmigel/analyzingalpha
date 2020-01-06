from datetime import datetime
import backtrader as bt
from positions.securities import get_security_data


START_DATE = '2010-01-01'
END_DATE = '2019-12-31'
START = datetime.strptime(START_DATE, '%Y-%m-%d')
END = datetime.strptime(END_DATE, '%Y-%m-%d')
BENCHMARK_TICKER = 'SPY'


class Strategy(bt.Strategy):
    params = dict(
        num_positions=1.0,
        stop_loss=0.05,
        trail=False,
        when=bt.timer.SESSION_START,
        timer=True,
        monthdays=[1],
        monthcarry=True,
    )

    def __init__(self):
        self.d_with_len = []

        self.add_timer(
            when=self.p.when,
            weekdays=self.p.monthdays,
            weekcarry=self.p.monthcarry
        )

    def prenext(self):
        # Add data for datas that meet preprocessing requirements
        # And call next even though data is not available for all tickers
        self.d_with_len = [d for d in self.datas if len(d)]

        if len(self.d_with_len) >= self.p.num_positions:
            self.next()

    def nextstart(self):
        # This is only called once when all data is present
        # So we are not unnecessarily calculating d_with_len
        self.d_with_len = self.datas
        self.next()
        print("All datas loaded")

    def notify_timer(self, timer, when, *args, **kwargs):
        self.rebalance()

    def rebalance(self):
        for d in self.d_with_len:
            if self.getposition(d).size == 0:
                size = (self.broker.get_cash() / d.close[0]) / self.p.num_positions
                stop_price = (1.0 - self.p.stop_loss) * d.close[0]
                buy_order = self.buy(d, size=size, transmit=False)

                if self.p.trail:
                    self.sell(d,
                              size=buy_order.size,
                              exectype=bt.Order.StopTrail,
                              trailpercent=self.p.stop_loss,
                              transmit=True,
                              parent=buy_order)
                else:
                    self.sell(d,
                              price=stop_price,
                              size=buy_order.size,
                              exectype=bt.Order.Stop,
                              transmit=True,
                              parent=buy_order)

    def stop(self):
        self.ending_value = round(self.broker.get_value(), 2)
        self.PnL = round(self.ending_value - startcash, 2)


if __name__ == '__main__':

    startcash = 10000
    cerebro = bt.Cerebro(optreturn=False)

    # Add Benchmark
    benchmark = get_security_data(BENCHMARK_TICKER, START, END)
    benchdata = bt.feeds.PandasData(dataname=benchmark, name='SPY', plot=True)
    cerebro.adddata(benchdata)

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Add Strategy
    cerebro.optstrategy(Strategy, stop_loss=(0.05, 0.10, 0.15, 0.20, 0.25, 0.30))


    # Add observers

    cerebro.addobserver(bt.observers.CashValue)
    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.Benchmark,
                        data=benchdata,
                        _doprenext=True,
                        timeframe=bt.TimeFrame.NoTimeFrame)
    
    # cerebro.addobserver(bt.observers.BuySell)

    # Add analyzers
    #cerebro.addanalyzer(TradeList, _name='trade_list')

    cerebro.addanalyzer(bt.analyzers.Returns)
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='strategy')
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='SPY', data=benchdata)
    cerebro.addanalyzer(bt.analyzers.DrawDown)

    opt_results = cerebro.run()
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

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