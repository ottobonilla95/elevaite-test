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
            username=os.getenv("OPEXWISE_DB_USER"),
            password=os.getenv("OPEXWISE_DB_PASSWORD"),
            host=os.getenv("OPEXWISE_DB_HOST"),
            port=int(os.getenv("OPEXWISE_DB_PORT")),
            database=os.getenv("OPEXWISE_DB_NAME")
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

    def get_history(self, case_number: Optional[str] = None, contact_email: Optional[str] = None) -> Union[str, None]:
        if not case_number and not contact_email:
            raise ValueError("Either case_number or email must be provided")

        # query_string = """
        #     SELECT subject 
        #     FROM workflow_990_fileupload_superset_916 
        #     WHERE 1=1
        # """
        query_string = """
            SELECT 
                case_number, subject, issue, symptoms, problem, root_cause, 
                asset_name, contact_email, contact_phone, account_name, created_date, resolved_date, analysis_unique_id
            FROM workflow_990_fileupload_superset_916
            WHERE 1=1
        """
        params = {}
        query_string+="AND symptoms != :duplicate"
        params["duplicate"] = "Duplicate Case"
        if case_number:
            query_string += " AND case_number = :case_num"
            params["case_num"] = case_number
        if contact_email:
            query_string += " AND contact_email = :email"
            params["email"] = contact_email

        query_string += " ORDER BY analysis_unique_id DESC"
        query_string += " LIMIT 3"

        query = sa.text(query_string)

        with self.connector.get_session() as session:
            try:
                result = session.execute(query, params)
                # rows = result.fetchall()
                rows = [[str(i) for i in row] for row in result.fetchall()]
                return rows if rows else None
            except Exception as e:
                print(f"An error occurred: {e}")
                return None
