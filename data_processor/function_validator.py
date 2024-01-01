import pandas as pd
from typing import List, Dict
from stdnum import isin, cusip
from sqlalchemy import create_engine

from models.helpers import divide_cusip

db_config = {
    'server': '',
    'user': '',
    'password': ''
} # database: 'sayers-wealth-prd-sqldb'

class RefinitivCodeValidator:
    def __init__(self, data: dict):
        self.df = self.setup_data(data)
        self.engine = {
            'qvm': create_engine(self.create_connection_string('')),
            'advisors': create_engine(self.create_connection_string('')),
        }
        self.exchange_table = pd.read_sql_table(table_name='exchanges', schema='define', con=self.engine['advisors'].connect())
        #save exchange table as json
        #self.exchange_table.to_json('exchange_table.json', orient='records')
    @staticmethod
    def create_connection_string(database_name: str) -> str:
        return f"mssql+pyodbc://{db_config['user']}:{db_config['password']}@{db_config['server']}/{database_name}?driver=ODBC+Driver+17+for+SQL+Server&MARS_Connection=Yes"

    def setup_data(self, data:dict) -> pd.DataFrame:
        # if 'portfolios' in data.keys() and isinstance(data['portfolios'], list):
        #     return [pd.DataFrame(portfolio) for portfolio in data.values()]
        if isinstance(data, pd.DataFrame):
            return data
        else:
            return pd.DataFrame(data)

    @staticmethod
    def is_australian_equity(row) -> bool:
        return row[2] == 'Australian Equities'

    def refinitiv_code(self, row) -> str:
        ticker = row[0]
 
        if isin.is_valid(ticker):
            return ticker+"|ISIN"

        if cusip.is_valid(ticker):
            # Split the CUSIP into subcategories.
            subcategories = divide_cusip(ticker)
            
            # Build the result string.
            result = f"{ticker}|CUSIP"
            for category, value in subcategories.items():
                result += f"{category}: {value}\n"
        
            return f"{ticker}|CUSIP({subcategories['Issue Type']})"

        if self.is_australian_equity(row) and len(ticker) < 8 and '.' not in ticker:
            return f"{ticker}.AX"

        if '.' not in ticker:
            if len(ticker) == 9:
                return ticker
            elif len(ticker) == 5 and ticker[3] == 'P':
                return f"{ticker}.AX|PREF"
            elif 'CMA' in ticker or 'CASH' in ticker:
                return f"{ticker}|CASH"
            elif '+' in ticker and len(ticker) == 10:
                return f"{ticker}|BOND"
            else:
                print(f"International Exchange Code Missing: Ticker >{ticker}< is not a valid ticker")
                return f"{ticker}|ERROR"

        ric, exchange_code = row[0].split('.')[0], row[0].split('.')[1]
        for exchange_ext_column in ['PWExchangeCode', 'NWExchangeCode', 'IBExchangeCode']:
            if self.exchange_table[exchange_ext_column].isin([exchange_code]).any():
                index = self.exchange_table[self.exchange_table[exchange_ext_column] == exchange_code].index[0]
                tr_code = self.exchange_table.loc[index, 'TRExtension']
                return f"{ric}.{tr_code}"
            else:
                raise ValueError(f"Exchange Code Missing from mapping table. Could not map {exchange_code} to a TR extension. Ticker = {row['ticker']}")

        

        for exchange_ext_column in ['PWExchangeCode', 'NWExchangeCode', 'IBExchangeCode']:
            if self.exchange_table[exchange_ext_column].isin([exchange_code]).any():
                    index = self.exchange_table[self.exchange_table[exchange_ext_column] == exchange_code].index[0]
                    tr_code = self.exchange_table.loc[index, 'TRExtension']
                    return f"{ric}.{tr_code}"
            else:
                    raise ValueError(f"Exchange Code Missing from mapping table. Could not map {exchange_code} to a TR extension. Ticker = {row['ticker']}")

    def map_values_from_validate(self, input_list: list) -> dict:
        assets = {'ISIN': [], 'Equity': [], 'Clean Rics': [], 'Preferred': [], 'Fixed_Interest': [], 'Cash': [], 'Errors': []}
        category_map = {'ISIN': 'ISIN', 'CUSIP(Equity)': 'Equity','CUSIP(Fixed Income)': 'Fixed_Interest', 'PREF': 'Preferred', 'BOND': 'Fixed_Interest', 'CASH': 'Cash', 'ERROR': 'Errors'}
        for item in input_list:
            item_parts = item.split('|')
            if len(item_parts) > 1:
                category = category_map.get(item_parts[1])
                if category:
                    assets[category].append(item_parts[0])
            else:
                assets['Clean Rics'].append(item)
        
        return assets
    
    def create_list_for_export(self, assets):
        return [value for key, values in assets.items() if key not in ['Errors', 'Cash'] for value in values]

    def assign_refinitiv_code(self, input_df: pd.DataFrame) -> pd.DataFrame:
        if isinstance(input_df, pd.DataFrame):
            sorted_items = [self.refinitiv_code(portfolio) for portfolio in input_df.itertuples(index=False)]
        else:
            holdings = input_df.get('holdings', None)
            if holdings is None:
                raise ValueError("Missing 'holdings' key in input DataFrame.")
            
            # Ensure holdings is a list
            if not isinstance(holdings, list):
                holdings = holdings[0]

            sorted_items =  [self.refinitiv_code(portfolio) for portfolio in holdings]
        
        # Map the values to the correct columns
        self.category_dict = self.map_values_from_validate(sorted_items)
        self.asset_list = self.create_list_for_export(self.category_dict)
        self.errors = self.category_dict['Errors']
        self.cash = self.category_dict['Cash']
        self.fixed_interest = self.category_dict['Fixed_Interest']
        