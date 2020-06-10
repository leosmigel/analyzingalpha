import intrinio_sdk
import pandas as pd
import backtrader as bt

START_DATE = '2017-01-01'
END_DATE = '2017-12-31'
APIKEY = 'YOUR_API_KEY'

# List sourced from DOW30
# https://docs.intrinio.com/developer-sandbox
STOCKS = [
        'AAPL', 'AXP', 'BA', 'CAT', 'CSCO',
        'CVX', 'DIS','GE', 'GS',
        'HD', 'IBM', 'INTC', 'JNJ', 'JPM',
        'KO', 'MCD', 'MMM', 'MRK', 'MSFT',
        'NKE', 'PFE', 'PG', 'TRV', 'UNH',
        'UTX', 'V', 'VZ', 'WMT', 'XOM'
        ]

intrinio_sdk.ApiClient().configuration.api_key['api_key'] = APIKEY,
security_api = intrinio_sdk.SecurityApi()
company_api = intrinio_sdk.CompanyApi()
fundamental_api = intrinio_sdk.FundamentalsApi()
securities_prices = pd.DataFrame()
securities_fundamentals = pd.DataFrame()

for stock in STOCKS:
    # Loop through the API response creating a list in the format we need.
    api_response = security_api.get_security_stock_prices(stock,
                                                          start_date=START_DATE,
                                                          end_date=END_DATE)
    prices = []
    for row in api_response.stock_prices_dict:
        t = stock
        d = row['date']
        o = row['adj_open']
        h = row['adj_high']
        l = row['adj_low']
        c = row['adj_close']
        v = row['adj_volume']
        prices.append([t, d, o, h, l, c, v])

    security_prices = pd.DataFrame(prices, columns=['ticker', 'date', 'open', 'high', 'low', 'close', 'volume'])

    quarters = ['Q1', 'Q2', 'Q3', 'Q4']
    fundamentals = []
    for quarter in quarters:
        api_response = company_api.lookup_company_fundamental(stock,
                                                        statement_code='calculations',
                                                        fiscal_year=2017,
                                                        fiscal_period=quarter)
        funid = api_response.to_dict()['id']
        fun_api_response = fundamental_api.get_fundamental_standardized_financials(funid)
        for tags in fun_api_response.standardized_financials_dict:
           if tags['data_tag']['tag'] == 'pricetobook':
               pb = tags['value']
               date = fun_api_response.fundamental_dict['start_date'] 
               fundamentals.append([stock, date, pb])
            
    security_fundamentals = pd.DataFrame(fundamentals, columns=['ticker', 'date', 'pb']) 
    securities_fundamentals = securities_fundamentals.append(security_fundamentals)
    securities_prices = securities_prices.append(security_prices)

securities_prices = securities_prices.set_index(['ticker', 'date']).sort_index()
securities_fundamentals = securities_fundamentals.set_index(['ticker', 'date']).sort_index()
securities_prices = securities_prices.merge(securities_fundamentals, on=['ticker','date'], how='left').ffill().bfill()

print(securities_prices)


class PandasDataCustom(bt.feeds.PandasData):
    lines = ('pb',)
    params = (
        ('pb', -1),
    )


class St(bt.Strategy):
    params = dict(
        targetnum=5,
        targetpct=0.2,
        weekdays=[5],
        weekcarry=True,
        when=bt.timer.SESSION_START
    )

    def __init__(self):
        self.inds = {}
        for stock in self.datas:
            self.inds[stock] = {}
            self.inds[stock]['pb'] = stock.pb

        self.add_timer(
            when=self.p.when,
            weekdays=self.p.weekdays,
            weekcarry=self.p.weekcarry
            )

    def notify_timer(self, timer, when, *args, **kwargs):
        self.rebalance()

    def rebalance(self):
        # Rank by lowest price-to-book value
        ranks = sorted(self.datas, key=lambda d: self.inds[d]['pb'][0])
        ranks = ranks[:self.p.targetnum]

        # Get existing positions
        posdata = [d for d, pos in self.getpositions().items() if pos]

        # Close positions if they are no longer in top rank
        for d in (d for d in posdata if d not in ranks):
            print(f"Closing: {d.p.name}")
            self.close(d)

        # Rebalance positions already there
        for d in (d for d in posdata if d in ranks):
            print(f"Rebalancing: {d.p.name}")
            self.order_target_percent(d, target=self.p.targetpct)
        
        # Buy new positions
        for d in ranks:
            print(f"Buying: {d.p.name}")
            self.order_target_percent(d, target=self.p.targetpct)


# Initialize Cerebro
cerebro = bt.Cerebro()

print(securities_prices)
# Add Data
for ticker, data in securities_prices.groupby(level=0):
    print(f"Adding ticker {ticker}")
    d = PandasDataCustom(dataname=data.droplevel(level=0),
                          name=ticker,
                          plot=False)
    cerebro.adddata(d)

# Add Strategy
cerebro.addstrategy(St)

# Run the strategy
cerebro.run()

# Plot results
cerebro.plot()
