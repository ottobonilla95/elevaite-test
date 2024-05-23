import logging
from contextlib import contextmanager
from fastapi import Request
import time
from functools import wraps

class Auditor:

   def __init__(self, config):
      self.logger = logging.getLogger("audit")
      self._start_time = None
      self.config = config
      self._setup_logger()

   def _setup_logger(self):
      # Create a console handler
      console_handler = logging.StreamHandler()
      console_formatter = logging.Formatter(self.config["log_format"])
      console_handler.setFormatter(console_formatter)

   #   # Create a file handler
   #   file_handler = logging.FileHandler(cls.config["log_file"])
   #   file_formatter = logging.Formatter(cls.config["log_format"])
   #   file_handler.setFormatter(file_formatter)

      # Get the logger and set the level
      logger = self.config["logger"]
      logger.setLevel(self.config["log_level"])

      # Add handlers to the logger
      logger.addHandler(console_handler)

      # logger.addHandler(file_handler)

   @contextmanager
   def audit_context(self, request: Request, methodname: str):
      logger = self.config["logger"]
      client_host = request.client.host
      request_method = request.method
      request_url = str(request.url)

      if self._start_time is None:
         self._start_time = time.time()
      
      method_start_time = time.time()
      logger.info(f"Entering {methodname} - Client: {client_host}, Request: {request_method} {request_url}")
      try:
         yield
      finally:
         method_end_time = time.time()
         method_elapsed_time = method_end_time - method_start_time
         total_elapsed_time = method_end_time - self._start_time
         logger.info(f"Exiting {methodname} - Client: {client_host}, Request: {request_method} {request_url}")
         logger.info(f"Time taken in {methodname}: {method_elapsed_time:.2f} seconds")
         logger.info(f"Elapsed time since first audit: {total_elapsed_time:.2f} seconds")

   
   def audit(self, methodname: str):
      def decorator(func):
         @wraps(func)
         async def wrapper(request: Request, *args, **kwargs):
            with self.audit_context(request, methodname):
               return await func(request, *args, **kwargs)
         return wrapper
      return decorator
   
