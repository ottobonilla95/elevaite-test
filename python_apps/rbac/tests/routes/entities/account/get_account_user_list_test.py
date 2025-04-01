import pytest
from unittest.mock import patch, AsyncMock, MagicMock, ANY
from .... import models
from ....auth.idp.google import (
    get_user_email_response_with_error,
    get_user_email_response_with_success,
)
from ....fixtures.setup_initial_data import db_data
from elevaitelibbbbbb.schemas import permission as permission_schemas


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
@patch("rbac_api.auth.idp.impl.requests")
async def test_get_account_user_list_with_existing_account_id_and_valid_access_token_not_in_redis_cache_and_authenticating_user_is_superadmin(
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
    account_id = db_data["account2"]["id"]
    response = await client.request(
        method="GET",
        url=f"/accounts/{account_id}/users",
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
            "id": db_data["user2"]["id"],
            "organization_id": db_data["organization"]["id"],
            "firstname": db_data["user2"]["firstname"],
            "lastname": db_data["user2"]["lastname"],
            "email": db_data["user2"]["email"],
            "is_superadmin": db_data["user2"]["is_superadmin"],
            "created_at": ANY,
            "updated_at": ANY,
            "is_account_admin": db_data["user2_account2"]["is_admin"],
            "roles": [],
        },
        {
            "id": db_data["user3"]["id"],
            "organization_id": db_data["organization"]["id"],
            "firstname": db_data["user3"]["firstname"],
            "lastname": db_data["user3"]["lastname"],
            "email": db_data["user3"]["email"],
            "is_superadmin": db_data["user3"]["is_superadmin"],
            "created_at": ANY,
            "updated_at": ANY,
            "is_account_admin": db_data["user3_account2"]["is_admin"],
            "roles": [],
        },
        {
            "id": db_data["user4"]["id"],
            "organization_id": db_data["organization"]["id"],
            "firstname": db_data["user4"]["firstname"],
            "lastname": db_data["user4"]["lastname"],
            "email": db_data["user4"]["email"],
            "is_superadmin": db_data["user4"]["is_superadmin"],
            "created_at": ANY,
            "updated_at": ANY,
            "is_account_admin": db_data["user4_account2"]["is_admin"],
            "roles": [],
        },
    ]

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
@patch("rbac_api.auth.idp.impl.requests")
async def test_get_account_user_list_with_existing_account_id_and_valid_access_token_in_redis_cache_and_authenticating_user_is_superadmin(
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

    existing_account_id = db_data["account2"]["id"]

    response = await client.request(
        method="GET",
        url=f"/accounts/{existing_account_id}/users",
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
            "id": db_data["user2"]["id"],
            "organization_id": db_data["organization"]["id"],
            "firstname": db_data["user2"]["firstname"],
            "lastname": db_data["user2"]["lastname"],
            "email": db_data["user2"]["email"],
            "is_superadmin": db_data["user2"]["is_superadmin"],
            "created_at": ANY,
            "updated_at": ANY,
            "is_account_admin": db_data["user2_account2"]["is_admin"],
            "roles": [],
        },
        {
            "id": db_data["user3"]["id"],
            "organization_id": db_data["organization"]["id"],
            "firstname": db_data["user3"]["firstname"],
            "lastname": db_data["user3"]["lastname"],
            "email": db_data["user3"]["email"],
            "is_superadmin": db_data["user3"]["is_superadmin"],
            "created_at": ANY,
            "updated_at": ANY,
            "is_account_admin": db_data["user3_account2"]["is_admin"],
            "roles": [],
        },
        {
            "id": db_data["user4"]["id"],
            "organization_id": db_data["organization"]["id"],
            "firstname": db_data["user4"]["firstname"],
            "lastname": db_data["user4"]["lastname"],
            "email": db_data["user4"]["email"],
            "is_superadmin": db_data["user4"]["is_superadmin"],
            "created_at": ANY,
            "updated_at": ANY,
            "is_account_admin": db_data["user4_account2"]["is_admin"],
            "roles": [],
        },
    ]

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_get_account_user_list_with_existing_account_id_and_valid_access_token_and_authenticating_user_is_not_superadmin_and_is_assigned_to_account(
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

    existing_account_id = db_data["account2"]["id"]

    response = await client.request(
        method="GET",
        url=f"/accounts/{existing_account_id}/users",
        headers=headers,
    )

    assert response.status_code == 200
    actual_response_payload = response.json()

    expected_response_payload = [
        {
            "id": db_data["user2"]["id"],
            "organization_id": db_data["organization"]["id"],
            "firstname": db_data["user2"]["firstname"],
            "lastname": db_data["user2"]["lastname"],
            "email": db_data["user2"]["email"],
            "is_superadmin": db_data["user2"]["is_superadmin"],
            "created_at": ANY,
            "updated_at": ANY,
            "is_account_admin": db_data["user2_account2"]["is_admin"],
            "roles": [],
        },
        {
            "id": db_data["user3"]["id"],
            "organization_id": db_data["organization"]["id"],
            "firstname": db_data["user3"]["firstname"],
            "lastname": db_data["user3"]["lastname"],
            "email": db_data["user3"]["email"],
            "is_superadmin": db_data["user3"]["is_superadmin"],
            "created_at": ANY,
            "updated_at": ANY,
            "is_account_admin": db_data["user3_account2"]["is_admin"],
            "roles": [],
        },
        {
            "id": db_data["user4"]["id"],
            "organization_id": db_data["organization"]["id"],
            "firstname": db_data["user4"]["firstname"],
            "lastname": db_data["user4"]["lastname"],
            "email": db_data["user4"]["email"],
            "is_superadmin": db_data["user4"]["is_superadmin"],
            "created_at": ANY,
            "updated_at": ANY,
            "is_account_admin": db_data["user4_account2"]["is_admin"],
            "roles": [],
        },
    ]

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_get_account_user_list_with_existing_account_id_and_valid_access_token_and_authenticating_user_is_not_superadmin_and_is_not_assigned_to_account(
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

    existing_account_id = db_data["account1"]["id"]

    response = await client.request(
        method="GET",
        url=f"/accounts/{existing_account_id}/users",
        headers=headers,
    )

    assert response.status_code == 403
    actual_response_payload = response.json()

    expected_response_payload = {
        "detail": f"logged-in user - '{db_data['user3']['id']}' - is not assigned to account - '{existing_account_id}'"
    }

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_get_account_user_list_with_non_existent_account_id_and_valid_access_token_and_authenticating_user_exists_in_db(
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

    non_existent_account_id = "d1df1a9e-4c01-4302-a74d-fe1ec9db7339"

    response = await client.request(
        method="GET",
        url=f"/accounts/{non_existent_account_id}/users",
        headers=headers,
    )

    assert response.status_code == 404
    actual_response_payload = response.json()

    expected_response_payload = {
        "detail": f"Account - '{non_existent_account_id}' - not found"
    }

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_get_account_user_list_with_existing_account_id_and_existing_top_level_project_id_assigned_filter_with_valid_access_token_and_authenticating_user_is_superadmin(
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

    existing_account_id = db_data["account2"]["id"]
    existing_top_level_project_filter_id = db_data["project1"]["id"]
    response = await client.request(
        method="GET",
        url=f"/accounts/{existing_account_id}/users?project_id={existing_top_level_project_filter_id}&assigned=true",
        headers=headers,
    )

    assert response.status_code == 200
    actual_response_payload = response.json()
    expected_response_payload = expected_response_payload = [
        {
            "id": db_data["user2"]["id"],
            "organization_id": db_data["organization"]["id"],
            "firstname": db_data["user2"]["firstname"],
            "lastname": db_data["user2"]["lastname"],
            "email": db_data["user2"]["email"],
            "is_superadmin": db_data["user2"]["is_superadmin"],
            "created_at": ANY,
            "updated_at": ANY,
            "is_account_admin": db_data["user2_account2"]["is_admin"],
            "roles": [],
        },
        {
            "id": db_data["user4"]["id"],
            "organization_id": db_data["organization"]["id"],
            "firstname": db_data["user4"]["firstname"],
            "lastname": db_data["user4"]["lastname"],
            "email": db_data["user4"]["email"],
            "is_superadmin": db_data["user4"]["is_superadmin"],
            "created_at": ANY,
            "updated_at": ANY,
            "is_account_admin": db_data["user4_account2"]["is_admin"],
            "roles": [],
        },
    ]

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_get_account_user_list_with_existing_account_id_and_existing_top_level_project_id_not_assigned_filter_with_valid_access_token_and_authenticating_user_is_superadmin(
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

    existing_account_id = db_data["account2"]["id"]
    existing_top_level_project_filter_id = db_data["project1"]["id"]
    response = await client.request(
        method="GET",
        url=f"/accounts/{existing_account_id}/users?project_id={existing_top_level_project_filter_id}&assigned=false",
        headers=headers,
    )

    assert response.status_code == 200
    actual_response_payload = response.json()
    print(f"actual = {actual_response_payload }")

    expected_response_payload = [
        {
            "id": db_data["user3"]["id"],
            "organization_id": db_data["organization"]["id"],
            "firstname": db_data["user3"]["firstname"],
            "lastname": db_data["user3"]["lastname"],
            "email": db_data["user3"]["email"],
            "is_superadmin": db_data["user3"]["is_superadmin"],
            "created_at": ANY,
            "updated_at": ANY,
            "is_account_admin": db_data["user3_account2"]["is_admin"],
            "roles": [],
        }
    ]

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_get_account_user_list_with_existing_account_id_and_existing_top_level_project_id_assigned_filter_with_valid_access_token_and_authenticating_user_is_account_admin(
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

    existing_account_id = db_data["account2"]["id"]
    existing_top_level_project_filter_id = db_data["project1"]["id"]
    response = await client.request(
        method="GET",
        url=f"/accounts/{existing_account_id}/users?project_id={existing_top_level_project_filter_id}&assigned=true",
        headers=headers,
    )

    assert response.status_code == 200
    actual_response_payload = response.json()
    expected_response_payload = expected_response_payload = [
        {
            "id": db_data["user2"]["id"],
            "organization_id": db_data["organization"]["id"],
            "firstname": db_data["user2"]["firstname"],
            "lastname": db_data["user2"]["lastname"],
            "email": db_data["user2"]["email"],
            "is_superadmin": db_data["user2"]["is_superadmin"],
            "created_at": ANY,
            "updated_at": ANY,
            "is_account_admin": db_data["user2_account2"]["is_admin"],
            "roles": [],
        },
        {
            "id": db_data["user4"]["id"],
            "organization_id": db_data["organization"]["id"],
            "firstname": db_data["user4"]["firstname"],
            "lastname": db_data["user4"]["lastname"],
            "email": db_data["user4"]["email"],
            "is_superadmin": db_data["user4"]["is_superadmin"],
            "created_at": ANY,
            "updated_at": ANY,
            "is_account_admin": db_data["user4_account2"]["is_admin"],
            "roles": [],
        },
    ]

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_get_account_user_list_with_existing_account_id_and_existing_top_level_project_id_not_assigned_filter_with_valid_access_token_and_authenticating_user_is_account_admin(
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

    existing_account_id = db_data["account2"]["id"]
    existing_top_level_project_filter_id = db_data["project1"]["id"]
    response = await client.request(
        method="GET",
        url=f"/accounts/{existing_account_id}/users?project_id={existing_top_level_project_filter_id}&assigned=false",
        headers=headers,
    )

    assert response.status_code == 200
    actual_response_payload = response.json()
    expected_response_payload = [
        {
            "id": db_data["user3"]["id"],
            "organization_id": db_data["organization"]["id"],
            "firstname": db_data["user3"]["firstname"],
            "lastname": db_data["user3"]["lastname"],
            "email": db_data["user3"]["email"],
            "is_superadmin": db_data["user3"]["is_superadmin"],
            "created_at": ANY,
            "updated_at": ANY,
            "is_account_admin": db_data["user3_account2"]["is_admin"],
            "roles": [],
        }
    ]

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_get_account_user_list_with_existing_account_id_and_existing_top_level_project_id_assigned_filter_with_valid_access_token_and_authenticating_user_is_project_admin(
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

    existing_account_id = db_data["account2"]["id"]
    existing_top_level_project_filter_id = db_data["project1"]["id"]
    response = await client.request(
        method="GET",
        url=f"/accounts/{existing_account_id}/users?project_id={existing_top_level_project_filter_id}&assigned=true",
        headers=headers,
    )

    assert response.status_code == 200
    actual_response_payload = response.json()
    expected_response_payload = expected_response_payload = [
        {
            "id": db_data["user2"]["id"],
            "organization_id": db_data["organization"]["id"],
            "firstname": db_data["user2"]["firstname"],
            "lastname": db_data["user2"]["lastname"],
            "email": db_data["user2"]["email"],
            "is_superadmin": db_data["user2"]["is_superadmin"],
            "created_at": ANY,
            "updated_at": ANY,
            "is_account_admin": db_data["user2_account2"]["is_admin"],
            "roles": [],
        },
        {
            "id": db_data["user4"]["id"],
            "organization_id": db_data["organization"]["id"],
            "firstname": db_data["user4"]["firstname"],
            "lastname": db_data["user4"]["lastname"],
            "email": db_data["user4"]["email"],
            "is_superadmin": db_data["user4"]["is_superadmin"],
            "created_at": ANY,
            "updated_at": ANY,
            "is_account_admin": db_data["user4_account2"]["is_admin"],
            "roles": [],
        },
    ]

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_get_account_user_list_with_existing_account_id_and_existing_top_level_project_id_not_assigned_filter_with_valid_access_token_and_authenticating_user_is_project_admin(
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

    existing_account_id = db_data["account2"]["id"]
    existing_top_level_project_filter_id = db_data["project1"]["id"]
    response = await client.request(
        method="GET",
        url=f"/accounts/{existing_account_id}/users?project_id={existing_top_level_project_filter_id}&assigned=false",
        headers=headers,
    )

    assert response.status_code == 200
    actual_response_payload = response.json()
    expected_response_payload = [
        {
            "id": db_data["user3"]["id"],
            "organization_id": db_data["organization"]["id"],
            "firstname": db_data["user3"]["firstname"],
            "lastname": db_data["user3"]["lastname"],
            "email": db_data["user3"]["email"],
            "is_superadmin": db_data["user3"]["is_superadmin"],
            "created_at": ANY,
            "updated_at": ANY,
            "is_account_admin": db_data["user3_account2"]["is_admin"],
            "roles": [],
        }
    ]

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_get_account_user_list_with_existing_account_id_and_non_existent_project_id_filter_with_valid_access_token_and_authenticating_user_is_superadmin(
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

    existing_account_id = db_data["account2"]["id"]
    non_existent_project_filter_id = "d1df1a9e-4c01-4302-a74d-fe1ec9db7339"
    response = await client.request(
        method="GET",
        url=f"/accounts/{existing_account_id}/users?project_id={non_existent_project_filter_id}",
        headers=headers,
    )

    assert response.status_code == 404
    actual_response_payload = response.json()
    expected_response_payload = {
        "detail": f"Project - '{non_existent_project_filter_id}' - not found in account - '{existing_account_id}'"
    }

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_get_account_user_list_with_existing_account_id_and_non_existent_project_id_filter_with_valid_access_token_and_authenticating_user_is_not_superadmin_and_is_assigned_to_account(
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

    existing_account_id = db_data["account2"]["id"]
    non_existent_project_filter_id = "d1df1a9e-4c01-4302-a74d-fe1ec9db7339"
    response = await client.request(
        method="GET",
        url=f"/accounts/{existing_account_id}/users?project_id={non_existent_project_filter_id}",
        headers=headers,
    )

    assert response.status_code == 404
    actual_response_payload = response.json()
    expected_response_payload = {
        "detail": f"Project - '{non_existent_project_filter_id}' - not found in account - '{existing_account_id}'"
    }

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_get_account_user_list_with_existing_account_id_and_existent_non_top_level_project_id_filter_with_valid_access_token_and_authenticating_user_is_superadmin(
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

    existing_account_id = db_data["account2"]["id"]
    existent_non_top_level_project_filter_id = db_data["project2"]["id"]
    response = await client.request(
        method="GET",
        url=f"/accounts/{existing_account_id}/users?project_id={existent_non_top_level_project_filter_id}",
        headers=headers,
    )

    assert response.status_code == 422
    actual_response_payload = response.json()
    expected_response_payload = {
        "detail": f"Project - '{existent_non_top_level_project_filter_id}' - is not a top-level project under account - '{existing_account_id}'"
    }

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_get_account_user_list_with_existing_account_id_and_existent_non_top_level_project_id_filter_with_valid_access_token_and_authenticating_user_is_not_superadmin_and_is_assigned_to_account(
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

    existing_account_id = db_data["account2"]["id"]
    existent_non_top_level_project_filter_id = db_data["project2"]["id"]
    response = await client.request(
        method="GET",
        url=f"/accounts/{existing_account_id}/users?project_id={existent_non_top_level_project_filter_id}",
        headers=headers,
    )

    assert response.status_code == 422
    actual_response_payload = response.json()
    expected_response_payload = {
        "detail": f"Project - '{existent_non_top_level_project_filter_id}' - is not a top-level project under account - '{existing_account_id}'"
    }

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
@patch("rbac_api.auth.impl.RedisSingleton")
async def test_get_account_user_list_with_existing_account_id_and_existent_top_level_project_id_filter_with_valid_access_token_and_authenticating_user_is_not_superadmin_and_not_account_admin_and_not_project_admin_and_is_assigned_to_account(
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

    existing_account_id = db_data["account2"]["id"]
    existing_top_level_project_filter_id = db_data["project1"]["id"]
    response = await client.request(
        method="GET",
        url=f"/accounts/{existing_account_id}/users?project_id={existing_top_level_project_filter_id}",
        headers=headers,
    )

    assert response.status_code == 403
    actual_response_payload = response.json()
    expected_response_payload = {
        "detail": f"logged-in user - '{db_data['user3']['id']}' - does not have superadmin privileges or account-admin privileges in account - '{existing_account_id}' - or project-admin privileges in project - '{existing_top_level_project_filter_id}' - to view account users with project filter in account - '{existing_account_id}'"
    }

    assert actual_response_payload == expected_response_payload


@pytest.mark.asyncio
async def test_get_account_user_list_with_existing_account_id_and_no_access_token(
    client, setup_initial_data
):

    headers = {"Authorization": " ", "Content-Type": "application/json"}

    existing_account_id = db_data["account1"]["id"]

    response = await client.request(
        method="GET",
        url=f"/accounts/{existing_account_id}/users",
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
async def test_get_account_user_list_with_existing_account_id_and_invalid_or_expired_access_token(
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

    existing_account_id = db_data["account1"]["id"]

    response = await client.request(
        method="GET",
        url=f"/accounts/{existing_account_id}/users",
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
async def test_get_account_user_list_with_existing_account_id_and_valid_access_token_and_authenticating_user_does_not_exist_in_db(
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

    existing_account_id = db_data["account1"]["id"]

    response = await client.request(
        method="GET",
        url=f"/accounts/{existing_account_id}/users",
        headers=headers,
    )

    assert response.status_code == 401
    actual_response_payload = response.json()

    expected_response_payload = {"detail": "user is unauthenticated"}

    assert actual_response_payload == expected_response_payload
