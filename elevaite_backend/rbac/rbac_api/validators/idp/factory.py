from  elevaitedb.schemas import (
    auth as auth_schemas,
) 
from .impl import (
   GoogleIDP,
   # add other iDP impl here
)
from .interface import IDPInterface

class IDPFactory:
   @staticmethod
   def get_idp(idp_type: auth_schemas.iDPType) -> IDPInterface:
      match idp_type:
         case auth_schemas.iDPType.GOOGLE:
            return GoogleIDP()
         case _:
            raise ValueError(f"Unsupported IDP type: {idp_type}")
