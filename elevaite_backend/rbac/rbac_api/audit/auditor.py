import logging

from fastapi import Request
import time
from functools import wraps

from elevaitedb.schemas import (
   api as api_schemas,
)
from .schema import (
   LogLevel,
)
class Auditor:

   def __init__(self, config):
      self.config = config
      self._setup_logger()

   def _setup_logger(self):
      logger = self.config['logger']
      # Create a console handler
      console_handler = logging.StreamHandler()
      console_formatter = logging.Formatter(self.config["log_format"])
      console_handler.setFormatter(console_formatter)
      # add handler to logger
      logger.addHandler(console_handler)

      # Set the level
      logger.setLevel(self.config["log_level"])

      # Prevent propagation to parent loggers to isolate behavior for audit to 'audit' logger only
      logger.propagate = False

   def audit(
      self,
      api_namespace: api_schemas.APINamespace
   ):
      def decorator(func):
         # Determine the module and method names
         caller_module_name = func.__module__
         caller_method_name = func.__name__
         @wraps(func)
         async def wrapper(request: Request, *args, **kwargs):
            method_start_time = None
            method_end_time = None
            log_level = None
            error_code = None
            error_msg = None
            try:
               method_start_time = time.time()
               response = await func(request, *args, **kwargs)
               method_end_time = time.time()
               log_level = LogLevel.INFO
               return response
            except Exception as e: # catch any exception, and update log level and error information in audit through request object
               method_end_time = time.time()
               log_level = LogLevel.ERROR
               error_code = getattr(e, 'status_code', None)
               error_msg = getattr(request.state, 'source_error_msg', str(e))
               raise e
            finally:
               method_elapsed_time = method_end_time - method_start_time
               access_method = getattr(request.state, 'access_method', 'N/A')
               idp = getattr(request.state, 'idp', 'N/A')
               logged_in_entity_id = getattr(request.state, 'logged_in_entity_id', 'N/A')
               client_host = request.client.host
               user_agent = request.headers.get('User-Agent', 'N/A')
               request_method = request.method
               request_url = str(request.url)

               # Initialize the audit log entry
               audit_log = {
                  "request_url" : request_url,
                  "request_method" : request_method, 
                  "client_host": client_host,
                  "user_agent": user_agent,
                  "api_namespace": api_namespace.value,
                  "module_name": caller_module_name,
                  "module_method" : caller_method_name,
                  "severity": log_level.value,
                  "access_method": access_method,
                  "idp": idp,
                  "logged_in_entity_id": logged_in_entity_id,
                  "elapsed_time": f"{method_elapsed_time:.3f} seconds"
               }
               if error_code:
                  audit_log["error_code"] = error_code 
               if error_msg:
                  audit_log["error_msg"] = error_msg
               
               logger = self.config['logger']

               match log_level:
                  case LogLevel.INFO:
                     logger.info(f"{audit_log}")
                  case LogLevel.ERROR:
                     logger.error(f"{audit_log}")
                  case _:
                     logger.info(f"{audit_log}") # default to INFO
         return wrapper
      return decorator
   
