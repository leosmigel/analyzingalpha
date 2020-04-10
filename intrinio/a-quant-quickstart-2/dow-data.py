import csv
import intrinio_sdk

APIKEY = 'YOUR_API_KEY'

# List sourced from DOW30
# https://docs.intrinio.com/developer-sandbox

STOCKS = [
        'AAPL', 'AXP', 'BA', 'CAT', 'CSCO',
        'CVX', 'DIS', 'DWDP', 'GE', 'GS',
        'HD', 'IBM', 'INTC', 'JNJ', 'JPM',
        'KO', 'MCD', 'MMM', 'MRK', 'MSFT',
        'NKE', 'PFE', 'PG', 'TRV', 'UNH',
        'UTX', 'V', 'VZ', 'WMT', 'XOM'
        ]

intrinio_sdk.ApiClient().configuration.api_key['api_key'] = APIKEY,
security_api = intrinio_sdk.SecurityApi()

for stock in STOCKS:
    # Loop through the API response creating a list in the format we need.
    print(stock)
    api_response = security_api.get_security_stock_prices(stock)
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
    filename = stock + '.csv'
    with open(filename, mode='w') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerows(prices)
