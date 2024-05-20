from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Session, Query
from sqlalchemy import and_

from typing import Any, Dict, Type, Optional, List, Tuple, Set, Callable
from collections import OrderedDict
from uuid import UUID

from elevaitedb.db import models
from elevaitedb.schemas import (
   permission as permission_schemas,
   auth as auth_schemas
)
from pydantic import ValidationError
from pprint import pprint
from rbac_api.app.errors.api_error import ApiError

from rbac_api.utils.funcs import (
   snake_to_camel,
   construct_jsonb_path_expression,
)
from rbac_api.utils.cte import (
   is_user_project_association_till_root,
)
from .config import (
   model_classStr_to_class,
   validation_precedence_order,
   account_scoped_permissions as account_scoped_permissions_schema,
   project_scoped_permissions as project_scoped_permissions_schema,
   apikey_scoped_permissions as apikey_scoped_permissions_schema
)

class RBACProvider:
   _instance = None

   def __new__(cls, *args, **kwargs):
      if cls._instance is None:
         cls._instance = super().__new__(cls)
      return cls._instance

   def __init__(
      self,
      model_classStr_to_class: Dict[str, Type[models.Base]],
      validation_precedence_order: List[Type[models.Base]],
   ):
      if not hasattr(self, '_initialized'):
         self._initialized = True
         self._model_classStr_to_class = model_classStr_to_class
         self._validation_precedence_order = validation_precedence_order
         self._account_scoped_permissions_schema = account_scoped_permissions_schema
         self._project_scoped_permissions_schema = project_scoped_permissions_schema     
         self._apikey_scoped_permissions_schema = apikey_scoped_permissions_schema
         
         (self._account_scoped_permissions_leaf_action_paths_map,
            self._project_scoped_permissions_leaf_action_paths_map,
            self._apikey_scoped_permissions_leaf_action_paths_map,
            self._entity_typenames_list,
            self._entity_typevalues_list,
            self._account_scoped_permissions_valid_entity_actions_map,
            self._project_scoped_permissions_valid_entity_actions_map,
            self._apikey_scoped_permissions_valid_entity_actions_map,
            self._entity_actions_to_path_params
         ) = self._initialize_rbac_instance_properties()
      
   def _initialize_rbac_instance_properties(self):
   
      # Populate and return the action paths map
      (account_scoped_permissions_leaf_action_paths_map,
      entity_to_typenames_list,
      entity_to_typevalues_list,
      account_scoped_permissions_valid_entity_actions_map,
      entity_actions_to_path_params) =  self._populate_rbac_schema_info(self._account_scoped_permissions_schema)
      # pprint("X-------ACCOUNT SCOPED PERMISSIONS LEAF ACTION PATHS MAP--------X")
      # for key,val in account_scoped_permissions_leaf_action_paths_map.items():
      #    pprint(f"{key} : {val}")
      #    pprint("----------")
      # pprint("X-------ENTITY TYPENAMES LIST--------X")
      # for key,val in entity_to_typenames_list.items():
      #    pprint(f"{key} : {val}")
      #    pprint("----------")
      # pprint("X-------ACCOUNT SCOPED PERMISSIONS VALID ENTITY ACTIONS --------X")
      # for key,val in account_scoped_permissions_valid_entity_actions_map.items():
      #    pprint(f"{key} : {val}")
      #    pprint("----------")
      # pprint("X-------ENTITY TYPE VALUES LIST --------X")
      # for key,val in entity_to_typevalues_list.items():
      #    pprint(f"{key} : {val}")
      #    pprint("----------")
      # pprint("X-------ENTITY ACTIONS TO PATH PARAMS SET --------X")
      # for key,val in entity_actions_to_path_params.items():
      #    pprint(f"{key} : {val}")
      #    pprint("----------")

      (project_scoped_permissions_leaf_action_paths_map,
      _,
      _,
      project_scoped_permissions_valid_entity_actions_map,
      _) =  self._populate_rbac_schema_info(self._project_scoped_permissions_schema)
      # pprint("X-------PROJECT SCOPED PERMISSIONS LEAF ACTION PATHS MAP--------X")
      # for key,val in project_scoped_permissions_leaf_action_paths_map.items():
      #    pprint(f"{key} : {val}")
      #    pprint("----------")
      # pprint("X-------PROJECT SCOPED PERMISSIONS VALID ENTITY ACTIONS --------X")
      # for key,val in project_scoped_permissions_valid_entity_actions_map.items():
      #    pprint(f"{key} : {val}")
      #    pprint("----------")

      (apikey_scoped_permissions_leaf_action_paths_map,
      _,
      _,
      apikey_scoped_permissions_valid_entity_actions_map,
      _) =  self._populate_rbac_schema_info(self._apikey_scoped_permissions_schema)

      # pprint("X-------APIKEY SCOPED PERMISSIONS LEAF ACTION PATHS MAP--------X")
      # for key,val in apikey_scoped_permissions_leaf_action_paths_map.items():
      #    pprint(f"{key} : {val}")
      #    pprint("----------")
      # pprint("X-------APIKEY SCOPED PERMISSIONS VALID ENTITY ACTIONS --------X")
      # for key,val in apikey_scoped_permissions_valid_entity_actions_map.items():
      #    pprint(f"{key} : {val}")
      #    pprint("----------")

      return (account_scoped_permissions_leaf_action_paths_map,
               project_scoped_permissions_leaf_action_paths_map,
               apikey_scoped_permissions_leaf_action_paths_map,
               entity_to_typenames_list, 
               entity_to_typevalues_list,
               account_scoped_permissions_valid_entity_actions_map,
               project_scoped_permissions_valid_entity_actions_map,
               apikey_scoped_permissions_valid_entity_actions_map,
               entity_actions_to_path_params
               )
      
   def _populate_rbac_schema_info(
      self,
      current_schema_obj: dict,
      current_cumulative_entities_in_path: list[Type[models.Base]] | None = None,
      current_cumulative_typevalues_in_path: list[tuple[str, ...]] | None = None,
      current_path=None,
      current_action_sequence: list[str] | None = None,
      valid_entity_actions_map: dict[Type[models.Base] | None, set[tuple[str, ...]]] | None = None,
      entity_actions_to_path_params: dict[tuple[Type[models.Base], tuple[str, ...]], set[Type[models.Base]]] | None = None,
      leaf_action_path_map: dict | None = None,
      entity_to_typenames_set: dict[Type[models.Base] | None, set] | None = None,
      entity_to_typenames_list: dict[Type[models.Base] | None, list[str]] | None = None,
      entity_to_typevalues_set: dict[Type[models.Base] | None, set] | None = None,
      entity_to_typevalues_list: dict[Type[models.Base] | None, list[tuple[str, ...]]] | None = None,
   ):
      # initialize default param values here; must be done this way and not in signature as the modified state for mutable types will persist in future function calls when specified in signature 
      if current_cumulative_entities_in_path is None:
        current_cumulative_entities_in_path = []
      if current_cumulative_typevalues_in_path is None:
         current_cumulative_typevalues_in_path = []
      if current_path is None:
         current_path = []
      if current_action_sequence is None:
         current_action_sequence = []
      if valid_entity_actions_map is None:
         valid_entity_actions_map = {}
      if entity_actions_to_path_params is None:
         entity_actions_to_path_params = {}
      if leaf_action_path_map is None:
         leaf_action_path_map = {}
      if entity_to_typenames_set is None:
         entity_to_typenames_set = {}
      if entity_to_typenames_list is None:
         entity_to_typenames_list = {}
      if entity_to_typevalues_set is None:
         entity_to_typevalues_set = {}
      if entity_to_typevalues_list is None:
         entity_to_typevalues_list = {}

      for key, value in current_schema_obj.items():
         current_path.append(key) 
         current_entity = current_cumulative_entities_in_path[-1] if current_cumulative_entities_in_path else None
         IS_ENTITY_KEY, IS_TYPEVALUES_KEY, IS_TYPEVALUES_KEY, IS_ACTION_KEY = False, False, False, False

         if key.startswith("ENTITY_"): # model name delimited with 'ENTITY_' prefix
            IS_ENTITY_KEY = True
            next_entity_str = key[len("ENTITY_"):]
            if next_entity_str not in self._model_classStr_to_class:
               raise ValueError(f"Entity '{next_entity_str}' does not exist in model_classStr_to_class map")
            if current_entity and current_entity not in entity_to_typevalues_list: # if the current entity traversed so far didn't have any types, update cumulative typevalues with empty tuple
               current_cumulative_typevalues_in_path.append(tuple())
            next_entity = self._model_classStr_to_class[next_entity_str]
            current_cumulative_entities_in_path.append(next_entity)

         elif key.startswith("TYPENAMES_"):  # model typenames delimited with 'TYPENAMES_' prefix
            # Update entity type map for entity mapped to all its typenames
            entity_typenames = key[len("TYPENAMES_"):].split("__")
            if current_entity not in entity_to_typenames_set:
               entity_to_typenames_set[current_entity] = set(entity_typenames)
               entity_to_typenames_list[current_entity] = entity_typenames

         elif key.startswith("TYPEVALUES_"): # model typevalues delimited with 'TYPEVALUES_' prefix
            IS_TYPEVALUES_KEY = True
            typevalues: list[str] = key[len("TYPEVALUES_"):].split("__")
            if current_entity not in entity_to_typevalues_set:
               entity_to_typevalues_list[current_entity] = []
               entity_to_typevalues_set[current_entity] = set()
            
            hashable_typevalues = tuple(typevalues)
            if hashable_typevalues not in entity_to_typevalues_set[current_entity]:
               entity_to_typevalues_list[current_entity].append(hashable_typevalues)
               entity_to_typevalues_set[current_entity].add(hashable_typevalues)

            current_cumulative_typevalues_in_path.append(hashable_typevalues) 

         elif key.startswith("ACTION_"): # model action delimited with 'ACTION_' prefix
            IS_ACTION_KEY = True
            action:str = key[len("ACTION_"):]
            current_action_sequence.append(action) 

            if not isinstance(value, dict): # if this is a leaf action
               current_entity = current_cumulative_entities_in_path[-1]
               if not current_entity in valid_entity_actions_map:
                  valid_entity_actions_map[current_entity] = set()
               valid_entity_actions_map[current_entity].add(tuple(current_action_sequence))
               
               if current_entity not in entity_to_typevalues_list: # if the leaf entity didn't have any types, update cumulative typevalues with empty tuple to account for its empty type
                  current_cumulative_typevalues_in_path.append(tuple()) 

               leaf_action_path_map[(tuple(current_cumulative_entities_in_path), tuple(current_cumulative_typevalues_in_path), tuple(current_action_sequence))] = current_path[:] #  save the path leading up to this 'leaf' action, with the cumulative entity and cumulative typevalues sequences which uniquely identify this path
               entity_actions_to_path_params[(current_entity, tuple(current_action_sequence))] = set(current_cumulative_entities_in_path)
                                                                                                   
               if current_entity not in entity_to_typevalues_list: # pop the empty type when stepping out of leaf action
                  current_cumulative_typevalues_in_path.pop() 
         else:
            raise ValueError(f"Not all of schema keys are prefixed with one of 'ENTITY_', 'TYPENAMES_', 'TYPEVALUES_', 'ACTION_'")
         
         # Recursively handle nested dictionaries
         if isinstance(value, dict):
            self._populate_rbac_schema_info(
               value,
               current_cumulative_entities_in_path,
               current_cumulative_typevalues_in_path,
               current_path,
               current_action_sequence,
               valid_entity_actions_map,
               entity_actions_to_path_params,
               leaf_action_path_map,
               entity_to_typenames_set,
               entity_to_typenames_list,
               entity_to_typevalues_set,
               entity_to_typevalues_list
               )
         
         current_path.pop() # remove current level key when going to next key in same level, or when returning to calling function
         
         # remove item according to key being iterated out of or backtracked from
         if IS_ACTION_KEY:
            current_action_sequence.pop() 
         elif IS_TYPEVALUES_KEY:
            current_cumulative_typevalues_in_path.pop()
         elif IS_ENTITY_KEY:
            if current_entity and current_entity not in entity_to_typevalues_list: 
               current_cumulative_typevalues_in_path.pop()
            current_cumulative_entities_in_path.pop()

      return leaf_action_path_map, entity_to_typenames_list,  entity_to_typevalues_list, valid_entity_actions_map, entity_actions_to_path_params

   async def evaluate_rbac_permissions(
      self,
      logged_in_user: models.User,
      account_id: Optional[UUID],
      project_id: Optional[UUID],
      permissions_evaluation_request : auth_schemas.PermissionsEvaluationRequest,
      db: Session,
   )-> auth_schemas.PermissionsEvaluationResponse:
      
      account_and_project_params = {}
      if account_id is not None:
         account_and_project_params['account_id'] = account_id
      if project_id is not None:
         account_and_project_params["project_id"] = project_id
      
      model_classStr_to_instanceIds = self._map_model_classStr_to_instanceIds(account_and_project_params)
      model_class_to_instance = await self._map_model_class_to_instances(db, model_classStr_to_instanceIds)

      if project_id and not account_id: # if only project_id provided and not account_id, derive account_id from project and update map
         model_class_to_instance.update(await self._map_model_class_to_instances(db, {'Account' : model_class_to_instance[models.Project].account_id}))
         account_and_project_params.update({'account_id' : model_class_to_instance[models.Project].account_id})

      # print(f'model_class_to_instance = {model_class_to_instance}')
      self._validate_inter_model_associations(model_class_to_instance, account_and_project_params)
      logged_in_user_account_and_project_associations:dict[str, Any] = await self._validate_logged_in_entity_account_and_project_associations(model_class_to_instance, logged_in_user, db)

      # Initialize the response
      response_data = {}
      permissions_evaluation_request_dict = permissions_evaluation_request.dict()
      for field_name in permissions_evaluation_request_dict.keys():
         field_value = permissions_evaluation_request_dict[field_name]
         if field_value is None: continue
         try:
            match field_name:
               case "IS_PROJECT_ADMIN":
                  if not models.Project in model_class_to_instance:
                     raise ApiError.validationerror("X-elevAIte-ProjectId header is required to evaluate 'IS_PROJECT_ADMIN' permissions for user")
                  logged_in_user_project_association = logged_in_user_account_and_project_associations.get("logged_in_user_project_association", None)
                  response_data[field_name] = {"OVERALL_PERMISSIONS" : logged_in_user_project_association.is_admin if logged_in_user_project_association else False}
               case "IS_ACCOUNT_ADMIN":
                  if not models.Account in model_class_to_instance:
                     raise ApiError.validationerror("X-elevAIte-AccountId or X-elevAIte-ProjectId header is required to evaluate 'IS_ACCOUNT_ADMIN' permissions for user")
                  logged_in_user_account_association = logged_in_user_account_and_project_associations.get("logged_in_user_account_association", None)
                  response_data[field_name] = {"OVERALL_PERMISSIONS": logged_in_user_account_association.is_admin if logged_in_user_account_association else False}
               case _:
                  # Parse the field name to get the model class and action sequence
                  target_model_class_str, target_model_action_sequence = auth_schemas.PermissionsEvaluationRequest.parse_model_type_and_action_sequence(field_name)
                  target_model_class_str = target_model_class_str.lower().capitalize()
                  # print(f'target_model_class_str = {target_model_class_str}, target_model_action_sequence = {target_model_action_sequence}')
                  target_model_class = self._model_classStr_to_class.get(target_model_class_str, None)
                  if not target_model_class:
                     print(f'in rbac.validate_rbac_permissions : no target class found for target_model_class_str = {target_model_class_str}')
                     raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
                  if not target_model_action_sequence in self._account_scoped_permissions_valid_entity_actions_map[target_model_class]:
                     print(f'in rbac.validate_rbac_permissions : target model action sequence - "{target_model_action_sequence}" - not found in valid_entity_actions_map')
                     raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
                  
      
                  MODEL_ACTION_IS_ONLY_ACCOUNT_SCOPED: bool = False
                  # validate account/project endpoint params requirements met or not based on action scope
                  if auth_schemas.PermissionsEvaluationRequest.validate_permission_scope(field_name, auth_schemas.RBACPermissionScope.ACCOUNT_SCOPE) and auth_schemas.PermissionsEvaluationRequest.validate_permission_scope(field_name, auth_schemas.RBACPermissionScope.PROJECT_SCOPE): # if endpoint supports account scoped and project scoped actions
                     if not logged_in_user.is_superadmin and not models.Account in model_class_to_instance:
                        raise ApiError.validationerror(f"X-elevAIte-AccountId is required to evaluate {field_name} permissions for user")
                  elif auth_schemas.PermissionsEvaluationRequest.validate_permission_scope(field_name, auth_schemas.RBACPermissionScope.ACCOUNT_SCOPE): # if endpoint only supports account scoped actions
                     if not logged_in_user.is_superadmin and not models.Account in model_class_to_instance:
                        raise ApiError.validationerror(f"X-elevAIte-AccountId is required to evaluate {field_name} permissions for user")
                     MODEL_ACTION_IS_ONLY_ACCOUNT_SCOPED = True
                  else: # endpoint action is only project scoped
                     if not logged_in_user.is_superadmin:
                        logged_in_user_account_association = logged_in_user_account_and_project_associations.get("logged_in_user_account_association", None)
                        if not (logged_in_user_account_association.is_admin if logged_in_user_account_association else False) and not models.Project in model_class_to_instance:
                           raise ApiError.validationerror(f"X-elevAIte-ProjectId is required to evaluate {field_name} permissions for user")

                  # Prepare field endpoint parameters for validation
                  total_field_params = {**field_value,  **account_and_project_params}
                  # print(f'field_value = {field_value}')
                  # print(f'total_field_params = {total_field_params}')

                  # create model to instance map for field exclusive values, and check associations with id's specified in total_field_params
                  field_model_classStr_to_instanceIds = self._map_model_classStr_to_instanceIds(field_value)
                  field_model_class_to_instance = await self._map_model_class_to_instances(db, field_model_classStr_to_instanceIds)
                  self._validate_inter_model_associations(field_model_class_to_instance, total_field_params)
                  
                  # combine model to instance map for field to include account_id/project_id mappings evaluated once outside loop
                  field_model_class_to_instance.update(model_class_to_instance)
                  
                  if MODEL_ACTION_IS_ONLY_ACCOUNT_SCOPED:
                     # remove project param, if it exists, from map to be passed into permission validation function if action is only account scoped
                     field_model_class_to_instance.pop(models.Project, None)
                     
                  # print(f'field_model_class_to_instance = {field_model_class_to_instance}')

                  # Validate account-scoped and project-scoped permissions
                  validation_info = await self._validate_account_and_project_based_permissions(
                     db,
                     logged_in_user_account_and_project_associations,
                     field_model_class_to_instance,
                     target_model_class,
                     target_model_action_sequence
                  )
                  
                  logged_in_user = validation_info.get("authenticated_entity", None)
                  if logged_in_user and logged_in_user.is_superadmin:
                     response_data[field_name] = auth_schemas.EvaluatedPermissionsFactory.get_evaluated_permission(all_permissions = True, permission_field=field_name).dict()
                     continue
                  logged_in_user_account_association = validation_info.get("logged_in_entity_account_association", None)
                  if logged_in_user_account_association and logged_in_user_account_association.is_admin:
                     response_data[field_name] = auth_schemas.EvaluatedPermissionsFactory.get_evaluated_permission(all_permissions = True, permission_field=field_name).dict()
                     continue

                  overall_permissions = True

                  typenames = validation_info.get("target_entity_typename_combinations", tuple()) 
                  typevalues = validation_info.get("target_entity_typevalue_combinations", tuple()) 

                  specific_permissions = {}

                  if typenames and typevalues:
                     typenames_key = '_'.join(typenames)
                     specific_permissions[typenames_key] = {}
                     specific_permissions_unauthorized_count = 0
                     for typevalues_combination in typevalues:
                        typevalues_key = "_".join(typevalues_combination)
                        validation_key = f'ENTITY_{target_model_class.__name__}_TYPENAMES_{typenames_key}_TYPEVALUES_{typevalues_key}'
                        unauthorized_type = validation_info.get(validation_key)
                        
                        specific_permissions[typenames_key][typevalues_key] = True

                        # Now we check if the type is unauthorized and set specific permissions to false
                        if unauthorized_type:
                           specific_permissions_unauthorized_count += 1 
                           specific_permissions[typenames_key][typevalues_key] = False
                     
                     if specific_permissions_unauthorized_count == len(typevalues):
                        overall_permissions = False
                  
                  response_data[field_name] = {
                     "OVERALL_PERMISSIONS" : overall_permissions
                  }

                  if specific_permissions:
                     response_data[field_name]['SPECIFIC_PERMISSIONS'] = specific_permissions
                 
         except HTTPException as e:
            if e.status_code == status.HTTP_403_FORBIDDEN:
               response_data[field_name] = {
                  "OVERALL_PERMISSIONS" : False
               }
            else:
               raise e

      return auth_schemas.PermissionsEvaluationResponse.parse_obj(response_data)

   async def validate_rbac_permissions(
      self,
      request,
      db: Session,
      authenticated_entity: models.User | models.Apikey,
      target_model_action_sequence: tuple[str, ...],
      target_model_class: Type[models.Base],
   ) -> dict[str, Any]:
      params = {**request.path_params}
      
      if not 'account_id' in request.path_params and not 'project_id' in request.path_params: # if account_id in path params or project_id in path params (account can be derived from project), dont consider account_id header
         if hasattr(request.state, 'account_context_exists') and request.state.account_context_exists: # if endpoint has account context, consider account header
            account_id = request.headers.get('X-elevAIte-AccountId', None)
            if account_id is not None:
               params['account_id'] = account_id

      if not 'project_id' in request.path_params:  # if project_id in path params, dont consider project header
         if hasattr(request.state, 'project_context_exists') and request.state.project_context_exists: # if endpoint has project context, consider project header
            project_id = request.headers.get('X-elevAIte-ProjectId', None) 
            if project_id is not None:
               params['project_id'] = project_id

      # create params dict only accounting for account and project 
      account_and_project_params = {}
      if 'account_id' in params:
         account_and_project_params['account_id'] = params['account_id']
      if 'project_id' in params:
         account_and_project_params['project_id'] = params['project_id']
      
      # make maps only considering params for account and project if provided, to prepare for validate logged-in user's account and project associations
      model_classStr_to_instanceIds = self._map_model_classStr_to_instanceIds(account_and_project_params)
      model_class_to_instance = await self._map_model_class_to_instances(db, model_classStr_to_instanceIds) 

      if 'project_id' in account_and_project_params and not 'account_id' in account_and_project_params: # if only project_id provided and not account_id, extract account_id from project and update map
         model_class_to_instance.update(await self._map_model_class_to_instances(db, {'Account' : model_class_to_instance[models.Project].account_id}))
         params.update({'account_id' : model_class_to_instance[models.Project].account_id})
         account_and_project_params.update({'account_id' : model_class_to_instance[models.Project].account_id})

      # do an inter-modal association check for only account and project instances
      self._validate_inter_model_associations(model_class_to_instance, account_and_project_params) 

      # validate authenticated entity's account and project association check before proceeding to validate intermodal checks for other params
      logged_in_entity_account_and_project_associations:dict[str, Any] = await self._validate_logged_in_entity_account_and_project_associations(model_class_to_instance, authenticated_entity, db)
      
      ## Update maps with rest of params here to prepare for validate intermodal associations with rest of params.
      model_classStr_to_instanceIds.update(self._map_model_classStr_to_instanceIds(params))
      model_class_to_instance.update(await self._map_model_class_to_instances(db, model_classStr_to_instanceIds))

      self._validate_inter_model_associations(model_class_to_instance, params)  

      validation_info:dict[str,Any] = await self._validate_account_and_project_based_permissions(
         db,
         logged_in_entity_account_and_project_associations,
         model_class_to_instance,
         target_model_class,
         target_model_action_sequence
      )

      converted_modelStr_instances_map = {model.__name__: instance for model, instance in model_class_to_instance.items()}
      validation_info.update(converted_modelStr_instances_map)
   
      return validation_info

   def _map_model_classStr_to_instanceIds(
      self,
      params: dict[str, Any],
   )-> dict[str, Any]:
      model_classStr_to_instanceIds = {}
      for param, value in params.items():
         if param.endswith("_id"):  # Checks if the parameter name indicates an id
            model_classStr_candidate = param[:-3].lower().capitalize()
            if model_classStr_candidate in self._model_classStr_to_class:  # Checks if the model classStr is valid based on the model map
               model_classStr_to_instanceIds[model_classStr_candidate] = value  # Adds the model and its ID to the dictionary
            else:
               print(f"in rbac._map_model_classStr_to_instanceIds : Invalid model class - '{model_classStr_candidate}' - derived from parameter: {param}")
               raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      return model_classStr_to_instanceIds
   
   async def _map_model_class_to_instances(
      self,
      db: Session,
      model_classStr_to_instanceIds: dict[str, Any],
   )-> dict[Type[models.Base], Type[models.Base]]:
      model_class_to_instance = {}
      for model_classStr, model_instance_id in model_classStr_to_instanceIds.items():
         if model_instance_id is None: 
            continue
         model = self._model_classStr_to_class.get(model_classStr)
         if not model:
            print(f"in rbac._map_model_class_to_instances : No model defined for model class: {model_classStr}")
            raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
         instance = db.query(model).filter(model.id == model_instance_id).first()
         if not instance:
            raise ApiError.notfound(f"{model_classStr} - '{model_instance_id}' - not found")
         model_class_to_instance[model] = instance
      return model_class_to_instance

   def _validate_inter_model_associations(
      self,
      model_class_to_instance: dict[Type[models.Base],Type[models.Base]],
      params: dict[str, Any],
   )-> None:
      ordered_class_to_instance = OrderedDict((k, model_class_to_instance[k]) for k in self._validation_precedence_order if k in model_class_to_instance)
      for model_class, instance in ordered_class_to_instance.items():
         # print(f'model_class = {model_class}')
         for param, value in params.items():
            # Prepare both camelCase and snake_case versions of the parameter name
            param_camel = snake_to_camel(param)
            param_snake = param  # The parameter could already be in snake_case

            # print(f'param_camel = {param_camel}')
            # print(f'param_snake = {param_snake}')
            attribute_name = param_camel if hasattr(instance, param_camel) else param_snake
            if hasattr(instance, attribute_name):
               if str(getattr(instance, attribute_name)) != str(value):
                  raise ApiError.validationerror(f"{model_class.__name__} - '{getattr(instance, 'id')}' - is not associated to {param} - '{value}'")
   
   async def _validate_logged_in_entity_account_and_project_associations(
      self,
      model_class_to_instance: dict[Type[models.Base],Type[models.Base]],
      authenticated_entity: models.User | models.Apikey,
      db: Session
   )-> dict[str, Any]:
   
      logged_in_entity_account_and_project_association_info = {"authenticated_entity" : authenticated_entity,
                                                               "logged_in_entity_account_association" : None,
                                                               "logged_in_entity_project_association" : None}
      
      if isinstance(authenticated_entity, models.User):
         logged_in_user: models.User = authenticated_entity
         if models.Account in model_class_to_instance:
            logged_in_user_account_association = db.query(models.User_Account).filter(
               models.User_Account.user_id == logged_in_user.id, models.User_Account.account_id == model_class_to_instance[models.Account].id
            ).first()

            if not logged_in_user_account_association:
               if not logged_in_user.is_superadmin:
                  raise ApiError.forbidden(f"you are not assigned to account - '{model_class_to_instance[models.Account].id}'")

            logged_in_entity_account_and_project_association_info["logged_in_entity_account_association"] = logged_in_user_account_association
         
         if models.Project in model_class_to_instance:
            logged_in_user_project_association = db.query(models.User_Project).filter(
               models.User_Project.user_id == logged_in_user.id, models.User_Project.project_id == model_class_to_instance[models.Project].id
            ).first()

            if not logged_in_user_project_association:  
               if not logged_in_user.is_superadmin and not (logged_in_user_account_association.is_admin if logged_in_user_account_association else False):
                  raise ApiError.forbidden(f"you are not assigned to project - '{model_class_to_instance[models.Project].id}'")

            logged_in_entity_account_and_project_association_info["logged_in_entity_project_association"] = logged_in_user_project_association

            if not logged_in_user.is_superadmin and not (logged_in_user_account_association.is_admin if logged_in_user_account_association else False):
               parent_project_id = model_class_to_instance[models.Project].parent_project_id
               if parent_project_id and not is_user_project_association_till_root(db=db, starting_project_id=parent_project_id, user_id=logged_in_user.id):
                  raise ApiError.forbidden(f"you are not assigned to one or more projects in the project hierarchy of parent project - '{parent_project_id}'")
      else: #  authenticated entity is Apikey
         logged_in_apikey: models.Apikey = authenticated_entity
         if not models.Project in model_class_to_instance or model_class_to_instance[models.Project].id != logged_in_apikey.project_id:
            raise ApiError.forbidden(f"your permissions are restricted to resources within project - '{logged_in_apikey.project_id}'")
         
      return logged_in_entity_account_and_project_association_info

   async def _validate_account_and_project_based_permissions(
      self,
      db: Session, 
      logged_in_entity_account_and_project_association_info: dict[str,Any],
      model_class_to_instance: dict[Type[models.Base],Type[models.Base]], 
      target_model_class: Type[models.Base],
      target_model_action_sequence: tuple[str, ...]
   ) -> dict:
      
      permission_validation_info = dict()
      permission_validation_info.update(logged_in_entity_account_and_project_association_info)

      logged_in_entity = logged_in_entity_account_and_project_association_info.get("authenticated_entity", None)
      if isinstance(logged_in_entity, models.User):
         logged_in_user_is_superadmin = logged_in_entity.is_superadmin if logged_in_entity else None
         # validate early if logged in user is superadmin
         if logged_in_user_is_superadmin:
            return permission_validation_info
         
         if not models.Account in model_class_to_instance:
            raise ApiError.forbidden("you do not have superadmin permissions and must provide an account_id")
         
         logged_in_user_account_association = logged_in_entity_account_and_project_association_info.get("logged_in_entity_account_association", None)
         logged_in_user_is_account_admin = logged_in_user_account_association.is_admin if logged_in_user_account_association else None
         # validate early if logged in user is account admin
         if logged_in_user_is_account_admin:
            return permission_validation_info
         
         logged_in_user_account_association_id = logged_in_user_account_association.id if logged_in_user_account_association else None

      cumulative_pathparam_typevalues_sequence = []
      cumulative_pathparam_typenames_sequence = []
      cumulative_pathparam_model_sequence = []

      cumulative_headerparam_typevalues_sequence = []
      cumulative_headerparam_typenames_sequence = []
      cumulative_headerparam_model_sequence = []

      is_target_model_class_visited = False

      # Iterate through the validation order for "READ" permission   
      for model_class in self._validation_precedence_order:
         if model_class in model_class_to_instance:
            if model_class is target_model_class:
               is_target_model_class_visited = True
            instance = model_class_to_instance[model_class]

            if model_class not in self._entity_actions_to_path_params[(target_model_class, ('READ',))]: # model class is from headers
               cumulative_headerparam_model_sequence.append(model_class)
      
               if model_class in self._entity_typenames_list:
                  model_typenames_sequence = []
                  model_typevalues_sequence = []
                  for model_type in self._entity_typenames_list[model_class]:
                     # print(f'model_class = {model_class}, attr_name = {model_type}, attr_val = {getattr(instance, model_type)}')
                     model_typenames_sequence.append(model_type)
                     model_typevalues_sequence.append(getattr(instance, model_type))
                  
                  cumulative_headerparam_typevalues_sequence.append(tuple(model_typevalues_sequence))
                  cumulative_headerparam_typenames_sequence.append(tuple(model_typenames_sequence))
               else:
                  cumulative_headerparam_typevalues_sequence.append(tuple())
                  cumulative_headerparam_typenames_sequence.append(tuple())

               (read_action_account_permissions_error_msg,
               read_action_project_permissions_error_msg,
               read_action_apikey_permissions_error_msg,
               _
               ) = self._get_model_permission_validation_info(
                  target_model_class=model_class,
                  model_class_sequence=cumulative_headerparam_model_sequence, 
                  model_typevalues_list=cumulative_headerparam_typevalues_sequence,
                  model_typenames_list=cumulative_headerparam_typenames_sequence,
                  model_action_sequence=("READ",),
                  model_class_to_instance=model_class_to_instance)
               
               model_read_action_permission_path = self._get_model_permissions_path(
                  authenticated_entity=logged_in_entity,
                  permissions_scope=auth_schemas.RBACPermissionScope.ACCOUNT_SCOPE,
                  target_model_class=model_class,
                  model_class_sequence=tuple(cumulative_headerparam_model_sequence),
                  model_typevalues_sequence=tuple(cumulative_headerparam_typevalues_sequence) if cumulative_headerparam_typevalues_sequence else ((),),
                  target_model_action_sequence=("READ",),
               )
            else: # model class is from path params
               cumulative_pathparam_model_sequence.append(model_class)
               if model_class in self._entity_typenames_list:
                  model_typenames_sequence = []
                  model_typevalues_sequence = []
                  for model_type in self._entity_typenames_list[model_class]:
                     # print(f'model_class = {model_class}, attr_name = {model_type}, attr_val = {getattr(instance, model_type)}')
                     model_typenames_sequence.append(model_type)
                     model_typevalues_sequence.append(getattr(instance, model_type))
                  
                  cumulative_pathparam_typevalues_sequence.append(tuple(model_typevalues_sequence))
                  cumulative_pathparam_typenames_sequence.append(tuple(model_typenames_sequence))
               else:
                  cumulative_pathparam_typevalues_sequence.append(tuple())
                  cumulative_pathparam_typenames_sequence.append(tuple())

               (read_action_account_permissions_error_msg,
               read_action_project_permissions_error_msg,
               read_action_apikey_permissions_error_msg,
               _
               ) = self._get_model_permission_validation_info(
                  target_model_class=model_class,
                  model_class_sequence= cumulative_pathparam_model_sequence,
                  model_typevalues_list=cumulative_pathparam_typevalues_sequence,
                  model_typenames_list=cumulative_pathparam_typenames_sequence,
                  model_action_sequence=("READ",),
                  model_class_to_instance=model_class_to_instance)
               
               model_read_action_permission_path = self._get_model_permissions_path(
                  authenticated_entity=logged_in_entity,
                  permissions_scope=auth_schemas.RBACPermissionScope.ACCOUNT_SCOPE,
                  target_model_class=model_class,
                  model_class_sequence=tuple(cumulative_pathparam_model_sequence),
                  model_typevalues_sequence=tuple(cumulative_pathparam_typevalues_sequence) if cumulative_pathparam_typevalues_sequence else ((),),
                  target_model_action_sequence=("READ",),
               )

            if isinstance(logged_in_entity, models.User):
               if not await self._check_account_scoped_role_based_permission_exists(db, logged_in_user_account_association_id, model_read_action_permission_path, "Allow"):
                  raise ApiError.forbidden(read_action_account_permissions_error_msg)

               logged_in_user_project_association = logged_in_entity_account_and_project_association_info.get("logged_in_entity_project_association", None)
               if logged_in_user_project_association:
                  # check project-based permission overrides
                  path_exists_in_project_scoped_permissions = True
                  try:
                     self._get_model_permissions_path(
                        authenticated_entity=logged_in_entity,
                        target_model_class=model_class,
                        permissions_scope=auth_schemas.RBACPermissionScope.PROJECT_SCOPE,
                        model_class_sequence=tuple(cumulative_pathparam_model_sequence),
                        model_typevalues_sequence=tuple(cumulative_pathparam_typevalues_sequence) if cumulative_pathparam_typevalues_sequence else ((),),
                        target_model_action_sequence=("READ",),
                     )
                  except Exception as e:  # field doesn't exist in project scoped rbac permission schema but it did in account scoped rbac permission schema, so skip it
                     path_exists_in_project_scoped_permissions = False
                  if path_exists_in_project_scoped_permissions and await self._check_project_scoped_permission_overrides_exist(logged_in_entity_account_and_project_association_info, model_read_action_permission_path):
                     raise ApiError.forbidden(read_action_project_permissions_error_msg)
            else: # if logged_in_entity is instanceof Apikey
               path_exists_in_api_scoped_permissions = True
               try:
                  self._get_model_permissions_path(
                     authenticated_entity=logged_in_entity,
                     target_model_class=model_class,
                     permissions_scope=auth_schemas.RBACPermissionScope.PROJECT_SCOPE,
                     model_class_sequence=tuple(cumulative_pathparam_model_sequence),
                     model_typevalues_sequence=tuple(cumulative_pathparam_typevalues_sequence) if cumulative_pathparam_typevalues_sequence else ((),),
                     target_model_action_sequence=("READ",),
                  )
               except Exception as e: # current permission field doesn't exist in ApiKeyScopedRBACPermission schema; assume that it is account-scoped/project-scoped model eventually leading up to an api-key scoped target model-action sequence and skip. If not, permissions will be denied when target is evaluated.
                  path_exists_in_api_scoped_permissions = False
               if path_exists_in_api_scoped_permissions and await self._check_project_scoped_permission_overrides_exist(logged_in_entity_account_and_project_association_info, model_read_action_permission_path):
                  raise ApiError.forbidden(read_action_apikey_permissions_error_msg)

      if not is_target_model_class_visited:
         cumulative_pathparam_model_sequence.append(target_model_class)
         target_model_typenames = tuple(self._entity_typenames_list[target_model_class]) if target_model_class in self._entity_typenames_list else tuple()
         target_model_typevalues = tuple(self._entity_typevalues_list[target_model_class]) if target_model_class in self._entity_typevalues_list else tuple() 
         permission_validation_info["target_entity_typename_combinations"] = target_model_typenames
         permission_validation_info["target_entity_typevalue_combinations"] = target_model_typevalues
         
         if target_model_class in self._entity_typenames_list:
            cumulative_pathparam_typenames_sequence.append(target_model_typenames)
            for type_values in self._entity_typevalues_list[target_model_class]:
               cumulative_pathparam_typevalues_sequence.append(type_values)  # Append the type values directly from the list
               
               (target_action_account_permissions_error_msg,
               target_action_project_permissions_error_msg,
               target_action_apikey_permissions_error_msg,
               validation_info_key
               ) = self._get_model_permission_validation_info(
                  target_model_class=target_model_class,
                  model_class_sequence=cumulative_pathparam_model_sequence,
                  model_typevalues_list=cumulative_pathparam_typevalues_sequence,
                  model_typenames_list=cumulative_pathparam_typenames_sequence,
                  model_action_sequence=target_model_action_sequence,
                  model_class_to_instance=model_class_to_instance)
               
               target_model_action_permission_path = self._get_model_permissions_path(
                  authenticated_entity=logged_in_entity,
                  permissions_scope=auth_schemas.RBACPermissionScope.ACCOUNT_SCOPE,
                  target_model_class=target_model_class,
                  model_class_sequence=tuple(cumulative_pathparam_model_sequence),
                  model_typevalues_sequence=tuple(cumulative_pathparam_typevalues_sequence),
                  target_model_action_sequence=target_model_action_sequence,
               )

               cumulative_pathparam_typevalues_sequence.pop() 

               if isinstance(logged_in_entity, models.User):
                  if not await self._check_account_scoped_role_based_permission_exists(db, logged_in_user_account_association_id, target_model_action_permission_path, "Allow"):
                     permission_validation_info[validation_info_key] = {"account_scoped_error_msg": target_action_account_permissions_error_msg}
                  
                  logged_in_user_project_association = logged_in_entity_account_and_project_association_info.get("logged_in_entity_project_association", None)
                  if logged_in_user_project_association:
                     # check project-based permission overrides
                     path_exists_in_project_scoped_permissions = True
                     try:
                        self._get_model_permissions_path(
                           authenticated_entity=logged_in_entity,
                           target_model_class=target_model_class,
                           permissions_scope=auth_schemas.RBACPermissionScope.PROJECT_SCOPE,
                           model_class_sequence=tuple(cumulative_pathparam_model_sequence),
                           model_typevalues_sequence=tuple(cumulative_pathparam_typevalues_sequence) if cumulative_pathparam_typevalues_sequence else ((),),
                           target_model_action_sequence=target_model_action_sequence,
                        )
                     except Exception as e: # field doesn't exist in project scoped rbac permission schema but it did in account scoped rbac permission schema, so skip it
                        path_exists_in_project_scoped_permissions = False
                     if path_exists_in_project_scoped_permissions and await self._check_project_scoped_permission_overrides_exist(logged_in_entity_account_and_project_association_info, target_model_action_permission_path):
                        if validation_info_key in permission_validation_info:
                           permission_validation_info[validation_info_key]["project_scoped_error_msg"] = target_action_project_permissions_error_msg
                        else:
                           permission_validation_info[validation_info_key] = {"project_scoped_error_msg": target_action_project_permissions_error_msg}
               else: # if logged_in_entity is instanceof Apikey
                  try:
                     path_exists_in_project_scoped_permissions = True
                     self._get_model_permissions_path(
                        authenticated_entity=logged_in_entity,
                        target_model_class=target_model_class,
                        permissions_scope=auth_schemas.RBACPermissionScope.PROJECT_SCOPE,
                        model_class_sequence=tuple(cumulative_pathparam_model_sequence),
                        model_typevalues_sequence=tuple(cumulative_pathparam_typevalues_sequence) if cumulative_pathparam_typevalues_sequence else ((),),
                        target_model_action_sequence=target_model_action_sequence,
                     )
                  except Exception as e: # target permission field doesn't exist in ApiKeyScopedRBACPermission schema; restrict project-scoped permissions
                     path_exists_in_project_scoped_permissions = False
                     if validation_info_key in permission_validation_info:
                        permission_validation_info[validation_info_key]["apikey_scoped_error_msg"] = target_action_apikey_permissions_error_msg
                     else:
                        permission_validation_info[validation_info_key] = {"apikey_scoped_error_msg": target_action_apikey_permissions_error_msg}
                  if path_exists_in_project_scoped_permissions and await self._check_project_scoped_permission_overrides_exist(logged_in_entity_account_and_project_association_info, target_model_action_permission_path):
                     if validation_info_key in permission_validation_info:
                        permission_validation_info[validation_info_key]["apikey_scoped_error_msg"] = target_action_apikey_permissions_error_msg
                     else:
                        permission_validation_info[validation_info_key] = {"apikey_scoped_error_msg": target_action_apikey_permissions_error_msg}
         else:
            cumulative_pathparam_typevalues_sequence.append(tuple())
            cumulative_pathparam_typenames_sequence.append(tuple())

            (target_action_account_permissions_error_msg,
               target_action_project_permissions_error_msg,
               target_action_apikey_permissions_error_msg,
               validation_info_key
            ) = self._get_model_permission_validation_info(
               model_class_sequence=cumulative_pathparam_model_sequence,
               model_typevalues_list=cumulative_pathparam_typevalues_sequence,
               model_typenames_list=cumulative_pathparam_typenames_sequence,
               target_model_class=target_model_class,
               model_action_sequence=target_model_action_sequence,
               model_class_to_instance=model_class_to_instance)
            
            target_model_action_permission_path = self._get_model_permissions_path(
               authenticated_entity=logged_in_entity,
               target_model_class=target_model_class,
               permissions_scope=auth_schemas.RBACPermissionScope.ACCOUNT_SCOPE,
               model_class_sequence=tuple(cumulative_pathparam_model_sequence),
               model_typevalues_sequence=tuple(cumulative_pathparam_typevalues_sequence) if cumulative_pathparam_typevalues_sequence else ((),),
               target_model_action_sequence=target_model_action_sequence,
            )
            if isinstance(logged_in_entity, models.User):
               if not await self._check_account_scoped_role_based_permission_exists(db, logged_in_user_account_association_id, target_model_action_permission_path, "Allow"):
                  raise ApiError.forbidden(target_action_account_permissions_error_msg)
                  
               logged_in_user_project_association = logged_in_entity_account_and_project_association_info.get("logged_in_entity_project_association", None)
               if logged_in_user_project_association:
                  # check project-based permission overrides
                  path_exists_in_project_scoped_permissions = True
                  try:
                     self._get_model_permissions_path(
                        authenticated_entity=logged_in_entity,
                        target_model_class=target_model_class,
                        permissions_scope=auth_schemas.RBACPermissionScope.PROJECT_SCOPE,
                        model_class_sequence=tuple(cumulative_pathparam_model_sequence),
                        model_typevalues_sequence=tuple(cumulative_pathparam_typevalues_sequence) if cumulative_pathparam_typevalues_sequence else ((),),
                        target_model_action_sequence=target_model_action_sequence,
                     )
                  except Exception as e: # field doesn't exist in project scoped rbac permission schema but it did in account scoped rbac permission schema, so skip it
                     path_exists_in_project_scoped_permissions = False
                  if path_exists_in_project_scoped_permissions and await self._check_project_scoped_permission_overrides_exist(logged_in_entity_account_and_project_association_info, target_model_action_permission_path):
                     raise ApiError.forbidden(target_action_project_permissions_error_msg)
            else: # if logged_in_entity is instanceof Apikey
               try:
                  self._get_model_permissions_path(
                     authenticated_entity=logged_in_entity,
                     target_model_class=target_model_class,
                     permissions_scope=auth_schemas.RBACPermissionScope.PROJECT_SCOPE,
                     model_class_sequence=tuple(cumulative_pathparam_model_sequence),
                     model_typevalues_sequence=tuple(cumulative_pathparam_typevalues_sequence) if cumulative_pathparam_typevalues_sequence else ((),),
                     target_model_action_sequence=target_model_action_sequence,
                  )
               except Exception as e: # target permission field doesn't exist in ApiKeyScopedRBACPermission schema; restrict project-scoped permissions
                  raise ApiError.forbidden(target_action_apikey_permissions_error_msg)
               if await self._check_project_scoped_permission_overrides_exist(logged_in_entity_account_and_project_association_info, target_model_action_permission_path):
                  raise ApiError.forbidden(target_action_apikey_permissions_error_msg)
         return permission_validation_info
      else:
         if target_model_action_sequence != ("READ",): 
            (target_action_account_permissions_error_msg,
            target_action_project_permissions_error_msg,
            target_action_apikey_permissions_error_msg,
            _
            ) = self._get_model_permission_validation_info(
                  model_typevalues_list=cumulative_pathparam_typevalues_sequence,
                  model_typenames_list=cumulative_pathparam_typenames_sequence,
                  model_class_sequence=cumulative_pathparam_model_sequence,
                  target_model_class=target_model_class,
                  model_action_sequence=target_model_action_sequence,
                  model_class_to_instance=model_class_to_instance
               )
            
            target_model_action_permission_path = self._get_model_permissions_path(
               authenticated_entity=logged_in_entity,
               target_model_class=target_model_class,
               permissions_scope=auth_schemas.RBACPermissionScope.ACCOUNT_SCOPE,
               model_class_sequence=tuple(cumulative_pathparam_model_sequence),
               model_typevalues_sequence=tuple(cumulative_pathparam_typevalues_sequence) if cumulative_pathparam_typevalues_sequence else ((),),
               target_model_action_sequence=target_model_action_sequence,
            )
            if isinstance(logged_in_entity, models.User):
               if not await self._check_account_scoped_role_based_permission_exists(db, logged_in_user_account_association_id, target_model_action_permission_path, "Allow"):
                  raise ApiError.forbidden(target_action_account_permissions_error_msg)

               logged_in_user_project_association = logged_in_entity_account_and_project_association_info.get("logged_in_entity_project_association", None)
               if logged_in_user_project_association:
                  # check project-based permission overrides
                  path_exists_in_project_scoped_permissions = True
                  try:
                     self._get_model_permissions_path(
                        authenticated_entity=logged_in_entity,
                        target_model_class=target_model_class,
                        permissions_scope=auth_schemas.RBACPermissionScope.PROJECT_SCOPE,
                        model_class_sequence=tuple(cumulative_pathparam_model_sequence),
                        model_typevalues_sequence=tuple(cumulative_pathparam_typevalues_sequence) if cumulative_pathparam_typevalues_sequence else ((),),
                        target_model_action_sequence=target_model_action_sequence,
                     )
                  except Exception as e: # field doesn't exist in project scoped rbac permission schema but it did in account scoped rbac permission schema, so skip it
                     path_exists_in_project_scoped_permissions = False
                  if path_exists_in_project_scoped_permissions and await self._check_project_scoped_permission_overrides_exist(logged_in_entity_account_and_project_association_info, target_model_action_permission_path):
                     raise ApiError.forbidden(target_action_project_permissions_error_msg)
            else: # if logged_in_entity is instanceof Apikey
               try:
                  self._get_model_permissions_path(
                     authenticated_entity=logged_in_entity,
                     target_model_class=target_model_class,
                     permissions_scope=auth_schemas.RBACPermissionScope.PROJECT_SCOPE,
                     model_class_sequence=tuple(cumulative_pathparam_model_sequence),
                     model_typevalues_sequence=tuple(cumulative_pathparam_typevalues_sequence) if cumulative_pathparam_typevalues_sequence else ((),),
                     target_model_action_sequence=target_model_action_sequence,
                  )
               except Exception as e: # target permission field doesn't exist in ApiKeyScopedRBACPermission schema; restrict project-scoped permissions
                  raise ApiError.forbidden(target_action_apikey_permissions_error_msg)
               if await self._check_project_scoped_permission_overrides_exist(logged_in_entity_account_and_project_association_info, target_model_action_permission_path):
                  raise ApiError.forbidden(target_action_apikey_permissions_error_msg)
      return permission_validation_info

   async def _check_account_scoped_role_based_permission_exists(
      self,
      db: Session, 
      logged_in_user_account_association_id,
      permission_path: list[str],
      action: str
   ) -> bool:
      # Construct the JSONB path expression for the permission check
      jsonb_path_expression = construct_jsonb_path_expression(JSONB_obj=models.Role.permissions, permission_path=permission_path, action_value=action)

      # Check if the permission exists for any of the user's roles
      permission_exists = db.query(
         db.query(models.Role)
         .join(models.Role_User_Account, models.Role_User_Account.role_id == models.Role.id)
         .filter(
               models.Role_User_Account.user_account_id == logged_in_user_account_association_id,
               jsonb_path_expression
         )
         .exists()
      ).scalar()

      return permission_exists

   async def _check_project_scoped_permission_overrides_exist(
      self,
      logged_in_entity_account_and_project_association_info: dict[str,Any],
      permission_path: list[str], 
   ) -> bool:
      logged_in_entity = logged_in_entity_account_and_project_association_info['authenticated_entity']
      logged_in_entity_is_user = True
      if isinstance(logged_in_entity, models.User):
         logged_in_user_project_association = logged_in_entity_account_and_project_association_info['logged_in_entity_project_association']
         if logged_in_user_project_association and logged_in_user_project_association.is_admin:
            return False
         try:
            project_scoped_permission_overrides = permission_schemas.ProjectScopedRBACPermission.parse_obj(logged_in_user_project_association.permission_overrides) if logged_in_user_project_association else None
         except Exception as e:
            print(f"Invalid Project_scoped_permission overrides schema for user - '{logged_in_user_project_association.user_id}' - in project - '{logged_in_user_project_association.project_id}'")
            raise e
      else: # logged_in_entity is Apikey
         logged_in_entity_is_user = False
         try:
            project_scoped_permission_overrides = permission_schemas.ApikeyScopedRBACPermission.parse_obj(logged_in_entity.permissions) if logged_in_entity else None
         except Exception as e:
            print(f"Invalid Project_scoped_permission overrides schema for apikey - '{logged_in_entity.id}' - in project - '{logged_in_entity.project_id}'")
            raise e
      if project_scoped_permission_overrides:
         current_attribute = project_scoped_permission_overrides
         for next_attribute in permission_path:
            if hasattr(current_attribute, next_attribute):
               current_attribute = getattr(current_attribute, next_attribute)
            else:
               # If the attribute does not exist, schema is malformed
               print(f"in check_project_scoped_permission_overrides_exist : logged-in {'user' if logged_in_entity_is_user else 'apikey'} - '{logged_in_entity.id}' - has malformed project permission overrides under project - '{logged_in_entity.project_id}'")
               raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
         if current_attribute == 'Deny':  
            return True
      return False
   
   def _get_model_permissions_path(
      self,
      authenticated_entity: models.User | models.Apikey,
      permissions_scope: auth_schemas.RBACPermissionScope,
      target_model_class: Type[models.Base],
      model_class_sequence,
      model_typevalues_sequence: tuple[tuple[str,...],...],
      target_model_action_sequence: tuple[str, ...],
   ):
      paths_map_input_tuple = (model_class_sequence, model_typevalues_sequence, target_model_action_sequence)
      if permissions_scope is auth_schemas.RBACPermissionScope.ACCOUNT_SCOPE:
         if not target_model_action_sequence in self._account_scoped_permissions_valid_entity_actions_map[target_model_class]:
            print(f"action sequence - '{target_model_action_sequence}' - for {target_model_class} resource not found in account-scoped-permissions schema")
            raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
         if not paths_map_input_tuple in self._account_scoped_permissions_leaf_action_paths_map:
            print(f"action path not found in account-scoped-permissions schema for target model class - '{target_model_class}' - with model class sequence - '{model_class_sequence}' - with model_type_values_sequence - '{model_typevalues_sequence}' - with target_model_action_sequence - '{target_model_action_sequence}'")
            raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
         action_path: list[str] = self._account_scoped_permissions_leaf_action_paths_map[paths_map_input_tuple]
      elif permissions_scope is auth_schemas.RBACPermissionScope.PROJECT_SCOPE:
         if isinstance(authenticated_entity, models.User):
            if not target_model_action_sequence in self._project_scoped_permissions_valid_entity_actions_map[target_model_class]:
               print(f"action sequence - '{target_model_action_sequence}' - for {target_model_class} resource not found in project-scoped-permissions schema")
               raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
            if not paths_map_input_tuple in self._project_scoped_permissions_leaf_action_paths_map:
               print(f"action path not found in project-scoped-permissions schema for target model class - '{target_model_class}' - with model class sequence - '{model_class_sequence}' - with model_type_values_sequence - '{model_typevalues_sequence}' - with target_model_action_sequence - '{target_model_action_sequence}'")
               raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
            action_path: list[str] = self._project_scoped_permissions_leaf_action_paths_map[paths_map_input_tuple]
         else: # authenticated entity is Apikey
            if not target_model_action_sequence in self._apikey_scoped_permissions_valid_entity_actions_map[target_model_class]:
               print(f"action sequence - '{target_model_action_sequence}' - for {target_model_class} resource not found in apikey-scoped-permissions schema")
               raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
            if not paths_map_input_tuple in self._apikey_scoped_permissions_leaf_action_paths_map:
               print(f"action path not found in apikey-scoped-permissions schema for target model class - '{target_model_class}' - with model class sequence - '{model_class_sequence}' - with model_type_values_sequence - '{model_typevalues_sequence}' - with target_model_action_sequence - '{target_model_action_sequence}'")
               raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
            action_path: list[str] = self._apikey_scoped_permissions_leaf_action_paths_map[paths_map_input_tuple]
      else:
         print(f"unimplemented business logic for get_model_permissions_path for scope - '{permissions_scope}'")
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      
      print(f'action_path = {action_path}')  
      return action_path
   
   def _get_model_permission_validation_info(
      self,
      target_model_class: Type[models.Base],
      model_class_sequence: list[Type[models.Base]],
      model_typenames_list: list[tuple[str, ...]],
      model_typevalues_list: list[tuple[str, ...]],
      model_action_sequence,
      model_class_to_instance
   ):
      if not model_action_sequence in self._account_scoped_permissions_valid_entity_actions_map[target_model_class]:
         print(f"undefined action sequence - '{model_action_sequence}' - for {target_model_class} resource")
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      
      # Building configuration
      configurations = tuple(
         (
            f"Resource - {model.__name__}, Types - {[', '.join(f'{typename}:{typevalue}' for typename, typevalue in zip(typenames, typevalues))]}"
            for model, typenames, typevalues in zip(model_class_sequence, model_typenames_list, model_typevalues_list)
            if any(zip(typenames, typevalues))
         )
      )

      configurations_str = '; '.join(configurations) if configurations else ''

      # account_permissions_error_message =f"you do not have superadmin/account-admin privileges and you do not have account-specific role-based access permissions to perform the action sequence - '{model_action_sequence}' - on '{target_model_class.__name__}' resources {'with the type configurations - ' + str(configurations) + ' -' if configurations else ''} in account - {model_class_to_instance[models.Account].id}"
      account_permissions_error_message = (
        f"you do not have superadmin/account-admin privileges and you do not have "
        f"account-specific role-based access permissions to perform the action sequence - '{model_action_sequence}' - "
        f"on '{target_model_class.__name__}' resources "
        f"{'under the following configurations - (' + configurations_str + ') -' if configurations else ''} "
        f"in account - {model_class_to_instance[models.Account].id}"
      )

      # Check if there's project-specific information and build relevant message
      project_permissions_error_message = None
      apikey_permissions_error_message = None
      if models.Project in model_class_to_instance:
         project_permissions_error_message = (
            f"you are denied permissions to perform the action sequence - '{model_action_sequence}' - "
            f"on '{target_model_class.__name__}' resources "
            f"{'under the following configurations - (' + configurations_str + ') -' if configurations else ''} "
            f"due to project-specific permission overrides in project - '{model_class_to_instance[models.Project].id}'"
         )
         apikey_permissions_error_message = (
            f"you are denied permissions to perform the action sequence - '{model_action_sequence}' - "
            f"on '{target_model_class.__name__}' resources "
            f"{'under the following configurations - (' + configurations_str + ') -' if configurations else ''} "
            f"due to apikey-specific permission overrides in project - '{model_class_to_instance[models.Project].id}'"
         )
      
      # Creating a validation info key with model class, typename, and typevalue
      validation_info_key = '__'.join(
        f'ENTITY_{model.__name__}_TYPENAMES_{"_".join(typenames)}_TYPEVALUES_{"_".join(typevalues)}'
        for model, typenames, typevalues in zip(model_class_sequence, model_typenames_list, model_typevalues_list)
      )
      
      return account_permissions_error_message, project_permissions_error_message, apikey_permissions_error_message,  validation_info_key
   
   def get_post_validation_types_filter_function_for_all_query(self, model_class: Type[models.Base], validation_info: Dict[str, Any]) -> Callable:

      def filter_function(query: Query) -> Query:  
         typenames = validation_info.get("target_entity_typename_combinations", tuple()) 
         typevalues = validation_info.get("target_entity_typevalue_combinations", tuple()) 

         filters_list = []
         for typevalues_combination in typevalues:
            key = f'ENTITY_{model_class.__name__}_TYPENAMES_{"_".join(typenames)}_TYPEVALUES_{"_".join(typevalues_combination)}'
            unauthorized_type = validation_info.get(key)
            
            # Now we check if the type is unauthorized and create filters for them
            if unauthorized_type:
               filters = {typename: value for typename, value in zip(typenames, typevalues_combination)}
               filters_list.append(filters)

         if filters_list:
            and_conditions = []
            for filters in filters_list:
               # Create conditions where each field must not equal the unauthorized value
               for field, value in filters.items():
                  condition = getattr(model_class, field) != value
                  and_conditions.append(condition)

            # Apply all AND conditions to the query
            if and_conditions:
               query = query.filter(and_(*and_conditions))

         return query
      return filter_function
   
   @classmethod 
   def get_instance(cls):
      if cls._instance is None:
         raise ValueError("RBACProvider not initialized. Call the constructor first.")
      return cls._instance


