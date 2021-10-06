import pandas as pd
from intrinio import intrinio_sdk

datatag_api = intrinio_sdk.DataTagApi()


financial_statements_df = pd.DataFrame()
statement_codes = ['balance_sheet_statement', 'income_statement', 'cash_flow_statement']

for statement_code in statement_codes:
    tags = datatag_api.get_all_data_tags(statement_code=statement_code)

    financial_statement = {}
    financial_statement['tag'] = []
    financial_statement['name'] = []
    financial_statement['statement_code'] = []
    financial_statement['statement_type'] = []
    financial_statement['sequence'] = []
    for tag in tags.tags_dict:
        financial_statement['tag'].append(tag['tag'])
        financial_statement['name'].append(tag['name'])
        financial_statement['statement_code'].append(tag['statement_code'])
        financial_statement['statement_type'].append(tag['statement_type'])
        financial_statement['sequence'].append(tag['sequence'])

    while tags.next_page:
        tags = datatag_api.get_all_data_tags(statement_code='statement_code', next_page=tags.next_page)
        for tag in tags.tags_dict:
            financial_statement['tag'].append(tag['tag'])
            financial_statement['name'].append(tag['name'])
            financial_statement['statement_code'].append(tag['statement_code'])
            financial_statement['statement_type'].append(tag['statement_type'])
            financial_statement['sequence'].append(tag['sequence'])

            print(financial_statement)
        
    df = pd.DataFrame.from_dict(financial_statement)
    financial_statements_df = financial_statements_df.append(df)

fltr = financial_statements_df['statement_type'] == 'industrial'
financial_statements_df.loc[fltr, 'statement_type'] = 'commercial'
financial_statements_df.to_csv('financial_statements_lines.csv')
