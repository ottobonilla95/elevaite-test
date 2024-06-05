import pytest 
from unittest.mock import patch, AsyncMock, MagicMock, ANY
from .... import models
from ....auth.idp.google import (
     get_user_email_response_with_error, 
     get_user_email_response_with_success,
)
from ....fixtures.setup_initial_data import db_data
from elevaitedb.schemas import permission as permission_schemas
from .utils import mock_getenv_org_id

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
@patch("rbac_api.auth.idp.impl.requests")
async def test_get_organization_users_with_valid_access_token_not_in_redis_cache_and_authenticating_user_is_superadmin(mock_requests, mock_redis_class, client, setup_initial_data):
    
   # Mock the GoogleIDP reques.get method
   mock_response = MagicMock()
   mock_response.json.return_value = get_user_email_response_with_success(email = db_data["user1"]["email"])
   mock_requests.get.return_value = mock_response

   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = None
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance
   
   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }
   
   response = await client.request(
      method="GET",
      url='/organization/users',
      headers=headers,
   )

   token = headers["Authorization"].split(" ")[1]
   # Verify the exact call to setex
   mock_redis_instance.connection.setex.assert_called_once_with(token, 60 * 60, db_data["user1"]["email"])
   # Assert the call and return value of connection.get
   mock_redis_instance.connection.get.assert_called_once_with(token)
   assert mock_redis_instance.connection.get(token) is None
   # Assert the call of GoogleIDP requests.get
   mock_requests.get.assert_called_once_with('https://www.googleapis.com/oauth2/v1/userinfo?alt=json', headers={"Authorization": f"Bearer {token}"})
   
   assert response.status_code == 200
   actual_response_payload = response.json()

   expected_response_payload = [
      {
         "id":db_data["user1"]["id"],
         "organization_id":db_data["user1"]["organization_id"],
         "firstname":db_data["user1"]["firstname"],
         "lastname":db_data["user1"]["lastname"],
         "email":db_data["user1"]["email"],
         "is_superadmin":db_data["user1"]["is_superadmin"],
         "created_at": ANY,
         "updated_at": ANY
      },
      {
         "id":db_data["user2"]["id"],
         "organization_id":db_data["user2"]["organization_id"],
         "firstname":db_data["user2"]["firstname"],
         "lastname":db_data["user2"]["lastname"],
         "email":db_data["user2"]["email"],
         "is_superadmin":db_data["user2"]["is_superadmin"],
         "created_at": ANY,
         "updated_at": ANY
      },
      {
         "id":db_data["user3"]["id"],
         "organization_id":db_data["user3"]["organization_id"],
         "firstname":db_data["user3"]["firstname"],
         "lastname":db_data["user3"]["lastname"],
         "email":db_data["user3"]["email"],
         "is_superadmin":db_data["user3"]["is_superadmin"],
         "created_at": ANY,
         "updated_at": ANY
      },
      {
         "id":db_data["user4"]["id"],
         "organization_id":db_data["user4"]["organization_id"],
         "firstname":db_data["user4"]["firstname"],
         "lastname":db_data["user4"]["lastname"],
         "email":db_data["user4"]["email"],
         "is_superadmin":db_data["user4"]["is_superadmin"],
         "created_at": ANY,
         "updated_at": ANY
      },
      {
         "id":db_data["user5"]["id"],
         "organization_id":db_data["user5"]["organization_id"],
         "firstname":db_data["user5"]["firstname"],
         "lastname":db_data["user5"]["lastname"],
         "email":db_data["user5"]["email"],
         "is_superadmin":db_data["user5"]["is_superadmin"],
         "created_at": ANY,
         "updated_at": ANY
      }
   ]

   assert actual_response_payload == expected_response_payload
    

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
@patch("rbac_api.auth.idp.impl.requests")
async def test_get_organization_users_with_valid_access_token_in_redis_cache_and_authenticating_user_is_superadmin(mock_requests, mock_redis_class, client, setup_initial_data):
    
   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = db_data["user1"]["email"]
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance

  # Mock the GoogleIDP request.get method
   mock_response = MagicMock()
   mock_response.json.return_value = get_user_email_response_with_success(email = db_data["user1"]["email"])
   mock_requests.get.return_value = mock_response

   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }

   response = await client.request(
      method="GET",
      url='/organization/users',
      headers=headers,
   )

   token = headers["Authorization"].split(" ")[1]
   # Verify that setex is not called
   mock_redis_instance.connection.setex.assert_not_called()

   # Assert the call and return value of connection.get
   mock_redis_instance.connection.get.assert_called_once_with(token)
   assert mock_redis_instance.connection.get(token) == db_data["user1"]["email"]

   # Assert that GoogleIDP.get_user_email is not called
   mock_requests.get.assert_not_called()
   
   assert response.status_code == 200
   actual_response_payload = response.json()

   expected_response_payload = [
      {
         "id":db_data["user1"]["id"],
         "organization_id":db_data["user1"]["organization_id"],
         "firstname":db_data["user1"]["firstname"],
         "lastname":db_data["user1"]["lastname"],
         "email":db_data["user1"]["email"],
         "is_superadmin":db_data["user1"]["is_superadmin"],
         "created_at": ANY,
         "updated_at": ANY
      },
      {
         "id":db_data["user2"]["id"],
         "organization_id":db_data["user2"]["organization_id"],
         "firstname":db_data["user2"]["firstname"],
         "lastname":db_data["user2"]["lastname"],
         "email":db_data["user2"]["email"],
         "is_superadmin":db_data["user2"]["is_superadmin"],
         "created_at": ANY,
         "updated_at": ANY
      },
      {
         "id":db_data["user3"]["id"],
         "organization_id":db_data["user3"]["organization_id"],
         "firstname":db_data["user3"]["firstname"],
         "lastname":db_data["user3"]["lastname"],
         "email":db_data["user3"]["email"],
         "is_superadmin":db_data["user3"]["is_superadmin"],
         "created_at": ANY,
         "updated_at": ANY
      },
      {
         "id":db_data["user4"]["id"],
         "organization_id":db_data["user4"]["organization_id"],
         "firstname":db_data["user4"]["firstname"],
         "lastname":db_data["user4"]["lastname"],
         "email":db_data["user4"]["email"],
         "is_superadmin":db_data["user4"]["is_superadmin"],
         "created_at": ANY,
         "updated_at": ANY
      },
      {
         "id":db_data["user5"]["id"],
         "organization_id":db_data["user5"]["organization_id"],
         "firstname":db_data["user5"]["firstname"],
         "lastname":db_data["user5"]["lastname"],
         "email":db_data["user5"]["email"],
         "is_superadmin":db_data["user5"]["is_superadmin"],
         "created_at": ANY,
         "updated_at": ANY
      }
   ]

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_get_organization_users_filtered_by_users_assigned_to_existing_account_id_and_authenticating_user_is_superadmin_with_valid_access_token(mock_redis_class, client, setup_initial_data):
    
   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = db_data["user1"]["email"]
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance

   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }

   existing_account_id = db_data["account2"]["id"]
   response = await client.request(
      method="GET",
      url=f'/organization/users?account_id={existing_account_id}&assigned=true',
      headers=headers,
   )
   
   assert response.status_code == 200
   actual_response_payload = response.json()

   print(f'actual_response_payload = {actual_response_payload}')

   expected_response_payload = [
      {
         "id":db_data["user2"]["id"],
         "organization_id":db_data["user2"]["organization_id"],
         "firstname":db_data["user2"]["firstname"],
         "lastname":db_data["user2"]["lastname"],
         "email":db_data["user2"]["email"],
         "is_superadmin":db_data["user2"]["is_superadmin"],
         "created_at": ANY,
         "updated_at": ANY
      },
      {
         "id":db_data["user3"]["id"],
         "organization_id":db_data["user3"]["organization_id"],
         "firstname":db_data["user3"]["firstname"],
         "lastname":db_data["user3"]["lastname"],
         "email":db_data["user3"]["email"],
         "is_superadmin":db_data["user3"]["is_superadmin"],
         "created_at": ANY,
         "updated_at": ANY
      },
      {
         "id":db_data["user4"]["id"],
         "organization_id":db_data["user4"]["organization_id"],
         "firstname":db_data["user4"]["firstname"],
         "lastname":db_data["user4"]["lastname"],
         "email":db_data["user4"]["email"],
         "is_superadmin":db_data["user4"]["is_superadmin"],
         "created_at": ANY,
         "updated_at": ANY
      }
   ]

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")

