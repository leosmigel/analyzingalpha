import alpaca_backtrader_api as alpaca
import backtrader as bt
import pytz
import pandas as pd
from local_settings import alpaca_paper

ALPACA_KEY_ID = alpaca_paper['api_key']
ALPACA_SECRET_KEY = alpaca_paper['api_secret']
ALPACA_PAPER = True

fromdate = pd.Timestamp(2020,5,1)
todate = pd.Timestamp(2020,8,17)
timezone = pytz.timezone('US/Eastern')

tickers = ['SPY']
timeframes = {
    '15Min':15,
    '30Min':30,
    '1H':60,
}
lentimeframes = len(timeframes)

class RSIStack(bt.Strategy):
    params = dict(
        rsi_overbought=70,
        rsi_oversold=30,
        rrr=2
    )

    def __init__(self):

        self.orefs = None
        self.inds = {}
        for d in self.datas:
            self.inds[d] = {}
            self.inds[d]['rsi'] = bt.ind.RSI(d)
            self.inds[d]['rsiob'] = self.inds[d]['rsi'] >= self.p.rsi_overbought
            self.inds[d]['rsios'] = self.inds[d]['rsi'] <= self.p.rsi_oversold
        for i in range(len(timeframes)-1, len(self.datas), len(timeframes)):
            self.inds[self.datas[i]]['atr'] = bt.ind.ATR(self.datas[i])

    def start(self):
        # Timeframes must be entered from highest to lowest frequency.
        # Getting the length of the lowest frequency timeframe will
        # show us how many periods have passed
        self.lenlowtframe = len(self.datas[-1])
        self.stacks = {}


    def next(self):
        # Reset all of the stacks if a bar has passed on our
        # lowest frequency timeframe
        if not self.lenlowtframe == len(self.datas[-1]):
            self.lenlowtframe += 1
            self.stacks = {}

        for i, d in enumerate(self.datas):
            # Create a dictionary for each new symbol.
            ticker = d.p.dataname
            if i % len(timeframes) == 0:
                self.stacks[ticker] = {}
                self.stacks[ticker]['rsiob'] = 0
                self.stacks[ticker]['rsios'] = 0
            if i % len(timeframes) == len(timeframes) -1:
                self.stacks[ticker]['data'] = d
            self.stacks[ticker]['rsiob'] += self.inds[d]['rsiob'][0]
            self.stacks[ticker]['rsios'] += self.inds[d]['rsios'][0]

        for k,v in list(self.stacks.items()):
            if v['rsiob'] < len(timeframes) and v['rsios'] < len(timeframes):
                del self.stacks[k]

        # Check if there are any stacks from the previous period
        # And buy/sell stocks if there are no existing positions or open orders
        positions = [d for d, pos in self.getpositions().items() if pos]
        if self.stacks and not positions and not self.orefs:
                for k,v in self.stacks.items():
                    d = v['data']
                    size = self.broker.get_cash() // d
                    if v['rsiob'] == len(timeframes) and \
                                     d.close[0] < d.close[-1]:
                        print(f"{d.p.dataname} overbought")
                        risk = d + self.inds[d]['atr'][0]
                        reward = d - self.inds[d]['atr'][0] * self.p.rrr
                        os = self.sell_bracket(data=d,
                                               price=d.close[0],
                                               size=size,
                                               stopprice=risk,
                                               limitprice=reward)
                        self.orefs = [o.ref for o in os]
                    elif v['rsios'] == len(timeframes) and d.close[0] > d.close[-1]:
                        print(f"{d.p.dataname} oversold")
                        risk = d - self.inds[d]['atr'][0]
                        reward = d + self.inds[d]['atr'][0] * self.p.rrr
                        os = self.buy_bracket(data=d,
                                              price=d.close[0],
                                              size=size,
                                              stopprice=risk,
                                              limitprice=reward)
                        self.orefs = [o.ref for o in os]


    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.data.datetime[0]
        if isinstance(dt, float):
            dt = bt.num2date(dt)
        print(f'{dt.isoformat()}: {txt}')

    def notify_trade(self, trade):
        if not trade.size:
            print(f'Trade PNL: ${trade.pnlcomm:.2f}')

    def notify_order(self, order):
        self.log(f'Order - {order.getordername()} {order.ordtypename()} {order.getstatusname()} for {order.size} shares @ ${order.price:.2f}')

        if not order.alive() and order.ref in self.orefs:
            self.orefs.remove(order.ref)

cerebro = bt.Cerebro()
cerebro.addstrategy(RSIStack)
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
    for timeframe, minutes in timeframes.items():
        print(f'Adding ticker {ticker} using {timeframe} timeframe at {minutes} minutes.')

        d = DataFactory(
            dataname=ticker,
            timeframe=bt.TimeFrame.Minutes,
            compression=minutes,
            fromdate=fromdate,
            todate=todate,
            historical=True)

        cerebro.adddata(d)

cerebro.run()
print("Final Portfolio Value: %.2f" % cerebro.broker.getvalue())
cerebro.plot(style='candlestick', barup='green', bardown='red')
