# Get the imports we need including backtrader
# csv and datetime.

import csv
from datetime import datetime
import backtrader as bt

STOCKS = [
        'AAPL', 'AXP', 'BA', 'CAT', 'CSCO',
        'CVX', 'DIS', 'DWDP', 'GE', 'GS',
        'HD', 'IBM', 'INTC', 'JNJ', 'JPM',
        'KO', 'MCD', 'MMM', 'MRK', 'MSFT',
        'NKE', 'PFE', 'PG', 'TRV',
        'UTX', 'V', 'VZ', 'WMT', 'XOM'
        ]

class MyStrategy(bt.Strategy):
    params = dict( 
        num_universe=10,
        num_positions=2,
        when=bt.timer.SESSION_START,
        weekdays=[5],
        weekcarry=True,
        rsi_period=10,
        sma_period=50
    ) 

    def __init__(self):
        self.inds = {}
        self.securities = self.datas[1:]
        for s in self.securities:
            self.inds[s] = {}
            self.inds[s]['sma'] = bt.ind.SMA(s, period=self.p.sma_period)
            self.inds[s]['rsi'] = bt.ind.RSI(s, period=self.p.rsi_period)

        self.add_timer(
            when=self.p.when,
            weekdays=self.p.weekdays,
            weekcarry=self.p.weekcarry
    )

    def notify_timer(self, timer, when, *args, **kwargs):
            self.rebalance()
    
    def notify_trade(self, trade):
        if trade.size == 0:  # Trade size zero is closed out.
            print(f"Trade PNL: Date: {trade.data.datetime.date(ago=0)} Ticker: {trade.data.p.name} Profit: {round(trade.pnlcomm,2)}")
            
            
    def rebalance(self):
        rankings = list(self.securities)
        rankings.sort(
            key=lambda s: self.inds[s]['sma'][0],
            reverse=False
        )
        rankings = rankings[:self.p.num_universe]
        rankings.sort(
            key=lambda s: self.inds[s]['rsi'][0],
            reverse=True
        )

        pos_size = -1 / self.p.num_positions # Go short

        # Sell stocks no longer meeting ranking filter.
        for i, d in enumerate(rankings):
            if self.getposition(d).size:
                if i > self.p.num_positions:
                    self.close(d)

        # Buy and rebalance stocks with remaining cash
        for i, d in enumerate(rankings[:self.p.num_positions]):
            self.order_target_percent(d, target=pos_size)
            

if __name__ == '__main__':
    # Initialize a cerebro instance
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(2500.0)
    cerebro.broker.setcommission(commission=0.001)

    # Read in the csv file we created and add the data.
    for stock in STOCKS:
        filename = stock + '.csv'
        data = bt.feeds.GenericCSVData(
            dataname=filename,
            dtformat=('%Y-%m-%d'),
            datetime=0,
            high=2,
            low=2,
            open=1,
            close=4,
            volume=5,
            openinterest=-1,
            name=stock
        )
        cerebro.adddata(data)

    # Add the strategy
    cerebro.addstrategy(MyStrategy)
    # Run the strategy printing the starting and ending values, and plot the results.

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    cerebro.run()
    print('Ending Portfolio Value: %.2f' % cerebro.broker.getvalue())