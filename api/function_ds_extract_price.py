
DATASTREAM_USERNAME = ''
DATASTREAM_PASSWORD = ''

import os, time, logging
from enum import Enum
from typing import List, Tuple

import pandas as pd
# from refinitiv.data.content import symbol_conversion, search
# import refinitiv.data as rd
import DatastreamDSWS as dsws
from stdnum import isin

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

def connect_to_datastream():
    ds = dsws.Datastream(username=DATASTREAM_USERNAME, password=DATASTREAM_PASSWORD)
    return ds

from typing import List, Tuple
import pandas as pd
from database.connection import engine
from sqlalchemy import text
#import pyodbc
from sqlalchemy import create_engine, or_, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, Boolean, func

def search_assets(search_values):
    
    # Define the table structure
    Base = declarative_base()

    class AssetCode(Base):
        __tablename__ = 'AssetCode'
        __table_args__ = {'schema': 'alphacalc_1'}

        CalcDate = Column(Date, primary_key=True)
        QuoteID = Column(Integer)
        InstrumentID = Column(Integer)
        RIC = Column(String)
        ISIN = Column(String)
        SEDOL = Column(String)
        ExchangeTicker = Column(String)
        CUSIP = Column(String)
        TRBCActivityCode = Column(Integer)
        
    class Asset(Base):
        __tablename__ = 'Asset'
        __table_args__ = {'schema': 'alphacalc_1'}

        QuoteID = Column(Integer, primary_key=True)
        InstrumentID = Column(Integer)
        RIC = Column(String)
        OrganizationID = Column(Integer)
        OrganizationName = Column(String)
        InstrumentTypeCode = Column(Integer)
        InstrumentName = Column(String)
        AssetCategoryCode = Column(Integer)
        ShareClass = Column(String)
        RoundLot = Column(Integer)
        HQCountryCode = Column(String)
        ExchangeCode = Column(String)
        ExchangeTicker = Column(String)
        ISIN = Column(String)
        SEDOL = Column(String)
        IsActive = Column(Boolean)
        IsPrimary = Column(Boolean)

    Session = sessionmaker(bind=engine)
    session = Session()

    latest_calc_date = session.query(func.max(AssetCode.CalcDate)).scalar()

    query = session.query(
            AssetCode.QuoteID,
            AssetCode.InstrumentID,
            AssetCode.RIC,
            AssetCode.ISIN,
            AssetCode.SEDOL,
            AssetCode.ExchangeTicker,
            AssetCode.CUSIP,
            AssetCode.TRBCActivityCode,
            Asset.OrganizationID,
            Asset.OrganizationName,
            Asset.InstrumentTypeCode,
            Asset.InstrumentName,
            Asset.AssetCategoryCode,
            Asset.ShareClass,
            Asset.RoundLot,
            Asset.HQCountryCode,
            Asset.ExchangeCode,
            Asset.IsActive,
            Asset.IsPrimary
        ).join(
            Asset, 
            and_(
                AssetCode.QuoteID == Asset.QuoteID,
                AssetCode.InstrumentID == Asset.InstrumentID,
                AssetCode.RIC == Asset.RIC,
                AssetCode.ExchangeTicker == Asset.ExchangeTicker,
                AssetCode.ISIN == Asset.ISIN,
                AssetCode.SEDOL == Asset.SEDOL
            )
        ).filter(
            AssetCode.CalcDate == latest_calc_date,
            or_(AssetCode.RIC.in_(search_values),
                AssetCode.ISIN.in_(search_values),
                AssetCode.SEDOL.in_(search_values),
                AssetCode.CUSIP.in_(search_values)
            )
        ).all()
    
    df = pd.DataFrame(query, columns=[
        'QuoteID', 'InstrumentID', 'RIC', 'ISIN', 'SEDOL', 
        'ExchangeTicker', 'CUSIP', 'TRBCActivityCode', 
        'OrganizationID', 'OrganizationName', 'InstrumentTypeCode', 
        'InstrumentName', 'AssetCategoryCode', 'ShareClass', 
        'RoundLot', 'HQCountryCode', 'ExchangeCode', 
        'ISActive', 'IsPrimary'
    ])

    rics = df['RIC'].to_list()

    result_dict = {}
    for row in query:
        key = row.RIC if row.RIC in search_values else (
            row.ISIN if row.ISIN in search_values else (
                row.SEDOL if row.SEDOL in search_values else row.CUSIP
            )
        )
        result_dict[key] = {
            'DocumentTitle': f"{row.InstrumentName}, {row.AssetCategoryCode}, {row.ExchangeCode}",
            'RIC': row.RIC
        }

    return rics, result_dict



