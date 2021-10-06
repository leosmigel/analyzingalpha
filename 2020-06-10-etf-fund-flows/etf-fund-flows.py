import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from app.db.psql import db, session
from app.models.etf import EtfFundFlow, \
                           get_etf_fund_flows, \
                           get_sector_tickers


def create_flow_data(tickers, start, end):
    ## Using convention for return identification:
    ## Simple returns denoted with capital R
    ## log returns identified by lowercase r
    etf_fund_flows = get_etf_fund_flows(tickers, start, end)
    etf_fund_flows['daily_R'] = etf_fund_flows['nav'].groupby(level='ticker').pct_change()
    etf_fund_flows['daily_r'] = np.log(etf_fund_flows['nav']).groupby(level=0).diff()
    etf_fund_flows['flow'] = np.log(etf_fund_flows['shares_outstanding']).groupby(level=0).diff()
    etf_fund_flows['mktcap'] = etf_fund_flows['nav'] * etf_fund_flows['shares_outstanding']
    etf_fund_flows.dropna(inplace=True)
    return etf_fund_flows

def calc_etf_return(df):
    avg_daily_r = df['daily_r'].mean()
    annual_ret_log = avg_daily_r * 252
    annual_ret_simple = np.exp(annual_ret_log) - 1
    return annual_ret_simple * 100

def calc_investor_return(df):
    flows = df['flow'] * (df['mktcap'] / df['mktcap'].iloc[0])
    flows.iloc[0] = 1
    basis = flows.cumsum()

    avg_daily_r = (df['daily_r'] * basis / basis.mean()).mean()
    annual_ret_log = avg_daily_r * 252
    annual_ret_simple = np.exp(annual_ret_log) - 1
    return annual_ret_simple * 100

def compare_annual(df):
    tickers = df.index.get_level_values(0).unique().tolist()

    out = pd.DataFrame()
    for ticker in tickers:
        twr = df.loc[ticker].resample('A').apply(calc_etf_return)
        mwr = df.loc[ticker].resample('A').apply(calc_investor_return)
        mwr.name = 'mwr'
        twr.name = 'twr'
        both = pd.concat([twr, mwr], axis=1).reset_index()
        both['ticker'] = ticker
        both['timing_impact'] = both['mwr'] - both['twr']
        both.set_index(['date', 'ticker'], inplace=True)
        out = pd.concat([out, both], axis=0)

    return out

start = '2017-04-01'
end = '2019-12-31'
ticker = 'XLE'

xle = create_flow_data([ticker], start, end)
xle = xle.loc['XLE']
xle['shares_outstanding'] \
    .plot(figsize=(16,10), legend=True)
xle['nav'].rename('price') \
    .plot(title=f"{ticker}: Shares Outstanding vs. Price",
          legend=True,
          secondary_y=True)
plt.show()

tickers = ['SPY', 'IWM', 'QQQ', 'VT']
flows = create_flow_data(tickers, start, end)

results = pd.DataFrame(columns=['investment', 'investor'])
for ticker in tickers:
   tmp = flows.xs(ticker, level='ticker', drop_level=True)
   results.loc[ticker, 'investment'] = calc_etf_return(tmp)
   results.loc[ticker, 'investor'] = calc_investor_return(tmp)
   results['behavioral_gap'] = results['investor'] - results['investment']
   print(results)

by_year = compare_annual(flows)['timing_impact'].unstack().round(3)
print(by_year)

by_year.index = by_year.index.year
sns.heatmap(by_year,center =0.00,
            cmap = sns.diverging_palette(10, 220, sep=1, n=21),
            annot=True)
plt.title('Behavioral Gap Heatmap')
plt.show()
