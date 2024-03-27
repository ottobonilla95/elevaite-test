# from ..utils.status_codes import StatusCodes
from fastapi import HTTPException, status
from typing import Optional

class ApiError:
   @staticmethod
   def badRequest(message: str | None = None):
      if message :
         return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail = message)
      else:
         return HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    
   @staticmethod
   def unauthorized(message: str | None = None):
      if message:
         return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)
      else:
         return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

   @staticmethod
   def forbidden(message: str | None = None):
      if message:
         return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)
      else:
         return HTTPException(status_code=status.HTTP_403_FORBIDDEN)
   
   @staticmethod
   def notfound(message: str | None = None):
      if message:
         return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
      else:
         return HTTPException(status_code=status.HTTP_404_NOT_FOUND)
   
   @staticmethod
   def conflict(message: str | None = None):
      if message:
         return HTTPException(status_code=status.HTTP_409_CONFLICT, detail = message)
      else:
         return HTTPException(status_code=status.HTTP_409_CONFLICT)
      
   @staticmethod
   def validationerror(message: str | None = None):
      if message: 
         return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message)
      else:
         return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
      
   @staticmethod
   def serviceunavailable(message: str | None = None):
      if message:
         return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=message)
      else:
         return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    

  
    
   
