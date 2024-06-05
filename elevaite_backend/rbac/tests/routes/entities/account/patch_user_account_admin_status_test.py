import pytest 
from unittest.mock import patch, AsyncMock, MagicMock, ANY
from .... import models
from ....auth.idp.google import (
     get_user_email_response_with_error, 
     get_user_email_response_with_success,
)
from ....fixtures.setup_initial_data import db_data
from elevaitedb.schemas import permission as permission_schemas
import uuid 

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
@patch("rbac_api.auth.idp.impl.requests")
async def test_patch_user_account_admin_status_with_existing_account_id_and_revoking_admin_status_of_assigned_admin_user_in_payload_and_valid_access_token_not_in_redis_cache_and_authenticating_user_is_superadmin(mock_requests, mock_redis_class, client, setup_initial_data):
    
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
   payload = {
      "action": "Revoke"
   }
   account_id = db_data["account2"]["id"]
   assigned_user_id = db_data["user2"]["id"]
   response = await client.request(
      method="PATCH",
      url=f'/accounts/{account_id}/users/{assigned_user_id}/admin',
      headers=headers,
      json=payload
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

   expected_response_payload = {
      "message": "Admin status successfully revoked"
   }

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
@patch("rbac_api.auth.idp.impl.requests")
async def test_patch_user_account_admin_status_with_existing_account_id_and_revoking_admin_status_of_assigned_admin_user_in_payload_and_valid_access_token_in_redis_cache_and_authenticating_user_is_superadmin(mock_requests, mock_redis_class, client, setup_initial_data):
    
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

   payload = {
      "action": "Revoke"
   }
   account_id = db_data["account2"]["id"]
   assigned_user_id = db_data["user2"]["id"]
   response = await client.request(
      method="PATCH",
      url=f'/accounts/{account_id}/users/{assigned_user_id}/admin',
      headers=headers,
      json=payload
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

   expected_response_payload = {
      "message": "Admin status successfully revoked"
   }

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_patch_user_account_admin_status_with_existing_account_id_and_granting_admin_status_of_assigned_non_admin_user_in_payload_and_valid_access_token_and_authenticating_user_is_superadmin(mock_redis_class, client, setup_initial_data):
    
   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = db_data["user1"]["email"]
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance
   
   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }

   payload = {
      "action": "Grant"
   }
   account_id = db_data["account2"]["id"]
   assigned_user_id = db_data["user3"]["id"]
   response = await client.request(
      method="PATCH",
      url=f'/accounts/{account_id}/users/{assigned_user_id}/admin',
      headers=headers,
      json=payload
   )
   
   assert response.status_code == 200
   actual_response_payload = response.json()

   expected_response_payload = {
      "message": "Admin status successfully granted"
   }

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
@patch("rbac_api.auth.idp.impl.requests")
async def test_patch_user_account_admin_status_with_existing_account_id_and_revoking_admin_status_of_assigned_admin_user_in_payload_and_valid_access_token_not_in_redis_cache_and_authenticating_user_is_account_admin(mock_requests, mock_redis_class, client, setup_initial_data):
    
   # Mock the GoogleIDP reques.get method
   mock_response = MagicMock()
   mock_response.json.return_value = get_user_email_response_with_success(email = db_data["user4"]["email"])
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
   payload = {
      "action": "Revoke"
   }
   account_id = db_data["account5"]["id"]
   assigned_user_id = db_data["user5"]["id"]
   response = await client.request(
      method="PATCH",
      url=f'/accounts/{account_id}/users/{assigned_user_id}/admin',
      headers=headers,
      json=payload
   )

   token = headers["Authorization"].split(" ")[1]
   # Verify the exact call to setex
   mock_redis_instance.connection.setex.assert_called_once_with(token, 60 * 60, db_data["user4"]["email"])
   # Assert the call and return value of connection.get
   mock_redis_instance.connection.get.assert_called_once_with(token)
   assert mock_redis_instance.connection.get(token) is None
   # Assert the call of GoogleIDP requests.get
   mock_requests.get.assert_called_once_with('https://www.googleapis.com/oauth2/v1/userinfo?alt=json', headers={"Authorization": f"Bearer {token}"})

   assert response.status_code == 200
   actual_response_payload = response.json()

   expected_response_payload = {
      "message": "Admin status successfully revoked"
   }

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
@patch("rbac_api.auth.idp.impl.requests")
async def test_patch_user_account_admin_status_with_existing_account_id_and_revoking_admin_status_of_assigned_admin_user_in_payload_and_valid_access_token_in_redis_cache_and_authenticating_user_is_account_admin(mock_requests, mock_redis_class, client, setup_initial_data):

   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = db_data["user4"]["email"]
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance

  # Mock the GoogleIDP request.get method
   mock_response = MagicMock()
   mock_response.json.return_value = get_user_email_response_with_success(email = db_data["user4"]["email"])
   mock_requests.get.return_value = mock_response
   
   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }

   payload = {
      "action": "Revoke"
   }
   account_id = db_data["account5"]["id"]
   assigned_user_id = db_data["user5"]["id"]
   response = await client.request(
      method="PATCH",
      url=f'/accounts/{account_id}/users/{assigned_user_id}/admin',
      headers=headers,
      json=payload
   )

   token = headers["Authorization"].split(" ")[1]
   # Verify that setex is not called
   mock_redis_instance.connection.setex.assert_not_called()

   # Assert the call and return value of connection.get
   mock_redis_instance.connection.get.assert_called_once_with(token)
   assert mock_redis_instance.connection.get(token) == db_data["user4"]["email"]

   # Assert that GoogleIDP.get_user_email is not called
   mock_requests.get.assert_not_called()
   
   assert response.status_code == 200
   actual_response_payload = response.json()

   expected_response_payload = {
      "message": "Admin status successfully revoked"
   }

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_patch_user_account_admin_status_with_existing_account_id_and_granting_admin_status_of_assigned_non_admin_user_in_payload_and_valid_access_token_and_authenticating_user_is_account_admin(mock_redis_class, client, setup_initial_data):
    
   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = db_data["user2"]["email"]
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance
   
   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }

   payload = {
      "action": "Grant"
   }
   account_id = db_data["account2"]["id"]
   assigned_user_id = db_data["user3"]["id"]
   response = await client.request(
      method="PATCH",
      url=f'/accounts/{account_id}/users/{assigned_user_id}/admin',
      headers=headers,
      json=payload
   )
   
   assert response.status_code == 200
   actual_response_payload = response.json()

   expected_response_payload = {
      "message": "Admin status successfully granted"
   }

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_patch_user_account_admin_status_with_existing_account_id_and_granting_admin_status_and_valid_access_token_and_authenticating_user_is_non_superadmin_and_non_account_admin(mock_redis_class, client, setup_initial_data):
    
   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = db_data["user3"]["email"]
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance
   
   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }

   payload = {
      "action": "Grant"
   }
   account_id = db_data["account2"]["id"]
   assigned_user_id = db_data["user4"]["id"]
   response = await client.request(
      method="PATCH",
      url=f'/accounts/{account_id}/users/{assigned_user_id}/admin',
      headers=headers,
      json=payload
   )
   
   assert response.status_code == 403
   actual_response_payload = response.json()

   expected_response_payload = {
      "detail": f"logged-in user - '{db_data['user3']['id']}' - does not have superadmin/account-admin privileges to update user admin status in account - '{account_id}'"
   }

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_patch_user_account_admin_status_with_existing_account_id_and_revoking_admin_status_and_valid_access_token_and_authenticating_user_is_non_superadmin_and_non_account_admin(mock_redis_class, client, setup_initial_data):
    
   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = db_data["user3"]["email"]
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance
   
   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }

   payload = {
      "action": "Revoke"
   }
   account_id = db_data["account2"]["id"]
   assigned_user_id = db_data["user4"]["id"]
   response = await client.request(
      method="PATCH",
      url=f'/accounts/{account_id}/users/{assigned_user_id}/admin',
      headers=headers,
      json=payload
   )
   
   assert response.status_code == 403
   actual_response_payload = response.json()

   expected_response_payload = {
      "detail": f"logged-in user - '{db_data['user3']['id']}' - does not have superadmin/account-admin privileges to update user admin status in account - '{account_id}'"
   }

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_patch_user_account_admin_status_with_existing_account_id_and_revoking_admin_status_and_valid_access_token_and_authenticating_user_is_not_superadmin_and_not_assigned_to_account(mock_redis_class, client, setup_initial_data):
    
   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = db_data["user3"]["email"]
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance
   
   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }

   payload = {
      "action": "Revoke"
   }
   account_id = db_data["account2"]["id"]
   assigned_user_id = db_data["user4"]["id"]
   response = await client.request(
      method="PATCH",
      url=f'/accounts/{account_id}/users/{assigned_user_id}/admin',
      headers=headers,
      json=payload
   )
   
   assert response.status_code == 403
   actual_response_payload = response.json()

   expected_response_payload = {
      "detail": f"logged-in user - '{db_data['user3']['id']}' - does not have superadmin/account-admin privileges to update user admin status in account - '{account_id}'"
   }

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_patch_user_account_admin_status_with_existing_account_id_and_revoking_admin_status_of_non_existent_user_in_payload_and_valid_access_token_and_authenticating_user_is_superadmin(mock_redis_class, client, setup_initial_data):
    
   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = db_data["user1"]["email"]
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance
   
   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }

   payload = {
      "action": "Revoke"
   }
   account_id = db_data['account2']['id']
   non_existent_user_id = "d1df1a9e-4c01-4302-a74d-fe1ec9db7339" 
   response = await client.request(
      method="PATCH",
      url=f'/accounts/{account_id}/users/{non_existent_user_id}/admin',
      headers=headers,
      json=payload
   )
   
   assert response.status_code == 404
   actual_response_payload = response.json()

   expected_response_payload = {
      "detail": f"User - '{non_existent_user_id}' - not found"
   }

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_patch_user_account_admin_status_with_existing_account_id_and_granting_admin_status_of_non_existent_user_in_payload_and_valid_access_token_and_authenticating_user_is_superadmin(mock_redis_class, client, setup_initial_data):
    
   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = db_data["user1"]["email"]
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance
   
   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }

   payload = {
      "action": "Grant"
   }
   account_id = db_data['account2']['id']
   non_existent_user_id = "d1df1a9e-4c01-4302-a74d-fe1ec9db7339" 
   response = await client.request(
      method="PATCH",
      url=f'/accounts/{account_id}/users/{non_existent_user_id}/admin',
      headers=headers,
      json=payload
   )
   
   assert response.status_code == 404
   actual_response_payload = response.json()

   expected_response_payload = {
      "detail": f"User - '{non_existent_user_id}' - not found"
   }

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_patch_user_account_admin_status_with_existing_account_id_and_revoking_admin_status_of_non_existent_user_in_payload_and_valid_access_token_and_authenticating_user_is_account_admin(mock_redis_class, client, setup_initial_data):
    
   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = db_data["user2"]["email"]
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance
   
   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }

   payload = {
      "action": "Revoke"
   }
   account_id = db_data['account2']['id']
   non_existent_user_id = "d1df1a9e-4c01-4302-a74d-fe1ec9db7339" 
   response = await client.request(
      method="PATCH",
      url=f'/accounts/{account_id}/users/{non_existent_user_id}/admin',
      headers=headers,
      json=payload
   )
   
   assert response.status_code == 404
   actual_response_payload = response.json()

   expected_response_payload = {
      "detail": f"User - '{non_existent_user_id}' - not found"
   }

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_patch_user_account_admin_status_with_existing_account_id_and_granting_admin_status_of_non_existent_user_in_payload_and_valid_access_token_and_authenticating_user_is_account_admin(mock_redis_class, client, setup_initial_data):
    
   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = db_data["user2"]["email"]
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance
   
   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }

   payload = {
      "action": "Grant"
   }
   account_id = db_data['account2']['id']
   non_existent_user_id = "d1df1a9e-4c01-4302-a74d-fe1ec9db7339" 
   response = await client.request(
      method="PATCH",
      url=f'/accounts/{account_id}/users/{non_existent_user_id}/admin',
      headers=headers,
      json=payload
   )
   
   assert response.status_code == 404
   actual_response_payload = response.json()

   expected_response_payload = {
      "detail": f"User - '{non_existent_user_id}' - not found"
   }

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_patch_user_account_admin_status_with_existing_account_id_and_granting_admin_status_of_existing_unassigned_user_in_payload_and_valid_access_token_and_authenticating_user_is_superadmin(mock_redis_class, client, setup_initial_data):
    
   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = db_data["user1"]["email"]
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance
   
   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }

   payload = {
      "action": "Grant"
   }
   account_id = db_data['account5']['id']
   existing_unassigned_user_id = db_data['user2']['id']
   response = await client.request(
      method="PATCH",
      url=f'/accounts/{account_id}/users/{existing_unassigned_user_id}/admin',
      headers=headers,
      json=payload
   )
   
   assert response.status_code == 422
   actual_response_payload = response.json()

   expected_response_payload = {
      "detail": f"user - '{db_data['user2']['id']}' - is not assigned to account - '{account_id}'"
   }

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_patch_user_account_admin_status_with_existing_account_id_and_revoking_admin_status_of_existing_unassigned_user_in_payload_and_valid_access_token_and_authenticating_user_is_superadmin(mock_redis_class, client, setup_initial_data):
    
   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = db_data["user1"]["email"]
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance
   
   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }

   payload = {
      "action": "Revoke"
   }
   account_id = db_data['account5']['id']
   existing_unassigned_user_id = db_data['user2']['id']
   response = await client.request(
      method="PATCH",
      url=f'/accounts/{account_id}/users/{existing_unassigned_user_id}/admin',
      headers=headers,
      json=payload
   )
   
   assert response.status_code == 422
   actual_response_payload = response.json()

   expected_response_payload = {
      "detail": f"user - '{db_data['user2']['id']}' - is not assigned to account - '{account_id}'"
   }

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_patch_user_account_admin_status_with_existing_account_id_and_granting_admin_status_of_existing_unassigned_user_in_payload_and_valid_access_token_and_authenticating_user_is_account_admin(mock_redis_class, client, setup_initial_data):
    
   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = db_data["user5"]["email"]
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance
   
   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }

   payload = {
      "action": "Grant"
   }
   account_id = db_data['account5']['id']
   existing_unassigned_user_id = db_data['user1']['id']
   response = await client.request(
      method="PATCH",
      url=f'/accounts/{account_id}/users/{existing_unassigned_user_id}/admin',
      headers=headers,
      json=payload
   )
   
   assert response.status_code == 422
   actual_response_payload = response.json()

   expected_response_payload = {
      "detail": f"user - '{db_data['user1']['id']}' - is not assigned to account - '{account_id}'"
   }

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_patch_user_account_admin_status_with_existing_account_id_and_revoking_admin_status_of_existing_unassigned_user_in_payload_and_valid_access_token_and_authenticating_user_is_account_admin(mock_redis_class, client, setup_initial_data):
    
   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = db_data["user5"]["email"]
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance
   
   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }

   payload = {
      "action": "Revoke"
   }
   account_id = db_data['account5']['id']
   existing_unassigned_user_id = db_data['user1']['id']
   response = await client.request(
      method="PATCH",
      url=f'/accounts/{account_id}/users/{existing_unassigned_user_id}/admin',
      headers=headers,
      json=payload
   )
   
   assert response.status_code == 422
   actual_response_payload = response.json()

   expected_response_payload = {
      "detail": f"user - '{db_data['user1']['id']}' - is not assigned to account - '{account_id}'"
   }

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_patch_user_account_admin_status_with_existing_account_id_and_revoking_admin_status_of_self_and_valid_access_token_and_authenticating_user_is_account_admin_and_not_superadmin(mock_redis_class, client, setup_initial_data):
    
   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = db_data["user4"]["email"]
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance
   
   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }

   payload = {
      "action": "Revoke"
   }
   account_id = db_data['account5']['id']
   existing_unassigned_user_id = db_data['user4']['id']
   response = await client.request(
      method="PATCH",
      url=f'/accounts/{account_id}/users/{existing_unassigned_user_id}/admin',
      headers=headers,
      json=payload
   )
   
   assert response.status_code == 403
   actual_response_payload = response.json()

   expected_response_payload = {'detail': f"logged-in user - '{db_data['user4']['id']}' - does not do not have permission to modify account admin status of self"}

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
async def test_patch_user_account_admin_status_with_no_access_token(client, setup_initial_data):
    
   headers = {
      "Authorization": " ",
      "Content-Type": "application/json"
   }

   payload = {
      "action": "Revoke"
   }

   existing_account_id = db_data["account1"]["id"]
   user_id = db_data['user5']['id']

   response = await client.request(
      method="PATCH",
      url=f'/accounts/{existing_account_id}/users/{user_id}/admin',
      headers=headers,
      json=payload
   )
  
   assert response.status_code == 401
   actual_response_payload = response.json()

   expected_response_payload = {"detail": "Request auth header must contain bearer iDP access_token for authentication"}

   assert actual_response_payload == expected_response_payload

