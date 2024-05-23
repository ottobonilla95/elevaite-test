from enum import Enum

class APINamespace(str , Enum):
   RBAC_API = "rbac_api"
   ETL_API = 'etl_api'
   MODEL_API = 'model_api'
   KNOWLEDGE_ENGINEERING_API = 'knowledge_engineering_api'