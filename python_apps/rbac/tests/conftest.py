import os
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../rbac_api/.env')) 
print('loaded env')

from .fixtures.database import test_engine, test_session
from .fixtures.client import app, client
from .fixtures.setup_initial_data import setup_initial_data
