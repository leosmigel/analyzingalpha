import pandas as pd
from datetime import datetime
import numpy as np

data = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')

# Get current S&P table and set header column
sp500 = data[0].loc[1:,[0,6]]
sp500.columns = ['added_ticker', 'date']

# Add S&P500 start date if date is null and correct '1985' date
sp500.loc[sp500['date'].isnull(), 'date'] = '1957-01-01'
sp500.loc[~sp500['date'].str.match('\d{4}-\d{2}-\d{2}'), 'date'] = '1985-01-01'
sp500.loc[:,'date'].apply(lambda x: datetime.strptime(x,'%Y-%m-%d'))
sp500 = pd.melt(sp500, id_vars=['date'], value_vars=['added_ticker'])

# Get S&P500 adjustments table and set columns
sp500_adjustments = data[1]
sp500_adjustments = sp500_adjustments[2:].copy()
sp500_adjustments.columns = ['date', 'added_ticker', 'added_name',
                            'removed_ticker', 'removed_name', 'reason']

# Correct for multiple table issues.
updates = sp500_adjustments[~sp500_adjustments['date'].str.contains(',')].T.shift(1).T
sp500_adjustments['date'].loc[~sp500_adjustments['date'].str.contains(',')] = np.nan
sp500_adjustments.update(updates)
sp500_adjustments['date'].loc[sp500_adjustments['date'] \
                         .isnull()] = sp500_adjustments['date'].T.shift(1).T
sp500_adjustments['date'].loc[sp500_adjustments['date'] \
                         .isnull()] = sp500_adjustments['date'].T.shift(1).T
sp500_adjustments['date'].loc[sp500_adjustments['date'] \
                         .isnull()] = sp500_adjustments['date'].T.shift(1).T
sp500_adjustments['date'].loc[sp500_adjustments['date'] \
                         .isnull()] = sp500_adjustments['date'].T.shift(1).T
sp500_adjustments['date'].loc[sp500_adjustments['date'] \
                         .isnull()] = sp500_adjustments['date'].T.shift(1).T
sp500_adjustments['date'] = sp500_adjustments['date'] \
                            .apply(lambda x: datetime.strptime(x,'%B %d, %Y'))
sp500_adjustments = pd.melt(sp500_adjustments, id_vars=['date'], 
                             value_vars=['added_ticker', 'removed_ticker'])

# Append adjustments to current index and sort by date
df = pd.concat([sp500, sp500_adjustments], ignore_index=True)
df['date'] = pd.to_datetime(df['date'])
df.sort_values(by='date',inplace=True)

# Dedupe the records and save to csv
deduped_df = df[~df.duplicated(['date', 'variable', 'value'])]
print(deduped_df.tail())
deduped_df.to_csv("sp500.csv")