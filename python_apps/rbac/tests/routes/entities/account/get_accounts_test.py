import pytest
from unittest.mock import patch, MagicMock, ANY
from ....auth.idp.google import (
    get_user_email_response_with_error,
    get_user_email_response_with_success,
)
from ....fixtures.setup_initial_data import db_data


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
@patch("rbac_api.auth.idp.impl.requests")
async def test_get_accounts_with_valid_access_token_not_in_redis_cache_and_authenticating_user_is_superadmin(
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

    response = await client.request(
        method="GET",
        url="/accounts/",
        headers=headers,
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

    expected_response_payload = [
        {
            "id": db_data["account1"]["id"],
            "name": db_data["account1"]["name"],
            "organization_id": db_data["account1"]["organization_id"],
            "description": db_data["account1"]["description"],
            "created_at": ANY,
            "updated_at": ANY,
        },
        {
            "id": db_data["account2"]["id"],
            "name": db_data["account2"]["name"],
            "organization_id": db_data["account2"]["organization_id"],
            "description": db_data["account2"]["description"],
            "created_at": ANY,
            "updated_at": ANY,
        },
        {
            "id": db_data["account3"]["id"],
            "name": db_data["account3"]["name"],
            "organization_id": db_data["account3"]["organization_id"],
            "description": db_data["account3"]["description"],
            "created_at": ANY,
            "updated_at": ANY,
        },
        {
            "id": db_data["account4"]["id"],
            "name": db_data["account4"]["name"],
            "organization_id": db_data["account4"]["organization_id"],
            "description": db_data["account4"]["description"],
            "created_at": ANY,
            "updated_at": ANY,
        },
        {
            "id": db_data["account5"]["id"],
            "name": db_data["account5"]["name"],
            "organization_id": db_data["account5"]["organization_id"],
            "description": db_data["account5"]["description"],
            "created_at": ANY,
            "updated_at": ANY,
        },
        {
            "id": db_data["default_account"]["id"],
            "name": db_data["default_account"]["name"],
            "organization_id": db_data["default_account"]["organization_id"],
            "description": db_data["default_account"]["description"],
            "created_at": ANY,
            "updated_at": ANY,
        },
    ]

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
@patch("rbac_api.auth.idp.impl.requests")
async def test_get_accounts_with_valid_access_token_in_redis_cache_and_authenticating_user_is_superadmin(
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

    response = await client.request(
        method="GET",
        url="/accounts/",
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
            "id": db_data["account1"]["id"],
            "name": db_data["account1"]["name"],
            "organization_id": db_data["account1"]["organization_id"],
            "description": db_data["account1"]["description"],
            "created_at": ANY,
            "updated_at": ANY,
        },
        {
            "id": db_data["account2"]["id"],
            "name": db_data["account2"]["name"],
            "organization_id": db_data["account2"]["organization_id"],
            "description": db_data["account2"]["description"],
            "created_at": ANY,
            "updated_at": ANY,
        },
        {
            "id": db_data["account3"]["id"],
            "name": db_data["account3"]["name"],
            "organization_id": db_data["account3"]["organization_id"],
            "description": db_data["account3"]["description"],
            "created_at": ANY,
            "updated_at": ANY,
        },
        {
            "id": db_data["account4"]["id"],
            "name": db_data["account4"]["name"],
            "organization_id": db_data["account4"]["organization_id"],
            "description": db_data["account4"]["description"],
            "created_at": ANY,
            "updated_at": ANY,
        },
        {
            "id": db_data["account5"]["id"],
            "name": db_data["account5"]["name"],
            "organization_id": db_data["account5"]["organization_id"],
            "description": db_data["account5"]["description"],
            "created_at": ANY,
            "updated_at": ANY,
        },
        {
            "id": db_data["default_account"]["id"],
            "name": db_data["default_account"]["name"],
            "organization_id": db_data["default_account"]["organization_id"],
            "description": db_data["default_account"]["description"],
            "created_at": ANY,
            "updated_at": ANY,
        },
    ]

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_get_accounts_filtered_by_name_and_valid_access_token_and_authenticating_user_is_superadmin(
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

    name_filter = "f"  # only retrieve accounts that case-insensitive pattern match 'f'
    response = await client.request(
        method="GET",
        url=f"/accounts/?name={name_filter}",
        headers=headers,
    )

    assert response.status_code == 200
    actual_response_payload = response.json()

    expected_response_payload = [
        {
            "id": db_data["default_account"]["id"],
            "name": db_data["default_account"]["name"],
            "organization_id": db_data["default_account"]["organization_id"],
            "description": db_data["default_account"]["description"],
            "created_at": ANY,
            "updated_at": ANY,
        }
    ]

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_get_accounts_with_valid_access_token_and_authenticating_user_is_not_superadmin(
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

    response = await client.request(
        method="GET",
        url="/accounts/",
        headers=headers,
    )

    assert response.status_code == 200
    actual_response_payload = response.json()

    expected_response_payload = [
        {
            "id": db_data["default_account"]["id"],
            "name": db_data["default_account"]["name"],
            "organization_id": db_data["default_account"]["organization_id"],
            "description": db_data["default_account"]["description"],
            "created_at": ANY,
            "updated_at": ANY,
        },
        {
            "id": db_data["account2"]["id"],
            "name": db_data["account2"]["name"],
            "organization_id": db_data["account2"]["organization_id"],
            "description": db_data["account2"]["description"],
            "created_at": ANY,
            "updated_at": ANY,
        },
    ]

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_get_accounts_filtered_by_account_name_with_valid_access_token_and_authenticating_user_is_not_superadmin(
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

    name_filter = "f"
    response = await client.request(
        method="GET",
        url=f"/accounts/?name={name_filter}",
        headers=headers,
    )

    assert response.status_code == 200
    actual_response_payload = response.json()

    expected_response_payload = [
        {
            "id": db_data["default_account"]["id"],
            "name": db_data["default_account"]["name"],
            "organization_id": db_data["default_account"]["organization_id"],
            "description": db_data["default_account"]["description"],
            "created_at": ANY,
            "updated_at": ANY,
        }
    ]

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
async def test_get_accounts_with_no_access_token(client, setup_initial_data):

    headers = {"Authorization": " ", "Content-Type": "application/json"}

    response = await client.request(
        method="GET",
        url="/accounts/",
        headers=headers,
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
async def test_get_accounts_with_invalid_or_expired_access_token(
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

    response = await client.request(
        method="GET",
        url="/accounts/",
        headers=headers,
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
async def test_get_accounts_with_valid_access_token_and_authenticating_user_does_not_exist_in_db(
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

    response = await client.request(
        method="GET",
        url="/accounts/",
        headers=headers,
    )

    assert response.status_code == 401
    actual_response_payload = response.json()

    expected_response_payload = {"detail": "user is unauthenticated"}

    assert actual_response_payload == expected_response_payload