def convert_tickers(tickers: List[str]) -> Tuple[List[str], dict]: #, from_type=RefinitivID._ALL_UNIQUE, to_type=RefinitivID.RIC
    #converted_tickers, metadata = convert_to(tickers, from_type, to_type)
    converted_tickers, metadata = search_assets(tickers)
    # if there is a NaN in any of the items, try again but return an ISIN for that item
    missing_tickers = []

    # Missing ability to convert to ISIN ####################
    # for k,v in metadata.items():
    #     if 'RIC' not in v.keys():
    #         missing_tickers.append(k)

    for key in tickers:
        if key not in list(metadata.keys()):
            missing_tickers.append(key)
    
    # if len(missing_tickers) > 0:
    #     isin_tickers, isin_metadata = convert_to(missing_tickers, from_type, RefinitivID.ISIN, "IssueISIN")
    #     converted_tickers.extend(isin_tickers)
    #     metadata.update(isin_metadata)

    # from stdnum import cusip
    # cusips=[]
    # for x in tickers:
    #     if cusip.is_valid(x):
    #         cusips.append(x)
    # if cusips:
    #     cusip_rspns, isin_metadata = convert_to(cusips, RefinitivID.CUSIP, RefinitivID.LIPPER_ID, "LIPPER_ID")
    
    for i, key in enumerate(converted_tickers):
        if pd.isna(key):
            converted_tickers.pop(i)

    adjusted_ric = ['<' + _ticker + '>' for _ticker in converted_tickers]

    return adjusted_ric, metadata, missing_tickers


def correct_headings(df:pd.DataFrame) -> pd.DataFrame:
    new_columns = df.columns.map(lambda x: tuple([val.replace('<', '').replace('>', '') for val in x]))
    df.columns = pd.MultiIndex.from_tuples(new_columns)
    df = df.droplevel(2, axis=1)
    df.rename(columns={'X(P)~AUD': 'P(AUD)', 'X(PI)~AUD': 'PI(AUD)', 'X(RI)~AUD}': 'RI(AUD)'}, level=1, inplace=True)
    return df


def get_datastream(tickers, fields, start, end, batch_size, freq):
    '''Get data from Datastream for a list of RICs, fields, start and end dates, and frequency.
    Returns a dataframe with the data, and a dictionary of metadata.

    https://developers.refinitiv.com/content/dam/devportal/api-families/eikon/datastream-web-service/documentation/manuals-and-guides/datastream-refinitiv-dsws-python_0.pdf
    
    Parameters
    ----------
    tickers : list
        List of tickers
    fields : list
        List of fields
    start : str
        Date can be relative (e.g. -10D, -2Y, 3M) or absolute (e.g. 2018-11-09) date format.
    end : str
        Date can be relative (e.g. -10D, -2Y, 3M) or absolute (e.g. 2018-11-09) date format.
    batch_size : int
        Number of RICs to request at a time
    freq : str
        Frequency of data. Frequency in the request can be specified in days (D), weeks (W), months (M), quarters (Q) or years(Y).

    example:
        ds.get_data(tickers='PCH#(VOD(P),3M)|E', start="20181101",end="-1M", freq="M")
        '''
    ds = connect_to_datastream()
    tickers = list(set(tickers)) # Remove duplicates
    data = []
    batch_data = pd.DataFrame()
    for i in range(0, len(tickers), batch_size):
        batch_tickers = tickers[i:i+batch_size]
        tickers_str = create_ticker_string(batch_tickers)
        batch_data = ds.get_data(tickers_str, fields, start, end, freq)
        if batch_data.empty:
            raise ValueError(f"Error with request: {batch_data}")
        if hasattr(batch_data, 'Value') and "$$ER" in batch_data.Value[0]:
            raise ValueError(f"Error with request: {batch_data.Value[0]}")
        data.append(batch_data)
    concat_df = pd.concat(data)
    renamed_df = correct_headings(concat_df)
    return renamed_df

def create_ticker_string(tickers:List[str]) -> str:
    return ','.join(tickers)

def run_pipeline(input_list:List[str], fields:List[str]= ['P'], start:str ="", end:str = "", freq="M", batch_size:int = 25) -> Tuple[pd.DataFrame,dict]: #, from_RefinitivID = RefinitivID._ALL_UNIQUE, to_RefinitivID = RefinitivID.RIC,
    '''Run the pipeline to get data from Datastream for a list of tickers, fields, start and end dates, and frequency.
    Returns a dataframe with the data, and a dictionary of metadata.
    '''
    rics, metadata, missing_items = convert_tickers(input_list) #, from_RefinitivID, to_RefinitivID
    
    df = get_datastream(rics, fields, start, end, batch_size, freq)
    return df, metadata, missing_items, start, end, freq

if __name__ == '__main__':
    # Example usage
    input_identifiers = ['AAPL.OQ', 'BA', 'VAS.AX', 'LP68425585', 'AIA.AX', 'AIA.NZ','AU000000ANZ3','sdhuvuhsvbdsibviusbbiuj']  # Mixed RIC and ISIN identifiers
    resp_df,_,_ = run_pipeline(input_identifiers, fields=['P','X(P)~AUD', 'X(PI)~AUD', 'X(RI)~AUD'], start = "-20Y")
    from pprint import pprint
    pprint(resp_df)
