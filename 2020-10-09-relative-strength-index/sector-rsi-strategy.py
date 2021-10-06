import backtrader as bt
from app.models.security import get_prices
from app.models.etf import get_sector_tickers

BENCHMARK_TICKER = '^GSPC'
START_DATE = '2010-01-01'
END_DATE = '2020-01-01'
USE_RSI_FILTER = True

class Strategy(bt.Strategy):
    params = dict(
        mom_period=20,
        num_positions=5,
        monthdays=[1],
        monthcarry=True,
        when=bt.timer.SESSION_START,
    )

    def __init__(self):
        self.inds = {}
        for d in self.datas:
            self.inds[d] = {}
            self.inds[d]['mom'] = bt.ind.ROC(d, period=self.p.mom_period, plot=False)
            self.inds[d]['rsi'] = bt.ind.RSI(d, plot=False)

        self.add_timer(
            when=self.p.when,
            monthdays=self.p.monthdays,
            monthcarry=self.p.monthcarry
        )

    def notify_timer(self, timer, when, *args, **kwargs):
        self.rebalance()

    def rebalance(self):
        ranked_sectors = []

        for d in self.datas[1:]:
            row = [d,
                   d.p.name,
                   self.inds[d]['mom'][0],
            ]
            if USE_RSI_FILTER:
                if self.inds[d]['rsi'][0] < 70:
                    ranked_sectors.append(row)
            else:
                ranked_sectors.append(row)
            
        sectors = sorted(ranked_sectors, key=lambda x: x[2], reverse=True)

        buys = [ s[0] for s in sectors[:self.p.num_positions] ]
        weight = 1 / len(buys)


        # prepare quick lookup list of stocks currently holding a position
        posdata = [d for d, pos in self.getpositions().items() if pos]

        # remove those no longer top ranked
        for d in (d for d in posdata if d not in buys):
            self.close(d)
    
        # rebalance those already top ranked and still there
        for d in (d for d in posdata if d in buys):
            self.order_target_percent(d, target=weight)
    
        # issue a target order for the newly top securities
        for d in buys:
            self.order_target_percent(d, target=weight)
    

# Create a cerebro instance
cerebro = bt.Cerebro(stdstats=True)

# Add Benchmark data
benchmark = get_prices([BENCHMARK_TICKER], START_DATE, END_DATE)
benchdata = bt.feeds.PandasData(dataname=benchmark.droplevel(level=0),
                                name='S&P 500',
                                plot=False)
print(f"Adding Benchmark {BENCHMARK_TICKER}.") 
cerebro.adddata(benchdata)

# Add sector data
sector_tickers = get_sector_tickers()
sector_prices = get_prices(sector_tickers, START_DATE, END_DATE)
for ticker, data in sector_prices.groupby(level=0):
    print(f"Adding sector ticker {ticker}.")
    d = bt.feeds.PandasData(dataname=data.droplevel(level=0),
                            name=ticker,
                            plot=False)
    cerebro.adddata(d)

# Add strategy
cerebro.addstrategy(Strategy)

# Add observers
cerebro.addobserver(bt.observers.Benchmark,
                    data=benchdata,
                    _doprenext=True,
                    timeframe=bt.TimeFrame.NoTimeFrame)

# Add analyzers
cerebro.addanalyzer(bt.analyzers.Returns, _name='strategy')
cerebro.addanalyzer(bt.analyzers.SharpeRatio, riskfreerate=0.02)

print(f'Starting Portfolio Value: {cerebro.broker.getvalue()}')

# Run the strategy
cerebro.run()

print(f'Ending Portfolio Value: {cerebro.broker.getvalue()}')

cerebro.plot()