import alpaca_trade_api as tradeapi

api = tradeapi.REST(key_id="PK0OQNZNYD5OULFOXE81",
                    secret_key="8WMMk9jWm5hCIRrxUwcn5KvE4hEcKA/5IllazT7K")
barset = api.get_barset('GOOG', 'day', limit=252)

# Augemented Dickey-Fuller Test
from statsmodels.tsa.stattools import adfuller
r = adfuller(barset.df[('GOOG', 'close')].values)

print(f'ADF Statistic: {r[0]:.2f}')
for k,v in r[4].items():
    print (f'{k}: {v:.2f}')

# Cointegrated Augmented Dickey-Fuller Test
hd = api.get_barset('HD', 'day', limit=252)
low = api.get_barset('LOW', 'day', limit=252)

## Plot the two price series
import matplotlib.pyplot as plt
plt.plot(hd.df[('HD','close')], c='red', label='HD')
plt.plot(low.df[('LOW','close')], c='blue', label='LOW')
plt.legend()
plt.show()

## Hedge Ratio
### Align Indicies
i = hd.df.index.join(low.df.index, how='inner')
hddf = hd.df[('HD','close')].loc[i]
lowdf = low.df[('LOW','close')].loc[i]

### Calculate Hedge Ratio
import statsmodels.api as sm
model = sm.OLS(hddf[:126], lowdf[:126])
model = model.fit()
hedge_ratio = model.params[0]
print(f'Hedge Ratio: {hedge_ratio:.2f}')

### Plot Scatter
plt.scatter(hd.df[('HD','close')][126:], low.df[('LOW','close')][126:])
plt.xlabel('Home Depot')
plt.ylabel('Lowes')
plt.show()

### Determine Spread
### Notice we're avoiding look-ahead bias by not using data
### that was used to calculate the hedge ratio
spread = hddf[:126] - hedge_ratio * lowdf[:126]
spread.plot()
plt.show()

### Determine Spread Stationarity
# determine stationarity
r = adfuller(spread)
print(f'ADF Statistic: {r[0]:.2f}')
for k,v in r[4].items():
    print (f'{k}: {v:.2f}')
