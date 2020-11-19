import alpaca_backtrader_api as alpaca
import backtrader as bt
import pytz
from datetime import datetime, date
from fredapi import Fred
from local_settings import alpaca_paper_settings, fred_settings

ALPACA_KEY_ID = alpaca_paper_settings['api_key']
ALPACA_SECRET_KEY = alpaca_paper_settings['api_secret']
ALPACA_PAPER = True
FRED_API_KEY = fred_settings['api_key']

fromdate = datetime(2020,6,1)
todate = datetime(2020,10,31)
tickers = ['SPY']

fred = Fred(api_key=FRED_API_KEY)
unrate = fred.get_series('unrate', observation_start=fromdate, observation_end=todate)
monthly_unrate_increasing = (unrate > unrate.shift(1)).dropna().astype(float)

class St(bt.Strategy):

    def __init__(self):
        self.technical_hedge = bt.ind.SMA(self.data, period=30, plot=False) > self.data

    def next(self):
        day = self.data0.datetime.date(ago=0)
        month = date.strftime(day, "%Y-%m")
        fundamental_hedge = monthly_unrate_increasing.loc[month][0]

        if self.technical_hedge[0] and fundamental_hedge:
            print(f"{day}: Hedging:\n**Negative price action: {self.technical_hedge[0]}. Unemployment increasing: {fundamental_hedge}")
        else:
            print(f"{day}: Not hedging:\n**Negative price action: {self.technical_hedge[0]}. Unemployment increasing: {fundamental_hedge}")


cerebro = bt.Cerebro()
cerebro.addstrategy(St)
cerebro.broker.setcash(100000)
cerebro.broker.setcommission(commission=0.0)

store = alpaca.AlpacaStore(
    key_id=ALPACA_KEY_ID,
    secret_key=ALPACA_SECRET_KEY,
    paper=ALPACA_PAPER
)

if not ALPACA_PAPER:
    print(f"LIVE TRADING")
    broker = store.getbroker()
    cerebro.setbroker(broker)

DataFactory = store.getdata

for ticker in tickers:
    print(f'Adding ticker {ticker}.')
    d = DataFactory(
        dataname=ticker,
        timeframe=bt.TimeFrame.Days,
        fromdate=fromdate,
        todate=todate,
        historical=True)
    cerebro.adddata(d)

cerebro.run()
print("Final Portfolio Value: %.2f" % cerebro.broker.getvalue())
#cerebro.plot(style='candlestick', barup='green', bardown='red')