@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
@patch("rbac_api.auth.idp.impl.requests")
async def test_patch_user_account_admin_status_with_existing_account_id_and_invalid_or_expired_access_token(mock_requests, mock_redis_class, client, setup_initial_data):
    
   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = None
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance

  # Mock the GoogleIDP request.get method
   mock_response = MagicMock()
   mock_response.json.return_value = get_user_email_response_with_error()
   mock_requests.get.return_value = mock_response

   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }

   payload = {
      "action": "Revoke"
   }

   existing_account_id = db_data["account1"]["id"]
   user_id = db_data['user5']['id']


   response = await client.request(
      method="DELETE",
      url=f'/accounts/{existing_account_id}/users/{user_id}',
      headers=headers,
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
async def test_patch_user_account_admin_status_with_existing_account_id_and_valid_access_token_and_authenticating_user_does_not_exist_in_db(mock_redis_class, client, setup_initial_data):
    
   # Mock the Redis get and setex methods
   mock_redis_instance = MagicMock()
   mock_redis_instance.connection.get.return_value = "unregistered_email"
   mock_redis_instance.connection.setex.return_value = None
   mock_redis_class.return_value = mock_redis_instance
   
   headers = {
      "Authorization": "Bearer MOCK_ACCESS_TOKEN",
      "Content-Type": "application/json"
   }
   payload = {
      "action": "Revoke"
   }

   existing_account_id = db_data["account1"]["id"]
   user_id = db_data["user2"]['id']

   response = await client.request(
      method="PATCH",
      url=f'/accounts/{existing_account_id}/users/{user_id}/admin',
      headers=headers,
      json=payload
   )
   
   assert response.status_code == 401
   actual_response_payload = response.json()

   expected_response_payload = {"detail": "user is unauthenticated"}

   assert actual_response_payload == expected_response_payload
