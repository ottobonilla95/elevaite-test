from elevaitelib.schemas import (
    auth as auth_schemas,
)
from .impl import (
    GoogleIDP,
    FusionAuthIDP,
    # add other iDP impl here
)
from .interface import IDPInterface


class IDPFactory:
    @staticmethod
    def get_idp(idp_type: auth_schemas.iDPType) -> IDPInterface:
        match idp_type:
            case auth_schemas.iDPType.GOOGLE:
                return GoogleIDP()
            case auth_schemas.iDPType.CREDENTIALS:
                return FusionAuthIDP()
            case _:
                raise ValueError(f"Unsupported IDP type: {idp_type}")
