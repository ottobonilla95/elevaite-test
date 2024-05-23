from typing import Dict, Any

def is_permission_subset(subset: Dict[str, Any], superset: Dict[str, Any]) -> bool:
   for key, value in subset.items():
      if key not in superset:
         return False
      if isinstance(value, dict):
         if not isinstance(superset[key], dict):
               return False
         if not is_permission_subset(value, superset[key]):
               return False
      else:
         if value != superset[key]:
               return False
   return True