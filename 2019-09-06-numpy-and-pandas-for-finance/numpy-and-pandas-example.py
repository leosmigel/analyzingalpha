# Using NumPy
## Import NumPy so we can use it
import numpy as np

## Create a list of lists. Think Excel table with rows and columns.
price_earnings = [
              ['Company A', 10., 2.0],
              ['Company B', 30., 4.0],
              ['Company C', 50., 6.0],
              ['Company D', 70., 8.0],
              ['Company E', 90., 10.0]
             ]


# Creating NumPy n-dimensional arrays

## Creating array from prior values
company_table = np.array(price_earnings)

## Autogenerate a 1D array
array1d = np.arange(10)

## Autogenerate a 2D array
array2d = array1d.reshape(2,5)

# Selecting Data by Slicing 
## Retreive a single cell
cell = company_table[1,1]

## Retrieve the first row and all of the columns
row = company_table[0,:]

## Retreive all rows for the third column
column = company_table[:,2]

## Retreive two columns
two_columns = company_table[:,[0,2]]

## Retreive subsection
subsection = company_table[[0,2],[0,1]]

## Create pe_ratios column 
pe_ratios = company_table[:,1].astype(float) / company_table[:,2].astype(float)

## Create mask to filter for low PEs
low_pe_filter = pe_ratios < 8

## Apply mask to company table to get low PE rows
low_pe_stocks = company_table[low_pe_filter]

array2d = np.array([
                     [1,2,3,4],
                     [5,6,7,8],
                     [9,10,11,12],
                     [13,14,15,16],
                     [17,18,19,20]
                    ])


rows_mask = [True, False, False, True, True]
columns_mask = [True, True, False, True]

# working examples
print(array2d.shape)
works1 = array2d[rows_mask]
works2 = array2d[:, columns_mask]
#works3 = array2d[rows_mask, columns_mask]

# incorrect examples due to dimension mismatch
#does_not_work1 = array2d[columns_mask]
#does_not_work2 = array2d[row_mask, row_mask]

# Change single value
array2d[0,0] = 5
array2d[0,0] = array2d[0,0] * 2

# Change row
array2d[0,:] = 0

# Change column
array2d[:,0] = 0

# Change a block
array2d[1:,[2,3]] = 0

# Change any value greater than 5 to 5
array2d[array2d > 5] = 5

# Change any value in column 2 greater than 5 to 5
array2d[array2d[:,1] > 5, 1] = 5

# Pandas
## Import pandas so we can use it
import pandas as pd

## Create a dataframe
data = {'company': ['Company A', 'Company B', 'Company C', 'Company D', 'Company E'],
        'price': [10, 30, 50, 70, 90],
        'earnings': [2.0, 4.0, 6.0, 8.0, 10.0]
        }

df = pd.DataFrame(data)
df.info()
print(df.describe())
print(df['price'].describe())
print(df['company'].describe())

# Create a series
column_series = df['company']
row_series = df.loc[0]

print(df.head(2))
print(df.tail(2))
print(column_series.head(2))
print(row_series.tail(2))

## Selecting from Dataframe
## Retrieve a single cell
cell = df.loc[1,'price']

## Retrieve the first row and all of the columns
row = df.loc[0,:]

## Retreive all rows for the third column
column = df.loc[:,'earnings']
column_short = df['earnings']

## Retreive a range of rows
rows = df.loc[1:3]
rows_short = df[1:3]

## Retreive two columns
two_columns = df.loc[:,['company','earnings']]
two_columns_short = df[['company','earnings']]

## Retrieve a range of columns
range_of_columns = df.loc[:,'earnings':'price']

## Retreive subsection
subsection = df.loc[0:2,['company','price']]

## Selecting from Series
## Selecting a single cell
cell = column_series.loc[1]
cell_short = column_series[1]

## Selecting a range of cells from a column
cell_range = column_series.loc[0:3]
cell_range_short = column_series[0:3]

## Selecting a range of cells from a row
cell_range = row_series.loc['company':'price']
cell_range_short = row_series['company':'price']

## Standard Operation examples
print(df[['earnings','price']] + 10)
df['pe_ratio'] = df['price'] / df['earnings']

# Assignment
df.set_index('company', inplace=True)
#df.loc['Company B', 'pe_ratio'] = 0.0

## Assignment to a single element
df.loc['Company B','price'] = 0.0
                      
## Assignment to an entire row
df.loc['Company B',:] = 0
                           
## Assignment to an entire column
df.loc[:,'earnings'] = 0.0
df['earnings'] = 1.0

## Assignment to a range of rows
df.loc['Company A':'Company C'] = 0.0 
df['Company A':'Company C'] = 1.0
                                    
## Assignment to two columns      
df.loc[:,['price','earnings']] = 2.0
df[['price','earnings']] = 3.0
                                                 
## Assignment to a range of columns              
df.loc[:,'earnings':'pe_ratio'] = 4.0

## Assignment to a subsection
df.loc['Company A':'Company C',['price','earnings']] = 5.0

## Assignment using boolean indexing
### Using boolean value
price_bool = df['price'] < 4.0
df.loc[price_bool,'price'] = 6.0

### Skipping boolean value
df.loc[df['price'] >= 4, 'price'] = 7.0
df['earnings'][df['price'] == 7] = 8.0
print(df)


