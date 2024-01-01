from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


db_config = {
    'server': '',
    'user': '',
    'password': ''
}
conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={db_config['server']};DATABASE=;UID={db_config['user']};PWD={db_config['password']};MARS_Connection=Yes"


engine = create_engine("")

Session = sessionmaker(bind=engine)