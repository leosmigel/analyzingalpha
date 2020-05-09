import csv
import pandas as pd
import intrinio_sdk

apikey = "ENTER_YOUR_API_KEY"

# Get connected to Intrinio and grab APIs
intrinio_sdk.ApiClient().configuration.api_key['api_key'] = apikey
company_api = intrinio_sdk.CompanyApi()
fundamentals_api = intrinio_sdk.FundamentalsApi()
security_api = intrinio_sdk.SecurityApi()

# Grab Apple filings for 2018 
api_response = company_api.get_company_fundamentals('AAPL',
                                          fiscal_year=2018,
                                          statement_code='calculations')

# Grab the full year filing
calculations = {}
for filing in api_response.fundamentals_dict:
	if filing['fiscal_period'] == 'FY':
		calcluations = filing
#print(calculations)

# Get the price to book from the full year filing
api_response = fundamentals_api.get_fundamental_standardized_financials(calcluations['id'])
pricetobook = None
for calc in api_response.standardized_financials_dict:
	if calc['data_tag']['tag'] == 'pricetobook':
		pricetobook = calc['value']
#print(pricetobook)

# Get the 2018 Apple prices
api_response = security_api.get_security_stock_prices('AAPL',
                                                      start_date='2018-01-01',
                                                      end_date='2018-12-31')
aapl_prices = api_response.stock_prices_dict
while api_response.next_page:
	api_response = security_api.get_security_stock_prices('AAPL',
                                                          start_date='2018-01-01',
                                                          end_date='2018-12-31', next_page=api_response.next_page)
	aapl_prices.extend(api_response.stock_prices_dict)
#print(aapl_prices)

# Manipulate the data using pandas and add price to book to OHLCV
df = pd.DataFrame(aapl_prices)
df.set_index('date', inplace=True)
df = df[['adj_open', 'adj_high', 'adj_low', 'adj_close', 'adj_volume']]
df.loc[:,'pb'] = pricetobook
#print(df)
#df.to_csv('aapl.csv')