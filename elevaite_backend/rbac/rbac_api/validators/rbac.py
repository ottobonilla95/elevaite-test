from fastapi import Request
from sqlalchemy.orm import Session
from typing import Any, Dict, Type, Optional
from collections import OrderedDict

from elevaitedb.db import models
from elevaitedb.schemas import (
   role_schemas
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
   rbac_schema,
   model_classStr_to_class,
   validation_precedence_order,
)

class RBAC:
   
   def __init__(
      self,
      rbac_schema: Dict,
      model_classStr_to_class: Dict[str, Type[models.Base]],
      validation_precedence_order: list[Type[models.Base]],
   ):
      self._rbac_schema = rbac_schema
      self._model_classStr_to_class = model_classStr_to_class
      self._validation_precedence_order = validation_precedence_order
      self._leaf_action_paths_map,self._entity_typenames_set,self._entity_typenames_list,self._entity_typevalues_list, self._valid_entity_actions_map = self._initialize_leaf_action_paths_and_instance_type_maps()
      
   def _initialize_leaf_action_paths_and_instance_type_maps(self):
      # Perform schema validation
      self._validate_rbac_schema()
      # Populate and return the action paths map
      (leaf_action_paths_map,
      entity_typenames_set,
      entity_typenames_list,
      entity_typevalues_list,
      valid_entity_actions_map) =  self._populate_rbac_schema_info(self._rbac_schema)
      # for key,val in leaf_action_paths_map.items():
      #    pprint(f"{key} : {val}")
      #    pprint("----------")
      # pprint("X-------INSTANCE TYPENAMES TO SET--------X")
      # for key,val in instance_typenames_to_set.items():
      #    pprint(f"{key} : {val}")
      #    pprint("----------")
      # pprint("X-------INSTANCE TYPENAMES LIST--------X")
      # for key,val in instance_typenames_to_list.items():
      #    pprint(f"{key} : {val}")
      #    pprint("----------")
      # pprint("X-------VALID INSTANCE ACTIONS --------X")
      # for key,val in valid_instance_actions_map.items():
      #    pprint(f"{key} : {val}")
      #    pprint("----------")
      # pprint("X-------ENTITY TYPE VALUES LIST --------X")
      # for key,val in entity_typevalues_list.items():
      #    pprint(f"{key} : {val}")
      #    pprint("----------")
      return leaf_action_paths_map, entity_typenames_set, entity_typenames_list, entity_typevalues_list, valid_entity_actions_map
   
   def _validate_rbac_schema(self):
      try:
         permissions_instance = role_schemas.AccountScopedPermission.parse_obj(self._rbac_schema)
         print("Validation Successful")
      except ValidationError as e:
         print("input RBAC schema Validation Error:", e.json())
         raise e
      
   def _populate_rbac_schema_info(
      self,
      current_schema_obj: dict,
      current_model: Optional[Type[models.Base]] = None,
      current_types: tuple[str, ...] = (),
      current_path=[],
      current_action_sequence: list[str] = [],
      valid_entity_actions_map: dict[Type[models.Base] | None, set[tuple[str, ...]]] = {},
      leaf_action_path_map: dict = {},
      entity_typenames_set: dict[Type[models.Base] | None, set] = {},
      entity_typenames_list: dict[Type[models.Base] | None, list[str]] = {},
      entity_typevalues_list: dict[Type[models.Base] | None, list[tuple[str, ...]]] = {},
   ):
      
      for key, value in current_schema_obj.items():
         current_path.append(key)
         # print(f'current_path: {current_path}, current key : {key}')
         # Handling ENTITY_ prefixed keys to update the model
         if key.startswith("ENTITY_"):
            entity_str = key[len("ENTITY_"):]
            if entity_str not in self._model_classStr_to_class:
               raise ValueError(f"Entity '{entity_str}' does not exist in model_classStr_to_class map")
            new_model = self._model_classStr_to_class[entity_str]
   
         elif key.startswith("TYPENAMES_"):
            # Update instance type map for instance mapped to all its typenames
            instance_typenames = key[len("TYPENAMES_"):].split("__")
            entity_typenames_set[current_model] = set(instance_typenames)
            entity_typenames_list[current_model] = instance_typenames
         elif key.startswith("TYPEVALUES_"):
            typevalues: list[str] = key[len("TYPEVALUES_"):].split("__")
            if current_model not in entity_typevalues_list:
               entity_typevalues_list[current_model] = []
            entity_typevalues_list[current_model].append(tuple(typevalues))
            # Append new type, preserving previous types
            new_types = current_types + tuple(typevalues)
         elif key.startswith("ACTION_"):
            action:str = key[len("ACTION_"):]
            next_action_sequence = current_action_sequence + [action]
            if not isinstance(value, dict): # if this is a leaf action
               if not current_model in valid_entity_actions_map:
                  valid_entity_actions_map[current_model] = set()
               valid_entity_actions_map[current_model].add(tuple(next_action_sequence))
               #  save the path leading up to this 'leaf' action
               leaf_action_path_map[(current_model, tuple(current_types), tuple(next_action_sequence))] = current_path[:]
      
         # Recursively handle nested dictionaries
         if isinstance(value, dict):
            self._populate_rbac_schema_info(
               value,
               new_model if key.startswith("ENTITY_") else current_model,
               new_types if key.startswith("TYPEVALUES_") else current_types,
               current_path,
               next_action_sequence if key.startswith("ACTION_") else current_action_sequence,
               valid_entity_actions_map,
               leaf_action_path_map,
               entity_typenames_set,
               entity_typenames_list,
               entity_typevalues_list
               )
            current_path.pop() # remove next-level key when coming back to prev level
         
         current_path.pop() # remove current level key when going to next key in same level
      
      current_path.append('Will be popped after returning to calling function') # compensate for popping extra element in last iteration
      return leaf_action_path_map, entity_typenames_set, entity_typenames_list,  entity_typevalues_list, valid_entity_actions_map

   async def validate_rbac(
      self,
      request: Request,
      db: Session,
      user_email: str,
      target_model_action_sequence: tuple[str, ...],
      target_model_class: Type[models.Base],
   ) -> dict[str, Any]:
      
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         raise ApiError.unauthorized("User is unauthenticated")

      # Extract parameters from the request
      params = {**request.path_params}
      
      account_id = request.headers.get('X-elevAIte-AccountId', None)
      if account_id is not None:
         params['account_id'] = account_id

      project_id = request.headers.get('X-elevAIte-ProjectId', None)
      if project_id is not None:
         params['project_id'] = project_id
      
      model_classStr_to_instanceIds = self._map_model_classStr_to_instanceIds(params)
      model_class_to_instance = await self._map_model_class_to_instances(db, model_classStr_to_instanceIds)
      
      self._validate_inter_model_associations(model_class_to_instance, params)
      logged_in_user_account_and_project_associations:dict[str, Any] = await self._validate_logged_in_user_account_and_project_associations(model_class_to_instance, logged_in_user, db)

      validation_info:dict[str,Any] = await self._validate_account_and_project_based_permissions(
         db,
         logged_in_user_account_and_project_associations,
         model_class_to_instance,
         target_model_class,
         target_model_action_sequence
      )

      converted_modelStr_instances_map = {model.__name__: instance for model, instance in model_class_to_instance.items()}
      validation_info.update(converted_modelStr_instances_map)
      validation_info.update(logged_in_user_account_and_project_associations)
      validation_info["db"] = db
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
               raise ValueError(f"Invalid model class - '{model_classStr_candidate}' - derived from parameter: {param}")
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
            raise ValueError(f"No model defined for model class: {model_classStr}")
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
         print(f'model_class = {model_class}')
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

   async def _validate_logged_in_user_account_and_project_associations(
      self,
      model_class_to_instance: dict[Type[models.Base],Type[models.Base]],
      logged_in_user: models.User,
      db: Session
   )-> dict[str, Any]:
   
      logged_in_user_account_and_project_association_info = {"logged_in_user" : logged_in_user,
                                                               "logged_in_user_account_association" : None,
                                                               "logged_in_user_project_association" : None}
      
      # Check if user is a superadmin and return early
      if logged_in_user.is_superadmin:
         return logged_in_user_account_and_project_association_info
      
      if models.Account in model_class_to_instance:
         logged_in_user_account_association = db.query(models.User_Account).filter(
            models.User_Account.user_id == logged_in_user.id, models.User_Account.account_id == model_class_to_instance[models.Account].id
         ).first()

         if not logged_in_user_account_association:
            raise ApiError.forbidden(f"you are not assigned to account - '{model_class_to_instance[models.Account].id}'")

         logged_in_user_account_and_project_association_info["logged_in_user_account_association"] = logged_in_user_account_association

         if logged_in_user_account_association.is_admin: # check if user is admin and validate early
            return logged_in_user_account_and_project_association_info
      
      if models.Project in model_class_to_instance:
         logged_in_user_project_association = db.query(models.User_Project).filter(
            models.User_Project.user_id == logged_in_user.id, models.User_Project.project_id == model_class_to_instance[models.Project].id
         ).first()

         if not logged_in_user_project_association:
            raise ApiError.forbidden(f"you are not assigned to project - '{model_class_to_instance[models.Project].id}'")

         logged_in_user_account_and_project_association_info["logged_in_user_project_association"] = logged_in_user_project_association

         parent_project_id = model_class_to_instance[models.Project].parent_project_id

         if parent_project_id and not is_user_project_association_till_root(db=db, starting_project_id=parent_project_id, user_id=logged_in_user.id):
            raise ApiError.forbidden(f"you are not assigned to one or more projects in the project hierarchy of parent project - '{parent_project_id}'")
      
      return logged_in_user_account_and_project_association_info

   async def _validate_account_and_project_based_permissions(
      self,
      db: Session, 
      logged_in_user_account_and_project_association_info: dict[str,Any], 
      model_class_to_instance: dict[Type[models.Base],Type[models.Base]], 
      target_model_class: Type[models.Base],
      target_model_action_sequence: tuple[str, ...]
   ) -> dict:
      logged_in_user = logged_in_user_account_and_project_association_info.get("logged_in_user", None)
      logged_in_user_is_superadmin = logged_in_user.is_superadmin if logged_in_user else None
      # validate early if logged in user is superadmin
      if logged_in_user_is_superadmin:
         return {}
      
      if not models.Account in model_class_to_instance:
         raise ApiError.validationerror("account_id must be provided for non-superadmin users")
      
      logged_in_user_account_association = logged_in_user_account_and_project_association_info.get("logged_in_user_account_association", None)
      logged_in_user_is_account_admin = logged_in_user_account_association.is_admin if logged_in_user_account_association else None
      # validate early if logged in user is account admin
      if logged_in_user_is_account_admin:
         return {}
      
      logged_in_user_account_association_id = logged_in_user_account_association.id if logged_in_user_account_association else None

      # Iterate through the validation order for "READ" permission
      cumulative_typevalues_sequence = []
      cumulative_typenames_sequence = []
      is_target_model_class_visited = False
      permission_validation_info = dict()

      for model_class in self._validation_precedence_order:
         if model_class in model_class_to_instance:
            if model_class is target_model_class:
               is_target_model_class_visited = True
            instance = model_class_to_instance[model_class]
            # if not model_class is models.Project:
               # current_model_typevalues_sequence = []
            if model_class in self._entity_typenames_list:
               for model_type in self._entity_typenames_list[model_class]:
                  print(f'model_class = {model_class}, attr_name = {model_type}, attr_val = {getattr(instance, model_type)}')
                  cumulative_typevalues_sequence.append(getattr(instance, model_type))
                  cumulative_typenames_sequence.append(model_type)
         
            (read_action_account_permissions_error_msg,
            read_action_project_permissions_error_msg,
            _
            ) = self._get_model_permission_validation_info(
               model_typevalues_list=cumulative_typevalues_sequence,
               model_typenames_list=cumulative_typenames_sequence,
               model_class=model_class,
               model_action_sequence=("READ",),
               model_class_to_instance=model_class_to_instance)
            
            model_read_action_permission_path = self._get_model_permissions_path(
               model_class=model_class,
               model_types_sequence=tuple(cumulative_typevalues_sequence),
               model_action_sequence=("READ",),
            )

            if not await self._check_account_scoped_role_based_permission_exists(db, logged_in_user_account_association_id, model_read_action_permission_path, "Allow"):
               raise ApiError.forbidden(read_action_account_permissions_error_msg)

            logged_in_user_project_association = logged_in_user_account_and_project_association_info.get("logged_in_user_project_association", None)
            if logged_in_user_project_association:
               # check project-based permission overrides
               if await self._check_project_scoped_permission_overrides_exist(logged_in_user_project_association, model_read_action_permission_path):
                  raise ApiError.forbidden(read_action_project_permissions_error_msg)

      if not is_target_model_class_visited:
         if target_model_class in self._entity_typenames_list:
            for type_values in self._entity_typevalues_list[target_model_class]:
               candidate_cumulative_typevalues_sequence = cumulative_typevalues_sequence[:]
               candidate_cumulative_typenames_sequence = cumulative_typenames_sequence[:]
               for model_type, type_value in zip(self._entity_typenames_list[target_model_class], type_values):
                  print(f"target_model_class = {target_model_class}, attr_name = {model_type}, attr_val = {type_value}")
                  candidate_cumulative_typevalues_sequence.append(type_value)  # Append the type values directly from the list
                  candidate_cumulative_typenames_sequence.append(model_type)
         
               (target_action_account_permissions_error_msg,
               target_action_project_permissions_error_msg,
               validation_info_key
               ) = self._get_model_permission_validation_info(
                  model_typevalues_list=candidate_cumulative_typevalues_sequence,
                  model_typenames_list=candidate_cumulative_typenames_sequence,
                  model_class=target_model_class,
                  model_action_sequence=target_model_action_sequence,
                  model_class_to_instance=model_class_to_instance)
               
               target_model_action_permission_path = self._get_model_permissions_path(
                  model_class=target_model_class,
                  model_types_sequence=tuple(candidate_cumulative_typevalues_sequence),
                  model_action_sequence=target_model_action_sequence,
               )

               if not await self._check_account_scoped_role_based_permission_exists(db, logged_in_user_account_association_id, target_model_action_permission_path, "Allow"):
                  permission_validation_info[validation_info_key] = {"account_scoped_error_msg": target_action_account_permissions_error_msg}
               
               logged_in_user_project_association = logged_in_user_account_and_project_association_info.get("logged_in_user_project_association", None)
               if logged_in_user_project_association:
                  # check project-based permission overrides
                  if await self._check_project_scoped_permission_overrides_exist(logged_in_user_project_association, target_model_action_permission_path):
                     if validation_info_key in permission_validation_info:
                        permission_validation_info[validation_info_key]["project_scoped_error_msg"] = target_action_project_permissions_error_msg
            return permission_validation_info

         else:
            (target_action_account_permissions_error_msg,
               target_action_project_permissions_error_msg,
               validation_info_key
            ) = self._get_model_permission_validation_info(
               model_typevalues_list=cumulative_typevalues_sequence,
               model_typenames_list=cumulative_typenames_sequence,
               model_class=target_model_class,
               model_action_sequence=target_model_action_sequence,
               model_class_to_instance=model_class_to_instance)
            
            target_model_action_permission_path = self._get_model_permissions_path(
               model_class=target_model_class,
               model_types_sequence=tuple(cumulative_typevalues_sequence),
               model_action_sequence=target_model_action_sequence,
            )
            if not await self._check_account_scoped_role_based_permission_exists(db, logged_in_user_account_association_id, target_model_action_permission_path, "Allow"):
               raise ApiError.forbidden(target_action_account_permissions_error_msg)
               
            logged_in_user_project_association = logged_in_user_account_and_project_association_info.get("logged_in_user_project_association", None)
            if logged_in_user_project_association:
               # check project-based permission overrides
               if await self._check_project_scoped_permission_overrides_exist(logged_in_user_project_association, target_model_action_permission_path):
                  raise ApiError.forbidden(target_action_project_permissions_error_msg)
      else:
         if target_model_action_sequence != ("READ",): 
            (target_action_account_permissions_error_msg,
            target_action_project_permissions_error_msg,
            _
            ) = self._get_model_permission_validation_info(
                     model_typevalues_list=cumulative_typevalues_sequence,
                     model_typenames_list=cumulative_typenames_sequence,
                     model_class=target_model_class,
                     model_action_sequence=target_model_action_sequence,
                     model_class_to_instance=model_class_to_instance)
            
            target_model_action_permission_path = self._get_model_permissions_path(
                  model_class=target_model_class,
                  model_types_sequence=tuple(cumulative_typevalues_sequence),
                  model_action_sequence=target_model_action_sequence,
               )# already computed read permissions
            if not await self._check_account_scoped_role_based_permission_exists(db, logged_in_user_account_association_id, target_model_action_permission_path, "Allow"):
               raise ApiError.forbidden(target_action_account_permissions_error_msg)

            logged_in_user_project_association = logged_in_user_account_and_project_association_info.get("logged_in_user_project_association", None)
            if logged_in_user_project_association:
               # check project-based permission overrides
               if await self._check_project_scoped_permission_overrides_exist(logged_in_user_project_association, target_model_action_permission_path):
                  raise ApiError.forbidden(target_action_project_permissions_error_msg)
            
      return {}

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
      logged_in_user_project_association,
      permission_path: list[str], 
   ) -> bool:
      if not logged_in_user_project_association.is_admin:
         # Fetch permission overrides for the logged-in non-project-admin user specific to project
         user_project_overrides = role_schemas.ProjectScopedPermission.parse_obj(logged_in_user_project_association.permission_overrides)
         if user_project_overrides:
            current_attribute = user_project_overrides
            for next_attribute in permission_path:
               if hasattr(current_attribute, next_attribute):
                  current_attribute = getattr(current_attribute, next_attribute)
               else:
                  # If the attribute does not exist, return False
                  return False
            if current_attribute == 'Deny':  
               return True
      return False
   
   def _get_model_permissions_path(
      self,
      model_class: Type[models.Base],
      model_types_sequence: tuple[str,...],
      model_action_sequence: tuple[str, ...],
   ):
      if not model_action_sequence in self._valid_entity_actions_map[model_class]:
         raise ApiError.validationerror(f"undefined action sequence - '{model_action_sequence}' - for {model_class} resource")
      
      action_path: list[str] = self._leaf_action_paths_map[(model_class, model_types_sequence, model_action_sequence)]
      print(f'action_path = {action_path}')  
      
      return action_path
   
   def _get_model_permission_validation_info(
      self,
      model_class: Type[models.Base],
      model_typenames_list: list[str],
      model_typevalues_list: list[str],
      model_action_sequence,
      model_class_to_instance
   ):
      if not model_action_sequence in self._valid_entity_actions_map[model_class]:
         raise ApiError.validationerror(f"undefined action sequence - '{model_action_sequence}' - for {model_class} resource")
      
      configurations = tuple(f'{model_typename} : {model_typevalue}'
                               for model_typename, model_typevalue in zip(model_typenames_list, model_typevalues_list))
      account_permissions_error_message =f"you do not have superadmin/account-admin privileges and you do not have account-specific role-based access permissions to perform the action sequence - '{model_action_sequence}' - on '{model_class.__name__}' resources {'with the type configurations - ' + str(configurations) + ' -' if configurations else ''} in account - {model_class_to_instance[models.Account].id}"


      if models.Project in model_class_to_instance:
         project_permissions_error_message = f"you are denied permissions to perform the action sequence - '{model_action_sequence}' - on '{model_class.__name__}' resources {'with the type configurations - ' + str(configurations) + ' -' if configurations else ''} due to project-specific permission overrides in project - '{model_class_to_instance[models.Project].id}'"
      
      validation_info_key = '_'.join(f'{typename}_{typevalue}' for typename, typevalue in zip(model_typenames_list, model_typevalues_list))
      
      return account_permissions_error_message, project_permissions_error_message if models.Project in model_class_to_instance else None, validation_info_key
   
rbac_instance = RBAC(rbac_schema, model_classStr_to_class, validation_precedence_order)



