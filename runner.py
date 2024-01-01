# import sys
# sys.path.append(r'post-holdings\\')

import logging
import pandas as pd
import azure.functions as func
from io import StringIO
import requests
import json

from data_processor.data_processor import run

def api_connection(result_data: dict):
    url = "http://example.com/api/data"
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=json.dumps(result_data))
    
    logging.info(f"API response: {response.text}")
    #return response.json()
    return func.HttpResponse('{"result": "test", "metadata": "test"}', status_code=200)


def main():
    logging.info('Python HTTP trigger function processed a request.')

    try:

        input_data = pd.read_csv(r"postholdings\data_processor\tests\test_data\table.csv")
        input_data.drop(columns=['name'], inplace=True)

        #delete_pickle = req.params.get('delete_pickle')

        raw_input_data = pd.read_json(r'')

        # Convert rows to DataFrame
        df = pd.json_normalize(raw_input_data)

        delete_pickle = True

        # if not delete_pickle:
        #     raise ValueError("delete_pickle parameter not provided")

        result, metadata_dict = run(input_data, delete_pickle)
        #response = {"result": result, "metadata": metadata_dict}

        response = {'result': ['test', 'test2'], 
                    'metadata': {'test': 'ABC', 
                                 'test2': 'DEF'}}

        return response

    except ValueError as e:
        print(e)

    except KeyError as e:
        print(e)

    except Exception as e:
        print(e)
    
if __name__ == "__main__":
    a = main()