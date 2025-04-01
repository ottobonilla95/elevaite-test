from .rbac_validator import RBACValidator
from .config import (
    model_classStr_to_class,
    validation_precedence_order,
    account_scoped_permissions as account_scoped_permissions_schema,
    project_scoped_permissions as project_scoped_permissions_schema,
    apikey_scoped_permissions as apikey_scoped_permissions_schema,
)


class RBACValidatorProvider:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = RBACValidator(
                model_classStr_to_class=model_classStr_to_class,
                validation_precedence_order=validation_precedence_order,
                account_scoped_permissions_schema=account_scoped_permissions_schema,
                project_scoped_permissions_schema=project_scoped_permissions_schema,
                apikey_scoped_permissions_schema=apikey_scoped_permissions_schema,
            )
        return cls._instance
