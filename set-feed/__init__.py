import os
import sys
import inspect
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from json import dumps
import os
import logging
import json
import hashlib
import pyodbc
from azure.functions import HttpRequest, HttpResponse
import os, sys; sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from listner import check_for_updates




# if __name__ == "__main__":
def main(req: HttpRequest) -> HttpResponse:
    s_params = req.headers.get("Params")
    # s_params = dumps({"PortfolioName":"TestPortfolio-TESTINGAFTERBREAK","ClientID":"1099","OnConflict":"Update"})
    connection_string = (
    r''
    r''
    r''
    r''
    r''
    )
    logging.info(connection_string)

    try:
        request_body = req.get_body().decode('utf-8')
        # request_body = dumps({"ticker":"ADH","quantity":"2352","category":"Australian Equities"})
        logging.info(request_body)
        logging.info(s_params)

        hash_key = hashlib.sha256((request_body + s_params).encode()).hexdigest()
        logging.info(f"hashKey: {hash_key}")

        inserted_ids = ""
        with pyodbc.connect(connection_string) as con:
            with con.cursor() as cursor:
                logging.info("Before hitting the uspAssetallocationHoldings..")
                cursor.execute("EXEC uspAssetallocationHoldings @JsonData=?, @Params=?, @HashKey=?",(request_body, s_params, hash_key))
                logging.info("After hitting the uspAssetallocationHoldings..")
                rows = cursor.fetchall()
                for row in rows:
                    inserted_ids = row.InsertedIDs
        logging.info("Before hitting the check for updates..")
        check_for_updates()
        logging.info("After hitting the check for updates..")
        # Polling loop
        unique_id = ""
        count = 0
        with pyodbc.connect(connection_string) as con:
            with con.cursor() as cursor:
                cursor.execute("select * from [assetallocation].[notifications] where uniqueID = ?", (hash_key,))
                rows = cursor.fetchall()
                for row in rows:
                    unique_id = row.uniqueID

        response_message = unique_id
        logging.info(response_message)
        return HttpResponse(response_message, status_code=200)

    except Exception as ex:
        logging.error(str(ex))
        error_model = json.dumps({'error': str(ex)})
        logging.info(error_model)
        
        return HttpResponse(error_model, status_code=500)
