import os

def check_env_vars():
   if not os.getenv('REDIS_HOST'):
      raise ValueError('"REDIS_HOST" environment variable missing')
   if not os.getenv('REDIS_PORT'):
      raise ValueError('"REDIS_PORT" environment variable missing')
   if not os.getenv("SQLALCHEMY_DATABASE_URL"):
      raise ValueError('"SQLALCHEMY_DATABASE_URL" environment variable missing')
   if not os.getenv("ROOT_SUPERADMIN_EMAIL"):
      raise ValueError('"ROOT_SUPERADMIN_EMAIL" environment variable missing')
   if not os.getenv("DEFAULT_ACCOUNT_ID"):
      raise ValueError('"DEFAULT_ACCOUNT_ID" environment variable missing')
   if not os.getenv("DEFAULT_PROJECT_ID"):
      raise ValueError('"DEFAULT_PROJECT_ID" environment variable missing')
   