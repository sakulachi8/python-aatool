
# remove this when running in production
import numpy as np
import time
import pandas as pd
from datetime import datetime
from typing import Tuple

from data_processor.function_validator import RefinitivCodeValidator
from data_processor.function_perform_calculations import main as function_perform_calculations
from data_processor.function_fill_in_missing_dates import fill_in_missing_returns
#from api.function_mongodb_connection import MongoDB_Connection
from api.function_ds_extract_price import run_pipeline
from models.helpers import PickleObject #, create_hash
import hashlib, logging

def run(uniqueID, input_data:pd.DataFrame, start, end, freq, delete_pickle, risk_free_rate = 0.02, num_portfolio_cycles = 1000, comments="") -> Tuple[list,dict]:
    """Run the main function for data analysis."""
    # hash_details = f"{input_data} {start} {end} {freq} {risk_free_rate} {num_portfolio_cycles} {comments}"
    # uniqueID = hashlib.sha256((hash_details).encode()).hexdigest()
    logging.info(f"hashKey: {uniqueID}")

    #uniqueID = input_data['uniqueID'].drop_duplicates().values.tolist()[0]
    input_data = input_data[['ticker', 'quantity', 'category']].to_dict('records')
    for i in input_data:
        i['quantity'] = float(i['quantity'])

    #uniqueID = create_hash(input_data)
    name = f"portfolio_ef_{uniqueID}"
    P = PickleObject(pkl_name=name)
    
    if P.status == 'Completed' and not delete_pickle:
        return P.data[0], P.data[1]

    if P.data:
        if delete_pickle:
            P.remove_pickle()
            P
        else:
            return P.data[0], P.data[1]
    
    t = time.time()
    print(f"Running process for {name}")

    if P.status == 'No data found':
        # Validate recieved data
        validator = RefinitivCodeValidator(input_data)
        validator.assign_refinitiv_code(validator.df)


        # request price data from the database
        timeseries_df, metadata_dict, missing_items, start, end, freq = run_pipeline(validator.asset_list,  fields = ['P','X(P)~AUD', 'X(PI)~AUD', 'X(RI)~AUD'], start=start, end=end, freq=freq)
        if validator.errors:
            print(f"Error during conversion: {validator.errors}")
            return []
        delattr(validator, 'engine')
        P.save(((timeseries_df, metadata_dict, validator, missing_items), "Pipeline_completed"))

    elif P.status == 'Pipeline_completed':
        timeseries_df, metadata_dict, validator, missing_items = P.data
    
    # Fill in missing dates
    returns_df, betas, start, end = fill_in_missing_returns(input_data, timeseries_df)

    
    # add these all to metadata_dict
    for i in [('Cash', validator.cash), ('Fixed_Interest', validator.fixed_interest),('Errors', validator.errors), ('Missing_Items',missing_items)]:
        metadata_dict[i[0]] = i[1]
    
    # Perform the calcs
    results_data, weights_data, analytics, message = function_perform_calculations(returns_df, timeseries_df, risk_free_rate, num_portfolio_cycles, metadata_dict, input_data, start, end, freq, betas, uniqueID, missing_items, comments)    
    t2 = time.time()
    print(f"Time taken for data collection and EF: {round(t2-t,2)} seconds")
    P.save(((results_data, weights_data, analytics, message, metadata_dict), "Completed"))
    
    return results_data, weights_data, analytics, metadata_dict, message

# need to add to dumo to monogo

if __name__ == "__main__":
    #from tests.test_data.dict import input_data
    #load csv tests.test_data.table.csv
    import pandas as pd
    import sys
    sys.path.append(r'C:\Users\sayersqvm\Documents\Python_Scripts\AssetAllocationTool\post-holdings')
    input_data = pd.read_csv(r"data_processor\tests\test_data\table.csv")
    input_data = input_data.drop(columns=["name"])
    delete_pickle = True
    x = run(input_data, delete_pickle)
    print(x)