async def test_get_organization_users_filtered_by_users_not_assigned_to_existing_account_id_and_authenticating_user_is_superadmin_with_valid_access_token(mock_redis_class, client, setup_initial_data):
    
   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = db_data["user1"]["email"]
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance

   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }

   existing_account_id = db_data["account2"]["id"]
   response = await client.request(
      method="GET",
      url=f'/organization/users?account_id={existing_account_id}&assigned=false',
      headers=headers,
   )
   
   assert response.status_code == 200
   actual_response_payload = response.json()

   expected_response_payload = [
      {
         "id":db_data["user1"]["id"],
         "organization_id":db_data["user1"]["organization_id"],
         "firstname":db_data["user1"]["firstname"],
         "lastname":db_data["user1"]["lastname"],
         "email":db_data["user1"]["email"],
         "is_superadmin":db_data["user1"]["is_superadmin"],
         "created_at": ANY,
         "updated_at": ANY
      },
      {
         "id":db_data["user5"]["id"],
         "organization_id":db_data["user5"]["organization_id"],
         "firstname":db_data["user5"]["firstname"],
         "lastname":db_data["user5"]["lastname"],
         "email":db_data["user5"]["email"],
         "is_superadmin":db_data["user5"]["is_superadmin"],
         "created_at": ANY,
         "updated_at": ANY
      }
   ]

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_get_organization_users_filtered_by_users_assigned_to_existing_account_id_and_authenticating_user_is_account_admin_with_valid_access_token(mock_redis_class, client, setup_initial_data):
    
   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = db_data["user2"]["email"]
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance
   
   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }
   
   existing_account_id = db_data["account2"]["id"]
   response = await client.request(
      method="GET",
      url=f'/organization/users?account_id={db_data["account2"]["id"]}&assigned=true',
      headers=headers,
   )

   assert response.status_code == 200
   actual_response_payload = response.json()

   expected_response_payload = [
      {
         "id":db_data["user2"]["id"],
         "organization_id":db_data["user2"]["organization_id"],
         "firstname":db_data["user2"]["firstname"],
         "lastname":db_data["user2"]["lastname"],
         "email":db_data["user2"]["email"],
         "is_superadmin":db_data["user2"]["is_superadmin"],
         "created_at": ANY,
         "updated_at": ANY
      },
      {
         "id":db_data["user3"]["id"],
         "organization_id":db_data["user3"]["organization_id"],
         "firstname":db_data["user3"]["firstname"],
         "lastname":db_data["user3"]["lastname"],
         "email":db_data["user3"]["email"],
         "is_superadmin":db_data["user3"]["is_superadmin"],
         "created_at": ANY,
         "updated_at": ANY
      },
      {
         "id":db_data["user4"]["id"],
         "organization_id":db_data["user4"]["organization_id"],
         "firstname":db_data["user4"]["firstname"],
         "lastname":db_data["user4"]["lastname"],
         "email":db_data["user4"]["email"],
         "is_superadmin":db_data["user4"]["is_superadmin"],
         "created_at": ANY,
         "updated_at": ANY
      }
   ]

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_get_organization_users_filtered_by_users_not_assigned_to_existing_account_id_and_authenticating_user_is_account_admin_with_valid_access_token(mock_redis_class, client, setup_initial_data):
    
   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = db_data["user2"]["email"]
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance
   
   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }
   
   existing_account_id = db_data["account2"]["id"]
   response = await client.request(
      method="GET",
      url=f'/organization/users?account_id={db_data["account2"]["id"]}&assigned=false',
      headers=headers,
   )

   assert response.status_code == 200
   actual_response_payload = response.json()

   expected_response_payload = [
      {
         "id":db_data["user1"]["id"],
         "organization_id":db_data["user1"]["organization_id"],
         "firstname":db_data["user1"]["firstname"],
         "lastname":db_data["user1"]["lastname"],
         "email":db_data["user1"]["email"],
         "is_superadmin":db_data["user1"]["is_superadmin"],
         "created_at": ANY,
         "updated_at": ANY
      },
      {
         "id":db_data["user5"]["id"],
         "organization_id":db_data["user5"]["organization_id"],
         "firstname":db_data["user5"]["firstname"],
         "lastname":db_data["user5"]["lastname"],
         "email":db_data["user5"]["email"],
         "is_superadmin":db_data["user5"]["is_superadmin"],
         "created_at": ANY,
         "updated_at": ANY
      }
   ]

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_get_organization_users_filtered_by_non_existent_account_id_and_authenticating_user_exists_in_db_with_valid_access_token(mock_redis_class, client, setup_initial_data):
    
   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = db_data["user3"]["email"]
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance
   
   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }
   
   non_existent_account_id = "782f314c-ce36-4740-ab7f-81bbe157c042"
   response = await client.request(
      method="GET",
      url=f'/organization/users?account_id={non_existent_account_id}',
      headers=headers,
   )

   assert response.status_code == 404
   actual_response_payload = response.json()

   expected_response_payload = {"detail": f"Account - '{non_existent_account_id}' - not found"}

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_get_organization_users_without_account_id_filter_and_authenticating_user_is_not_superadmin(mock_redis_class, client, setup_initial_data):
    
   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = db_data["user2"]["email"]
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance
   
   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }
   
   response = await client.request(
      method="GET",
      url=f'/organization/users',
      headers=headers,
   )

   assert response.status_code == 403
   actual_response_payload = response.json()

   expected_response_payload = {
      "detail": f"logged-in user - '{db_data['user2']['id']}' - does not have superadmin privileges and must provide admin account filter to read organization users"
   }

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_get_organization_users_with_existing_account_id_filter_and_authenticating_user_is_not_superadmin_and_not_account_admin(mock_redis_class, client, setup_initial_data):
    
   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = db_data["user3"]["email"]
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance
   
   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }
   
   existing_account_id = db_data["account2"]["id"]
   response = await client.request(
      method="GET",
      url=f'/organization/users?account_id={existing_account_id}',
      headers=headers,
   )

   assert response.status_code == 403
   actual_response_payload = response.json()

   expected_response_payload = {
      "detail": f"logged-in user - '{db_data['user3']['id']}' - does not have superadmin or account-admin privileges in account - '{existing_account_id}' - to read organization users"
   }

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
@patch("rbac_api.auth.idp.impl.requests")
async def test_get_organization_users_with_invalid_or_expired_access_token(mock_requests, mock_redis_class, client, setup_initial_data):
    
   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = None
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance

  # Mock the GoogleIDP request.get method
   mock_response = MagicMock()
   mock_response.json.return_value = get_user_email_response_with_error()
   mock_requests.get.return_value = mock_response

   patch_organization_payload = {
      "name": "Updated Organization Name",
      "description": "Updated organization description"
   }

   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }

   response = await client.request(
      method="GET",
      url='/organization/users',
      headers=headers,
      json=patch_organization_payload
   )

   token = headers["Authorization"].split(" ")[1]
   # Verify that setex is not called (error thrown before that)
   mock_redis_instance.connection.setex.assert_not_called()

   # Assert the call of connection.get
   mock_redis_instance.connection.get.assert_called_once_with(token)

   # Assert that GoogleIDP.get_user_email is called
   mock_requests.get.assert_called_once_with('https://www.googleapis.com/oauth2/v1/userinfo?alt=json', headers={"Authorization": f"Bearer {token}"})

   assert response.status_code == 401
   actual_response_payload = response.json()

   expected_response_payload = {"detail": "invalid or expired auth credentials"}

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_get_organization_users_with_valid_access_token_and_authenticating_user_does_not_exist_in_db(mock_redis_class, client, setup_initial_data):
    
   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = "unregistered_email"
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance

   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }

   response = await client.request(
      method="GET",
      url='/organization/users',
      headers=headers,
   )
   
   assert response.status_code == 401
   actual_response_payload = response.json()

   expected_response_payload = {"detail": "user is unauthenticated"}

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
async def test_get_organization_users_with_no_access_token(client, setup_initial_data):
    
   headers = {
      "Authorization": " ",
      "Content-Type": "application/json"
   }

   response = await client.request(
      method="GET",
      url='/organization/users',
      headers=headers,
   )
  
   assert response.status_code == 401
   actual_response_payload = response.json()

   expected_response_payload = {"detail": "Request auth header must contain bearer iDP access_token for authentication"}

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("os.getenv", side_effect=mock_getenv_org_id)
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_get_organization_users_with_non_existent_organization_and_valid_access_token_and_authenticating_user_exists_in_db(mock_redis_class, mock_os_getenv, client, setup_initial_data):
    
   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = db_data["user1"]["email"]
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance

   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }

   response = await client.request(
      method="GET",
      url='/organization/users',
      headers=headers,
   )

   mock_os_getenv.assert_called_once_with("ORGANIZATION_ID", None)
   assert response.status_code == 404
   actual_response_payload = response.json()

   expected_response_payload = {"detail": f"Organization not found"}

   assert actual_response_payload == expected_response_payload
