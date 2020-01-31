# Get the imports we need to use including
# Intrinio, Backtrader. We also grab csv
# and datetime to save the data to a csv.

import csv
from datetime import datetime
import backtrader as bt
import intrinio_sdk
apikey = 'YOUR_API_KEY'


if __name__ == '__main__':

    # Connect to Intrinio using our sandbox API key.
    # The code is exactly the same same as the Python
    # Interpreter tutorial
    intrinio_sdk.ApiClient().configuration.api_key['api_key'] = apikey
    security_api = intrinio_sdk.SecurityApi()
    api_response = security_api.get_security_stock_prices('AAPL')

    # Loop through the API response creating a list in the format we need.
    prices = []
    for row in api_response.stock_prices_dict:
        date = row['date']
        o = row['adj_open']
        h = row['adj_high']
        l = row['adj_low']
        c = row['adj_close']
        v = row['adj_volume']
        prices.append([date, o, h, l, c, v])

    # Reverse the list so the data is oldest to newest
    prices = reversed(prices)

    # Write the list to a csv file
    with open('apple.csv', mode='w') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerows(prices)


    # With the data now in a CSV file
    # it's time to create the strategy in Backtrader
    class SmaCross(bt.SignalStrategy):
        def __init__(self):
            sma1, sma2 = bt.ind.SMA(period=1), bt.ind.SMA(period=4)
            crossover = bt.ind.CrossOver(sma1, sma2)
            self.signal_add(bt.SIGNAL_LONG, crossover)

    if __name__ == '__main__':
        cerebro = bt.Cerebro()
        cerebro.addstrategy(SmaCross)
        cerebro.broker.setcash(250.0)
        cerebro.broker.setcommission(commission=0.001)

        # Read in the csv file we created and add the data.
        data = bt.feeds.GenericCSVData(
            dataname='apple.csv',
            dtformat=('%Y-%m-%d'),
            datetime=0,
            high=2,
            low=2,
            open=1,
            close=4,
            volume=5,
            openinterest=-1
        )

        cerebro.adddata(data)

        # Run the strategy printing the starting and ending values, and plot the results.
        print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
        cerebro.run()
        print('Ending Portfolio Value: %.2f' % cerebro.broker.getvalue())
        cerebro.plot()

