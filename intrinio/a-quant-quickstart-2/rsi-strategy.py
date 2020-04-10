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
        'NKE', 'PFE', 'PG', 'TRV', 'UNH',
        'UTX', 'V', 'VZ', 'WMT', 'XOM'
        ]

class MyStrategy(bt.Strategy):
    params = dict( 
    num_positions=5,
    weekdays=5,
    weekcarry=True,
    rsi_period=5
    ) 

    def __init__(self):
        self.rsi = {}
        for d in self.datas:
            self.rsi[d] = bt.ind.RSI(d, period=self.p.rsi_period)


if __name__ == '__main__':
    # Initialize a cerebro instance
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(2500.0)
    cerebro.broker.setcommission(commission=0.001)

    # Read in the csv file we created and add the data.
    for stock in STOCKS[:3]:
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
    cerebro.plot()
    