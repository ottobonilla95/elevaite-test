import pytest
from unittest.mock import patch, AsyncMock, MagicMock, ANY
from .... import models
from ....auth.idp.google import (
    get_user_email_response_with_error,
    get_user_email_response_with_success,
)
from ....fixtures.setup_initial_data import db_data
from elevaitelib.schemas import permission as permission_schemas
import uuid


@pytest.mark.asyncio
@patch("elevaitelib.orm.db.models.User_Account", new=models.User_Account)
@patch("rbac_api.auth.impl.RedisSingleton")
@patch("rbac_api.auth.idp.impl.requests")
async def test_assign_users_to_account_with_existing_account_id_and_unassigned_users_in_payload_and_valid_access_token_not_in_redis_cache_and_authenticating_user_is_superadmin(
    mock_requests, mock_redis_class, client, setup_initial_data
):

    # Mock the GoogleIDP reques.get method
    mock_response = MagicMock()
    mock_response.json.return_value = get_user_email_response_with_success(
        email=db_data["user1"]["email"]
    )
    mock_requests.get.return_value = mock_response

    # Mock the Redis get and setex methods
    mock_redis_instance = MagicMock()
    mock_redis_instance.connection.get.return_value = None
    mock_redis_instance.connection.setex.return_value = None
    mock_redis_class.return_value = mock_redis_instance

    headers = {
        "Authorization": "Bearer MOCK_ACCESS_TOKEN",
        "Content-Type": "application/json",
    }
    assign_users_to_account_payload = {
        "user_ids": [db_data["user2"]["id"], db_data["user3"]["id"]]
    }

    account_id = db_data["account3"]["id"]
    response = await client.request(
        method="POST",
        url=f"/accounts/{account_id}/users",
        headers=headers,
        json=assign_users_to_account_payload,
    )

    token = headers["Authorization"].split(" ")[1]
    # Verify the exact call to setex
    mock_redis_instance.connection.setex.assert_called_once_with(
        token, 60 * 60, db_data["user1"]["email"]
    )
    # Assert the call and return value of connection.get
    mock_redis_instance.connection.get.assert_called_once_with(token)
    assert mock_redis_instance.connection.get(token) is None
    # Assert the call of GoogleIDP requests.get
    mock_requests.get.assert_called_once_with(
        "https://www.googleapis.com/oauth2/v1/userinfo?alt=json",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    actual_response_payload = response.json()

    expected_response_payload = {
        "message": f"Successfully assigned 2 user/(s) to account - '{account_id}'"
    }

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("elevaitelib.orm.db.models.User_Account", new=models.User_Account)
@patch("rbac_api.auth.impl.RedisSingleton")
@patch("rbac_api.auth.idp.impl.requests")
async def test_assign_users_to_account_users_with_existing_account_id_and_unassigned_users_in_payload_and_valid_access_token_in_redis_cache_and_authenticating_user_is_superadmin(
    mock_requests, mock_redis_class, client, setup_initial_data
):

    # Mock the Redis get and setex methods
    mock_redis_instance = MagicMock()
    mock_redis_instance.connection.get.return_value = db_data["user1"]["email"]
    mock_redis_instance.connection.setex.return_value = None
    mock_redis_class.return_value = mock_redis_instance

    # Mock the GoogleIDP request.get method
    mock_response = MagicMock()
    mock_response.json.return_value = get_user_email_response_with_success(
        email=db_data["user1"]["email"]
    )
    mock_requests.get.return_value = mock_response

    headers = {
        "Authorization": "Bearer MOCK_ACCESS_TOKEN",
        "Content-Type": "application/json",
    }

    assign_users_to_account_payload = {
        "user_ids": [db_data["user2"]["id"], db_data["user3"]["id"]]
    }

    account_id = db_data["account3"]["id"]
    response = await client.request(
        method="POST",
        url=f"/accounts/{account_id}/users",
        headers=headers,
        json=assign_users_to_account_payload,
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
        "message": f"Successfully assigned 2 user/(s) to account - '{account_id}'"
    }

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("elevaitelib.orm.db.models.User_Account", new=models.User_Account)
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_assign_users_to_account_users_with_existing_account_id_and_unassigned_users_in_payload_and_valid_access_token_and_authenticating_user_is_account_admin(
    mock_redis_class, client, setup_initial_data
):

    # Mock the Redis get and setex methods
    mock_redis_instance = MagicMock()
    mock_redis_instance.connection.get.return_value = db_data["user4"]["email"]
    mock_redis_instance.connection.setex.return_value = None
    mock_redis_class.return_value = mock_redis_instance

    headers = {
        "Authorization": "Bearer MOCK_ACCESS_TOKEN",
        "Content-Type": "application/json",
    }

    assign_users_to_account_payload = {
        "user_ids": [db_data["user1"]["id"], db_data["user2"]["id"]]
    }

    account_id = db_data["account4"]["id"]
    response = await client.request(
        method="POST",
        url=f"/accounts/{account_id}/users",
        headers=headers,
        json=assign_users_to_account_payload,
    )

    assert response.status_code == 200
    actual_response_payload = response.json()

    expected_response_payload = {
        "message": f"Successfully assigned 2 user/(s) to account - '{account_id}'"
    }

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("elevaitelib.orm.db.models.User_Account", new=models.User_Account)
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_assign_users_to_account_users_with_existing_account_id_and_unassigned_users_in_payload_and_valid_access_token_and_authenticating_user_is_not_superadmin_and_not_account_admin(
    mock_redis_class, client, setup_initial_data
):

    # Mock the Redis get and setex methods
    mock_redis_instance = MagicMock()
    mock_redis_instance.connection.get.return_value = db_data["user3"]["email"]
    mock_redis_instance.connection.setex.return_value = None
    mock_redis_class.return_value = mock_redis_instance

    headers = {
        "Authorization": "Bearer MOCK_ACCESS_TOKEN",
        "Content-Type": "application/json",
    }

    assign_users_to_account_payload = {
        "user_ids": [db_data["user1"]["id"], db_data["user2"]["id"]]
    }

    account_id = db_data["account2"]["id"]
    response = await client.request(
        method="POST",
        url=f"/accounts/{account_id}/users",
        headers=headers,
        json=assign_users_to_account_payload,
    )

    assert response.status_code == 403
    actual_response_payload = response.json()

    expected_response_payload = {
        "detail": f"logged-in user - '{db_data['user3']['id']}' - does not have superadmin/account-admin privileges to assign users to account - '{account_id}'"
    }

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_assign_users_to_account_with_non_existent_account_id_and_valid_access_token_and_authenticating_user_exists_in_db(
    mock_redis_class, client, setup_initial_data
):

    # Mock the Redis get and setex methods
    mock_redis_instance = MagicMock()
    mock_redis_instance.connection.get.return_value = db_data["user2"]["email"]
    mock_redis_instance.connection.setex.return_value = None
    mock_redis_class.return_value = mock_redis_instance

    headers = {
        "Authorization": "Bearer MOCK_ACCESS_TOKEN",
        "Content-Type": "application/json",
    }
    assign_users_to_account_payload = {
        "user_ids": [db_data["user1"]["id"], db_data["user3"]["id"]]
    }

    non_existent_account_id = "d1df1a9e-4c01-4302-a74d-fe1ec9db7339"
    response = await client.request(
        method="POST",
        url=f"/accounts/{non_existent_account_id}/users",
        headers=headers,
        json=assign_users_to_account_payload,
    )

    assert response.status_code == 404
    actual_response_payload = response.json()

    expected_response_payload = {
        "detail": f"Account - '{non_existent_account_id}' - not found"
    }

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_assign_users_to_account_with_existing_account_id_and_already_assigned_users_in_payload_and_valid_access_token_and_authenticating_user_is_superadmin(
    mock_redis_class, client, setup_initial_data
):

    # Mock the Redis get and setex methods
    mock_redis_instance = MagicMock()
    mock_redis_instance.connection.get.return_value = db_data["user1"]["email"]
    mock_redis_instance.connection.setex.return_value = None
    mock_redis_class.return_value = mock_redis_instance

    headers = {
        "Authorization": "Bearer MOCK_ACCESS_TOKEN",
        "Content-Type": "application/json",
    }
    assign_users_to_account_payload = {
        "user_ids": [db_data["user2"]["id"], db_data["user3"]["id"]]
    }

    account_id = db_data["account2"]["id"]
    response = await client.request(
        method="POST",
        url=f"/accounts/{account_id}/users",
        headers=headers,
        json=assign_users_to_account_payload,
    )

    assert response.status_code == 409
    actual_response_payload = response.json()

    expected_response_payload = {
        "detail": f"One or more users are already assigned to account - '{account_id}'"
    }

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_assign_users_to_account_with_existing_account_id_and_already_assigned_users_in_payload_and_valid_access_token_and_authenticating_user_is_account_admin(
    mock_redis_class, client, setup_initial_data
):

    # Mock the Redis get and setex methods
    mock_redis_instance = MagicMock()
    mock_redis_instance.connection.get.return_value = db_data["user2"]["email"]
    mock_redis_instance.connection.setex.return_value = None
    mock_redis_class.return_value = mock_redis_instance

    headers = {
        "Authorization": "Bearer MOCK_ACCESS_TOKEN",
        "Content-Type": "application/json",
    }
    assign_users_to_account_payload = {
        "user_ids": [db_data["user3"]["id"], db_data["user4"]["id"]]
    }

    account_id = db_data["account2"]["id"]
    response = await client.request(
        method="POST",
        url=f"/accounts/{account_id}/users",
        headers=headers,
        json=assign_users_to_account_payload,
    )

    assert response.status_code == 409
    actual_response_payload = response.json()

    expected_response_payload = {
        "detail": f"One or more users are already assigned to account - '{account_id}'"
    }

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_assign_users_to_account_with_existing_account_id_and_no_users_in_payload_and_valid_access_token_and_authenticating_user_is_superadmin(
    mock_redis_class, client, setup_initial_data
):

    # Mock the Redis get and setex methods
    mock_redis_instance = MagicMock()
    mock_redis_instance.connection.get.return_value = db_data["user1"]["email"]
    mock_redis_instance.connection.setex.return_value = None
    mock_redis_class.return_value = mock_redis_instance

    headers = {
        "Authorization": "Bearer MOCK_ACCESS_TOKEN",
        "Content-Type": "application/json",
    }
    assign_users_to_account_payload = {"user_ids": []}

    account_id = db_data["account2"]["id"]
    response = await client.request(
        method="POST",
        url=f"/accounts/{account_id}/users",
        headers=headers,
        json=assign_users_to_account_payload,
    )

    assert response.status_code == 422
    actual_response_payload = response.json()

    expected_response_payload = {
        "detail": [
            {
                "loc": ["body", "user_ids"],
                "msg": "The list of user IDs must have length between 1 and 50 (inclusive)",
                "type": "value_error",
            }
        ]
    }

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_assign_users_to_account_with_existing_account_id_and_more_than_50_users_in_payload_and_valid_access_token_and_authenticating_user_is_superadmin(
    mock_redis_class, client, setup_initial_data
):

    # Mock the Redis get and setex methods
    mock_redis_instance = MagicMock()
    mock_redis_instance.connection.get.return_value = db_data["user1"]["email"]
    mock_redis_instance.connection.setex.return_value = None
    mock_redis_class.return_value = mock_redis_instance

    headers = {
        "Authorization": "Bearer MOCK_ACCESS_TOKEN",
        "Content-Type": "application/json",
    }
    assign_users_to_account_payload = {
        "user_ids": [str(uuid.uuid4()) for i in range(51)]
    }

    account_id = db_data["account2"]["id"]
    response = await client.request(
        method="POST",
        url=f"/accounts/{account_id}/users",
        headers=headers,
        json=assign_users_to_account_payload,
    )

    assert response.status_code == 422
    actual_response_payload = response.json()

    expected_response_payload = {
        "detail": [
            {
                "loc": ["body", "user_ids"],
                "msg": "The list of user IDs must have length between 1 and 50 (inclusive)",
                "type": "value_error",
            }
        ]
    }

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_assign_users_to_account_with_existing_account_id_and_duplicate_users_in_payload_and_valid_access_token_and_authenticating_user_is_superadmin(
    mock_redis_class, client, setup_initial_data
):

    # Mock the Redis get and setex methods
    mock_redis_instance = MagicMock()
    mock_redis_instance.connection.get.return_value = db_data["user1"]["email"]
    mock_redis_instance.connection.setex.return_value = None
    mock_redis_class.return_value = mock_redis_instance

    headers = {
        "Authorization": "Bearer MOCK_ACCESS_TOKEN",
        "Content-Type": "application/json",
    }
    assign_users_to_account_payload = {
        "user_ids": [db_data["user2"]["id"], db_data["user2"]["id"]]
    }

    account_id = db_data["account2"]["id"]
    response = await client.request(
        method="POST",
        url=f"/accounts/{account_id}/users",
        headers=headers,
        json=assign_users_to_account_payload,
    )

    assert response.status_code == 422
    actual_response_payload = response.json()

    expected_response_payload = {
        "detail": [
            {
                "loc": ["body", "user_ids"],
                "msg": "Duplicate user IDs are not allowed",
                "type": "value_error",
            }
        ]
    }

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_assign_users_to_account_with_existing_account_id_and_one_or_more_users_in_payload_not_found_and_valid_access_token_and_authenticating_user_is_superadmin(
    mock_redis_class, client, setup_initial_data
):

    # Mock the Redis get and setex methods
    mock_redis_instance = MagicMock()
    mock_redis_instance.connection.get.return_value = db_data["user1"]["email"]
    mock_redis_instance.connection.setex.return_value = None
    mock_redis_class.return_value = mock_redis_instance

    headers = {
        "Authorization": "Bearer MOCK_ACCESS_TOKEN",
        "Content-Type": "application/json",
    }
    assign_users_to_account_payload = {
        "user_ids": [db_data["user2"]["id"], str(uuid.uuid4())]
    }

    account_id = db_data["account2"]["id"]
    response = await client.request(
        method="POST",
        url=f"/accounts/{account_id}/users",
        headers=headers,
        json=assign_users_to_account_payload,
    )

    assert response.status_code == 404
    actual_response_payload = response.json()

    expected_response_payload = {"detail": "One or more users not found"}

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_assign_users_to_account_with_existing_account_id_and_no_users_in_payload_and_valid_access_token_and_authenticating_user_is_account_admin(
    mock_redis_class, client, setup_initial_data
):

    # Mock the Redis get and setex methods
    mock_redis_instance = MagicMock()
    mock_redis_instance.connection.get.return_value = db_data["user2"]["email"]
    mock_redis_instance.connection.setex.return_value = None
    mock_redis_class.return_value = mock_redis_instance

    headers = {
        "Authorization": "Bearer MOCK_ACCESS_TOKEN",
        "Content-Type": "application/json",
    }
    assign_users_to_account_payload = {"user_ids": []}

    account_id = db_data["account2"]["id"]
    response = await client.request(
        method="POST",
        url=f"/accounts/{account_id}/users",
        headers=headers,
        json=assign_users_to_account_payload,
    )

    assert response.status_code == 422
    actual_response_payload = response.json()

    expected_response_payload = {
        "detail": [
            {
                "loc": ["body", "user_ids"],
                "msg": "The list of user IDs must have length between 1 and 50 (inclusive)",
                "type": "value_error",
            }
        ]
    }

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_assign_users_to_account_with_existing_account_id_and_more_than_50_users_in_payload_and_valid_access_token_and_authenticating_user_is_account_admin(
    mock_redis_class, client, setup_initial_data
):

    # Mock the Redis get and setex methods
    mock_redis_instance = MagicMock()
    mock_redis_instance.connection.get.return_value = db_data["user2"]["email"]
    mock_redis_instance.connection.setex.return_value = None
    mock_redis_class.return_value = mock_redis_instance

    headers = {
        "Authorization": "Bearer MOCK_ACCESS_TOKEN",
        "Content-Type": "application/json",
    }
    assign_users_to_account_payload = {
        "user_ids": [str(uuid.uuid4()) for i in range(51)]
    }

    account_id = db_data["account2"]["id"]
    response = await client.request(
        method="POST",
        url=f"/accounts/{account_id}/users",
        headers=headers,
        json=assign_users_to_account_payload,
    )

    assert response.status_code == 422
    actual_response_payload = response.json()

    expected_response_payload = {
        "detail": [
            {
                "loc": ["body", "user_ids"],
                "msg": "The list of user IDs must have length between 1 and 50 (inclusive)",
                "type": "value_error",
            }
        ]
    }

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_assign_users_to_account_with_existing_account_id_and_duplicate_users_in_payload_and_valid_access_token_and_authenticating_user_is_account_admin(
    mock_redis_class, client, setup_initial_data
):

    # Mock the Redis get and setex methods
    mock_redis_instance = MagicMock()
    mock_redis_instance.connection.get.return_value = db_data["user2"]["email"]
    mock_redis_instance.connection.setex.return_value = None
    mock_redis_class.return_value = mock_redis_instance

    headers = {
        "Authorization": "Bearer MOCK_ACCESS_TOKEN",
        "Content-Type": "application/json",
    }
    assign_users_to_account_payload = {
        "user_ids": [db_data["user1"]["id"], db_data["user1"]["id"]]
    }

    account_id = db_data["account2"]["id"]
    response = await client.request(
        method="POST",
        url=f"/accounts/{account_id}/users",
        headers=headers,
        json=assign_users_to_account_payload,
    )

    assert response.status_code == 422
    actual_response_payload = response.json()

    expected_response_payload = {
        "detail": [
            {
                "loc": ["body", "user_ids"],
                "msg": "Duplicate user IDs are not allowed",
                "type": "value_error",
            }
        ]
    }

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_assign_users_to_account_with_existing_account_id_and_one_or_more_users_in_payload_not_found_and_valid_access_token_and_authenticating_user_is_account_admin(
    mock_redis_class, client, setup_initial_data
):

    # Mock the Redis get and setex methods
    mock_redis_instance = MagicMock()
    mock_redis_instance.connection.get.return_value = db_data["user2"]["email"]
    mock_redis_instance.connection.setex.return_value = None
    mock_redis_class.return_value = mock_redis_instance

    headers = {
        "Authorization": "Bearer MOCK_ACCESS_TOKEN",
        "Content-Type": "application/json",
    }
    assign_users_to_account_payload = {
        "user_ids": [db_data["user1"]["id"], str(uuid.uuid4())]
    }

    account_id = db_data["account2"]["id"]
    response = await client.request(
        method="POST",
        url=f"/accounts/{account_id}/users",
        headers=headers,
        json=assign_users_to_account_payload,
    )

    assert response.status_code == 404
    actual_response_payload = response.json()

    expected_response_payload = {"detail": "One or more users not found"}

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
async def test_assign_users_to_account_with_existing_account_id_and_no_access_token(
    client, setup_initial_data
):

    headers = {"Authorization": " ", "Content-Type": "application/json"}

    assign_users_to_account_payload = {
        "user_ids": [db_data["user1"]["id"], db_data["user2"]["id"]]
    }

    existing_account_id = db_data["account1"]["id"]

    response = await client.request(
        method="POST",
        url=f"/accounts/{existing_account_id}/users",
        headers=headers,
        json=assign_users_to_account_payload,
    )

    assert response.status_code == 401
    actual_response_payload = response.json()

    expected_response_payload = {
        "detail": "Request auth header must contain bearer iDP access_token for authentication"
    }

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
@patch("rbac_api.auth.idp.impl.requests")
async def test_assign_users_to_account_with_existing_account_id_and_invalid_or_expired_access_token(
    mock_requests, mock_redis_class, client, setup_initial_data
):

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
        "Content-Type": "application/json",
    }

    assign_users_to_account_payload = {
        "user_ids": [db_data["user1"]["id"], db_data["user2"]["id"]]
    }

    existing_account_id = db_data["account1"]["id"]

    response = await client.request(
        method="POST",
        url=f"/accounts/{existing_account_id}/users",
        headers=headers,
        json=assign_users_to_account_payload,
    )

    token = headers["Authorization"].split(" ")[1]
    # Verify that setex is not called (error thrown before that)
    mock_redis_instance.connection.setex.assert_not_called()

    # Assert the call of connection.get
    mock_redis_instance.connection.get.assert_called_once_with(token)

    # Assert that GoogleIDP.get_user_email is called
    mock_requests.get.assert_called_once_with(
        "https://www.googleapis.com/oauth2/v1/userinfo?alt=json",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    actual_response_payload = response.json()

    expected_response_payload = {"detail": "invalid or expired auth credentials"}

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_assign_users_to_account_with_existing_account_id_and_valid_access_token_and_authenticating_user_does_not_exist_in_db(
    mock_redis_class, client, setup_initial_data
):

    # Mock the Redis get and setex methods
    mock_redis_instance = MagicMock()
    mock_redis_instance.connection.get.return_value = "unregistered_email"
    mock_redis_instance.connection.setex.return_value = None
    mock_redis_class.return_value = mock_redis_instance

    headers = {
        "Authorization": "Bearer MOCK_ACCESS_TOKEN",
        "Content-Type": "application/json",
    }

    assign_users_to_account_payload = {
        "user_ids": [db_data["user1"]["id"], db_data["user2"]["id"]]
    }

    existing_account_id = db_data["account1"]["id"]

    response = await client.request(
        method="POST",
        url=f"/accounts/{existing_account_id}/users",
        headers=headers,
        json=assign_users_to_account_payload,
    )

    assert response.status_code == 401
    actual_response_payload = response.json()

    expected_response_payload = {"detail": "user is unauthenticated"}

    assert actual_response_payload == expected_response_payload
