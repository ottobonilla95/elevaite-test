from .providers.config import ( 
   model_classStr_to_class,
   validation_precedence_order
)
from .providers.rbac import RBACProvider 

# Initialize the RBAC instance
rbac_provider = RBACProvider(
   model_classStr_to_class=model_classStr_to_class,
   validation_precedence_order=validation_precedence_order
)