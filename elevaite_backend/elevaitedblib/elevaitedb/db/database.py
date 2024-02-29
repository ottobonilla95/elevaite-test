import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()
SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")
print(SQLALCHEMY_DATABASE_URL)
# SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
# SQLALCHEMY_DATABASE_URL = "postgresql://elevaite:elevaite@localhost:5433/elevaite"
# SQLALCHEMY_DATABASE_URL = "postgresql://elevaite_admin:1R_6byQw~8[[@3.101.65.253:5431/elevaite"
# SQLALCHEMY_DATABASE_URL = "postgresql://elevaite_admin:1R_6byQw~8[[@10.0.255.130:5432/elevaite"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL  # , connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
