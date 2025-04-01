import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from typing import Optional, Union
from dotenv import load_dotenv
import os

load_dotenv()

class DatabaseConnector:   
    def __init__(self):
        self.connection_url = sa.URL.create(
            drivername='postgresql+psycopg2',
            username=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")),
            database=os.getenv("DB_NAME")
        )
        self.engine = self.create_engine()

    def create_engine(self) -> Engine:
        return sa.create_engine(self.connection_url)

    def get_session(self):
        Session = sessionmaker(bind=self.engine)
        return Session()


class CaseHistoryLoader:
    
    def __init__(self, connector: DatabaseConnector):
        self.connector = connector

    def get_history(self, case_number: Optional[str] = None, email: Optional[str] = None) -> Union[str, None]:
        if not case_number and not email:
            raise ValueError("Either case_number or email must be provided")

        query_string = """
            SELECT subject 
            FROM workflow_990_fileupload_superset_916 
            WHERE 1=1
        """
        params = {}
        if case_number:
            query_string += " AND case_number = :case_num"
            params["case_num"] = case_number
        if email:
            query_string += " AND email = :email"
            params["email"] = email
        query_string += " LIMIT 1"
        query = sa.text(query_string)

        with self.connector.get_session() as session:
            try:
                result = session.execute(query, params)
                row = result.fetchone()
                return row[0] if row else None
            except Exception as e:
                print(f"An error occurred: {e}")
                return None
