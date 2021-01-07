import alpaca_trade_api as tradeapi

api = tradeapi.REST(key_id="YOURKEY",secret_key="YOURSECRET")


# Get data from alpaca and align dates
gld = api.get_barset('GLD', 'day', limit=252)
gdx = api.get_barset('GDX', 'day', limit=252)
uso = api.get_barset('USO', 'day', limit=252)

glddf = gld.df[('GLD', 'close')].rename("GLD")
gdxdf = gdx.df[('GDX', 'close')].rename("GDX")
usodf = uso.df[('USO', 'close')].rename("USO")

glddf = glddf.to_frame()
df = glddf.join([gdxdf, usodf], how='inner')

# Plot the prices
import matplotlib.pyplot as plt
df.plot(figsize=(20,15))
#plt.show()

# Johansen Test
from statsmodels.tsa.vector_ar.vecm import coint_johansen
r = coint_johansen(df, 0, 1)

# Print trace statistics and eigen statistics
print(f"\t\tStat \t90%\t 95%\t 99%")
print (f"R <= Zero\t{round(r.lr1[0], 3)}\t{round(r.cvt[0, 0], 3)}\t {round(r.cvt[0, 1],3)}\t {round(r.cvt[0, 2],3)}")

# Analyze USO split
print(usodf['2020-04-25':'2020-04-30'])

