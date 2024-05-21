from fastapi import Request
from sqlalchemy.orm import Session
from abc import ABC, abstractmethod
from elevaitedb.db.models import User, Apikey

class AuthenticationInterface(ABC):
    @abstractmethod
    def authenticate(self, request: Request, db: Session)-> User | Apikey:
      """
      Authenticate access to endpoints.

      Args:
      request (Request): The incoming starlette request object

      Returns:
      user or apikey whose permissions will be evaluated

      Raises:
      NotImplementedError: If the subclass does not implement this method.
      """
      raise NotImplementedError("Authentication Subclasses must implement this method to authenticate access to endpoints")
