import time, json
from datetime import datetime
import logging
import pandas as pd
from sqlalchemy import select, update, create_engine, and_, text
from models.SQLalchemy import Notification, Holdings
from data_processor.data_processor import run
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError



logging.basicConfig(level=logging.INFO)
conection_str = ""

engine = create_engine(conection_str)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
import concurrent.futures

def process_notification(notification):
    session: Session = SessionLocal()
    try:
        t1=time.time()
        if not notification.uniqueID: raise Exception("No uniqueID found in notification")
        logging.info(f"Running analysis for new data...\n{notification.uniqueID}\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        
        #get_holdings_query = select(Holdings).where(Holdings.uniqueID == notification.uniqueID)
        #holdings = session.execute(get_holdings_query).scalars().all()
        # Query the Holdings table
        stmt = text(f"""SELECT TOP (10) [holdingID]
                ,[uniqueID]
                ,[ticker]
                ,[quantity]
                ,[category]
                ,[completed]
                ,[updated_at]
            FROM [assetallocation].[holdings]
            where uniqueID = '{notification.uniqueID}'""")
        sql_query = session.execute(stmt)
        df = pd.DataFrame(sql_query.fetchall())
        notification.params = json.loads(notification.params)[0] if notification.params else None
        #notification.params = [n.lower() for n in notification.params] # convert all keys to lowercase <-- needs testing
        #clientID = notification.clientID if hasattr(notification, 'clientID') else None
        delete_pickle = bool(notification.params['Delete_pickle']) if 'Delete_pickle' in notification.params else False
        num_portfolio_cycles = notification.params['Num_portfolio_cycles'] if 'Num_portfolio_cycles' in notification.params else 1000
        num_portfolio_cycles = notification.params['Simulations'] if 'Simulations' in notification.params else 1000
        if isinstance(num_portfolio_cycles, str): num_portfolio_cycles = int(num_portfolio_cycles)
        risk_free_rate = notification.params['Risk_free_rate'] if 'Risk_free_rate' in notification.params else 0.04
        start = notification.params['FromDate'] if 'FromDate' in notification.params else None
        end = notification.params['ToDate'] if 'ToDate' in notification.params else None
        freq = notification.params['Frequency'] if 'Frequency' in notification.params else 'M'
        comments = notification.params['Comments'] if 'Comments' in notification.params else None
        if start: start = format_date(start)
        if end: end = format_date(end)
        
        resp = run(notification.uniqueID, df, start, end, freq, delete_pickle=delete_pickle, risk_free_rate = risk_free_rate, num_portfolio_cycles = num_portfolio_cycles, comments=comments)

        t2=time.time()
        time_taken = t2-t1
        logging.info(f"Analysis completed for new data...\n{notification}\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}\nTime taken: {time_taken}")
    
        # Update processed notifications
        update_query = update(Notification).where(Notification.uniqueID == notification.uniqueID).values(status=1)
        session.execute(update_query)
        session.commit()
        logging.info(f"Updated notification status for {notification.uniqueID}..\n\nStill Listening..")
    except Exception as e:
        session.rollback()
        logging.error("Error processing notification: %s", e)
        print(e)
    finally:
        session.close()

def format_date(date_str):
    # Validating 'yyyy-mm-dd' format
    if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError:
            pass

    # Validating 'd/m/yyyy' format
    try:
        date = datetime.strptime(date_str, "%d/%m/%Y")
        return date.strftime("%Y-%m-%d")
    except ValueError:
        pass

    # Validating 'dd/mm/yyyy' format
    try:
        date = datetime.strptime(date_str, "%d/%m/%Y")
        return date.strftime("%Y-%m-%d")
    except ValueError:
        pass

    raise ValueError("Invalid date format. Please use 'yyyy-mm-dd', 'd/m/yyyy', or 'dd/mm/yyyy' format.")


def check_for_updates(unique_id):
    session: Session = SessionLocal() 
    try:
        # Select all unchecked notifications
        query = select(Notification).where(Notification.uniqueID == unique_id)
        result = session.execute(query).scalars().all()
        session.close()

        # Process notifications concurrently
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(process_notification, result)

    except SQLAlchemyError as e:
        session.rollback()
        logging.error("Error checking for updates: %s", e)
        
    except Exception as e:
        session.rollback()
        logging.error("Error checking for updates: %s", e)
    finally:
        session.close()

if __name__ == "__main__":
    logging.info("Starting to listen for updates from the asset allocation excel file...")