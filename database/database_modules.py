import logging, json
import pandas as pd

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from models.SQLalchemy import MonteCarlo, PortfolioReturns, MarketReturns, OtherData, Holdings

def get_db_session():
    db_config = {
        'server': '',
        'user': '',
        'password': ''
    }

    engine = create_engine(f"mssql+pyodbc:?driver=ODBC+Driver+17+for+SQL+Server&MARS_Connection=Yes")
    
    return sessionmaker(bind=engine)


def get_dataframe_by_hashkey(hashkey):
    Session = get_db_session()
    tables = {
        'monte_carlo': MonteCarlo, 
        'portfolio_returns': PortfolioReturns,
        'market_returns': MarketReturns,
        'other_data': OtherData
    }
    dataframes = {table_name: get_data_from_table(Session(), table_class, hashkey) for table_name, table_class in tables.items()}
    return dataframes


def get_data_from_table(session: Session, table_class: type, hashkey: str):
    query = session.query(table_class).filter(table_class.uniqueID == hashkey)
    
    # Execute the query and fetch all results
    results = query.all()

    # Create a DataFrame from the results
    df = pd.DataFrame([res.__dict__ for res in results])

    # Return the DataFrame
    return df


def load_results_to_database(results, weights_record, analytics) -> dict:
    Session = get_db_session()
    with Session() as session:
        try:
            logging.info("Loading results into the database...")
            for table in [MonteCarlo, PortfolioReturns, MarketReturns, OtherData]:
                session.query(table).filter(table.uniqueID == analytics["uniqueID"]).delete()
            session.commit()

            # use bulk_save_objects for batch inserts
            session.bulk_insert_mappings(MonteCarlo, [ 
                    {
                        "uniqueID": analytics["uniqueID"], 
                        "simulation_number": i+1, 
                        "simulated_stdev": result[0], 
                        "simulated_return": result[1], 
                        "simulated_sharpe": result[2], 
                        "simulation_weight": json.dumps(weights_record[i].tolist())
                    } for i, result in enumerate(results)
                ], return_defaults=False, render_nulls=True)
            
            session.bulk_insert_mappings(PortfolioReturns, [
                    {
                        "date": date,
                        "uniqueID": analytics["uniqueID"],
                        "asset": column,
                        "value": analytics["returns_data"].loc[date, column]
                    }
                    for column in analytics["returns_columns_raw"]
                    for date in analytics["returns_data"].index
                    if column in analytics["returns_data"].columns
                ]
            )

            session.bulk_insert_mappings(MarketReturns, [
                    {
                        "date": date,
                        "uniqueID": analytics["uniqueID"],
                        "asset": column,
                        "value": analytics["market_returns"].loc[date, column]
                    }
                    for column in analytics["market_returns_columns_raw"]
                    for date in analytics["market_returns"].index
                    if column in analytics["market_returns"].columns
                ]
            )

            other_data = OtherData(uniqueID=analytics["uniqueID"], 
                            returns_col_name=analytics["portfolio_returns_columns"],
                            market_returns_col_name=analytics["market_returns_columns"],
                            max_sharpe_weights=analytics["max_sharpe"]["weights"],
                            max_sharpe_returns=analytics["max_sharpe"]["returns"],
                            max_sharpe_volatility=analytics["max_sharpe"]["volatility"],
                            min_vol_weights=analytics["min_vol"]["weights"],
                            min_vol_returns=analytics["min_vol"]["returns"],
                            min_vol_volatility=analytics["min_vol"]["volatility"], 
                            max_target_return=analytics["efficient_frontier"]["max_target_return"],
                            returns_range=analytics["efficient_frontier"]["returns_range"],
                            efficient_portfolios_weights=analytics["efficient_portfolios"]["weights"],
                            efficient_portfolios_returns=analytics["efficient_portfolios"]["returns"],
                            efficient_portfolios_volatilities=analytics["efficient_portfolios"]["volatilities"],
                            max_drawdown=analytics["max_drawdown"],
                            betas=analytics["betas"],
                            holdings_metadata=analytics["metadata"],
                            start_date=analytics["start"],
                            end_date=analytics["end"],
                            freq=analytics["freq"],
                            risk_free_rate=analytics["risk_free_rate"],
                            num_portfolios=analytics["num_portfolios"],
                            missing_assets=analytics["missing_data"],
                            comments=analytics["comments"],
                            holdings_data=analytics["holdings_data"]
                           )

            session.add(other_data)

            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            print("Failed to load data into database. Error: ", str(e))
            # handle error as appropriate for your application
        finally:
            session.close()
