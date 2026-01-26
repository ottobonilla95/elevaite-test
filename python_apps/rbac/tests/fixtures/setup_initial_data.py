import pytest
from .. import models

db_data = {
    "organization": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "elevAIte organization name",
        "description": "elevAIte organization desc",
    },
    "account1": {
        "id": "33edce67-caff-437b-8d01-b6ed8b26f31a",
        "organization_id": "123e4567-e89b-12d3-a456-426614174000",
        "description": "account 1 description",
        "name": "Account 1",
    },
    "account2": {
        "id": "b15f0661-6f0b-4fde-b588-5177aff76e55",
        "organization_id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Account 2",
        "description": "account 2 description",
    },
    "account3": {
        "id": "1902ac41-86fa-44ca-b619-88d9cfbc1b06",
        "organization_id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Account 3",
        "description": "account 3 description",
    },
    "account4": {
        "id": "3a542f4a-a623-4167-bfaa-076084ef820d",
        "organization_id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Account 4",
        "description": "account 4 description",
    },
    "account5": {
        "id": "a6500bf7-591a-454d-af39-850a9a17762e",
        "organization_id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Account 5",
        "description": "account 5 description",
    },
    "default_account": {
        "id": "9849ec30-b236-496a-9695-b9c90f28e554",
        "organization_id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "elevAIte Default Account",
        "description": "default account description",
    },
    "user1": {
        "id": "6066df3a-fb7a-4492-8ed6-9486fa503298",
        "organization_id": "123e4567-e89b-12d3-a456-426614174000",
        "firstname": "user1_fname",
        "lastname": "user1_lname",
        "email": "user1@gmail.com",
        "is_superadmin": True,
    },
    "user2": {
        "id": "4d4a59fd-f2c4-478e-a2ad-e30ac5b624be",
        "organization_id": "123e4567-e89b-12d3-a456-426614174000",
        "firstname": "user2_fname",
        "lastname": "user2_lname",
        "email": "user2@gmail.com",
        "is_superadmin": False,
    },
    "user3": {
        "id": "f564c6dd-d22e-4b34-8f63-fab4143de88b",
        "organization_id": "123e4567-e89b-12d3-a456-426614174000",
        "firstname": "user3_fname",
        "lastname": "user3_lname",
        "email": "user3@gmail.com",
        "is_superadmin": False,
    },
    "user4": {
        "id": "4f089ac8-553e-4253-9e87-772fc2690ea4",
        "organization_id": "123e4567-e89b-12d3-a456-426614174000",
        "firstname": "user4_fname",
        "lastname": "user4_lname",
        "email": "user4@gmail.com",
        "is_superadmin": False,
    },
    "user5": {
        "id": "4f089ac9-553e-4253-9e87-772fc2690ea4",
        "organization_id": "123e4567-e89b-12d3-a456-426614174000",
        "firstname": "user5_fname",
        "lastname": "user5_lname",
        "email": "user5@gmail.com",
        "is_superadmin": True,
    },
    "user1_default_account": {
        "id": "51195bd4-47c7-480f-a3d4-02c6295456c4",
        "user_id": "6066df3a-fb7a-4492-8ed6-9486fa503298",
        "account_id": "9849ec30-b236-496a-9695-b9c90f28e554",
        "is_admin": False,
    },
    "user2_default_account": {
        "id": "08a1023f-ffee-4c6e-adac-64af39222876",
        "user_id": "4d4a59fd-f2c4-478e-a2ad-e30ac5b624be",
        "account_id": "9849ec30-b236-496a-9695-b9c90f28e554",
        "is_admin": False,
    },
    "user2_account2": {
        "id": "7d9aaa98-14c4-4db5-8b85-45629a81d951",
        "user_id": "4d4a59fd-f2c4-478e-a2ad-e30ac5b624be",
        "account_id": "b15f0661-6f0b-4fde-b588-5177aff76e55",
        "is_admin": True,
    },
    "user3_default_account": {
        "id": "1d44d9aa-061c-4d0b-86c4-0fe4b66a5c93",
        "user_id": "f564c6dd-d22e-4b34-8f63-fab4143de88b",
        "account_id": "9849ec30-b236-496a-9695-b9c90f28e554",
        "is_admin": False,
    },
    "user3_account2": {
        "id": "5d9aaa98-14c4-4db5-8b85-45629a81d951",
        "user_id": "f564c6dd-d22e-4b34-8f63-fab4143de88b",
        "account_id": "b15f0661-6f0b-4fde-b588-5177aff76e55",
        "is_admin": False,
    },
    "user3_account4": {
        "id": "8d4aaa94-14c4-4db5-8b85-45629a81d951",
        "user_id": "f564c6dd-d22e-4b34-8f63-fab4143de88b",
        "account_id": "3a542f4a-a623-4167-bfaa-076084ef820d",
        "is_admin": False,
    },
    "user4_default_account": {
        "id": "3d44d9aa-061c-4d0b-86c4-0fe4b66a5c93",
        "user_id": "4f089ac8-553e-4253-9e87-772fc2690ea4",
        "account_id": "9849ec30-b236-496a-9695-b9c90f28e554",
        "is_admin": False,
    },
    "user4_account2": {
        "id": "8d9aaa98-14c4-4db5-8b85-45629a81d951",
        "user_id": "4f089ac8-553e-4253-9e87-772fc2690ea4",
        "account_id": "b15f0661-6f0b-4fde-b588-5177aff76e55",
        "is_admin": False,
    },
    "user4_account4": {
        "id": "8d4aaa98-14c4-4db5-8b85-45629a81d951",
        "user_id": "4f089ac8-553e-4253-9e87-772fc2690ea4",
        "account_id": "3a542f4a-a623-4167-bfaa-076084ef820d",
        "is_admin": True,
    },
    "user4_account5": {
        "id": "8d4aaa98-15c4-4db5-8b85-45629a81d951",
        "user_id": "4f089ac8-553e-4253-9e87-772fc2690ea4",
        "account_id": "a6500bf7-591a-454d-af39-850a9a17762e",
        "is_admin": True,
    },
    "user5_default_account": {
        "id": "1d44d9aa-063c-4d0b-86c4-0fe4b66a5c93",
        "user_id": "4f089ac9-553e-4253-9e87-772fc2690ea4",
        "account_id": "9849ec30-b236-496a-9695-b9c90f28e554",
        "is_admin": False,
    },
    "user5_account4": {
        "id": "8d4aab98-14c4-4db5-8b85-45629a81d951",
        "user_id": "4f089ac9-553e-4253-9e87-772fc2690ea4",
        "account_id": "3a542f4a-a623-4167-bfaa-076084ef820d",
        "is_admin": False,
    },
    "user5_account5": {
        "id": "8d4aab98-14c4-4dc5-8b85-45629a81d951",
        "user_id": "4f089ac9-553e-4253-9e87-772fc2690ea4",
        "account_id": "a6500bf7-591a-454d-af39-850a9a17762e",
        "is_admin": False,
    },
    "project1": {
        "id": "6c717b08-da35-460a-ac11-7ad275ca48bc",
        "name": "Account2_project1",
        "account_id": "b15f0661-6f0b-4fde-b588-5177aff76e55",
        "parent_project_id": None,
        "description": "Account2_project1 description",
        "creator_id": "6066df3a-fb7a-4492-8ed6-9486fa503298",
    },
    "project2": {
        "id": "c1954046-0779-48d8-9059-cc7700d31890",
        "name": "Account2_project1_child1",
        "account_id": "b15f0661-6f0b-4fde-b588-5177aff76e55",
        "parent_project_id": "6c717b08-da35-460a-ac11-7ad275ca48bc",
        "description": "Account2_project1_child1 description",
        "creator_id": "6066df3a-fb7a-4492-8ed6-9486fa503298",
    },
    "project3": {
        "id": "ff2ea384-1086-461a-88a1-fb97cd88946e",
        "name": "Account2_project1_child2",
        "account_id": "b15f0661-6f0b-4fde-b588-5177aff76e55",
        "parent_project_id": "6c717b08-da35-460a-ac11-7ad275ca48bc",
        "description": "Account2_project1_child2 description",
        "creator_id": "6066df3a-fb7a-4492-8ed6-9486fa503298",
    },
    "project4": {
        "id": "f1160094-a517-4665-ad52-63b7c119262b",
        "name": "Account2_project1_child1_child1",
        "account_id": "b15f0661-6f0b-4fde-b588-5177aff76e55",
        "parent_project_id": "c1954046-0779-48d8-9059-cc7700d31890",
        "description": "Account2_project1_child1_child1 description",
        "creator_id": "6066df3a-fb7a-4492-8ed6-9486fa503298",
    },
    "user1_project1": {
        "id": "ab55bd5f-e8f0-4a20-a859-b2901e52afeb",
        "user_id": "6066df3a-fb7a-4492-8ed6-9486fa503298",
        "project_id": "6c717b08-da35-460a-ac11-7ad275ca48bc",
        "is_admin": True,
        "permission_overrides": dict(),
    },
    "user1_project2": {
        "id": "4c0844f4-0a22-4d1c-a458-6e80bcc253ff",
        "user_id": "6066df3a-fb7a-4492-8ed6-9486fa503298",
        "project_id": "c1954046-0779-48d8-9059-cc7700d31890",
        "is_admin": True,
        "permission_overrides": dict(),
    },
    "user1_project3": {
        "id": "afbe997a-669c-427c-9920-e85dd66ae4b5",
        "user_id": "6066df3a-fb7a-4492-8ed6-9486fa503298",
        "project_id": "ff2ea384-1086-461a-88a1-fb97cd88946e",
        "is_admin": True,
        "permission_overrides": dict(),
    },
    "user1_project4": {
        "id": "24799281-e269-431c-9502-f3c732f30811",
        "user_id": "6066df3a-fb7a-4492-8ed6-9486fa503298",
        "project_id": "f1160094-a517-4665-ad52-63b7c119262b",
        "is_admin": True,
        "permission_overrides": dict(),
    },
    "user2_project1": {
        "id": "8bc401c1-f93f-4a32-b158-787414ce26ba",
        "user_id": "4d4a59fd-f2c4-478e-a2ad-e30ac5b624be",
        "project_id": "6c717b08-da35-460a-ac11-7ad275ca48bc",
        "is_admin": True,
        "permission_overrides": dict(),
    },
    "user2_project2": {
        "id": "26d9c3e9-cca0-48b5-9c8e-e4f886236504",
        "user_id": "4d4a59fd-f2c4-478e-a2ad-e30ac5b624be",
        "project_id": "c1954046-0779-48d8-9059-cc7700d31890",
        "is_admin": False,
        "permission_overrides": dict(),
    },
    "user2_project3": {
        "id": "09e38126-4dde-4efc-a425-ea5e8ed94d89",
        "user_id": "4d4a59fd-f2c4-478e-a2ad-e30ac5b624be",
        "project_id": "ff2ea384-1086-461a-88a1-fb97cd88946e",
        "is_admin": False,
        "permission_overrides": dict(),
    },
    "user2_project4": {
        "id": "a102ad8e-2fdc-4543-9e9d-de7075fc9e18",
        "user_id": "4d4a59fd-f2c4-478e-a2ad-e30ac5b624be",
        "project_id": "f1160094-a517-4665-ad52-63b7c119262b",
        "is_admin": False,
        "permission_overrides": dict(),
    },
    "user4_project1": {
        "id": "b102ad8e-2fdc-4543-9e9d-de7075fc9e18",
        "user_id": "4f089ac8-553e-4253-9e87-772fc2690ea4",
        "project_id": "6c717b08-da35-460a-ac11-7ad275ca48bc",
        "is_admin": True,
        "permission_overrides": dict(),
    },
    "role1": {
        "id": "482f314c-ce36-4740-ab7f-81bbe157c042",
        "name": "Data Scientist",
        "permissions": {
            "ENTITY_Project": {
                "ACTION_READ": "Allow",
                "ACTION_CREATE": "Allow",
                "ENTITY_Apikey": {"ACTION_READ": "Allow", "ACTION_CREATE": "Allow"},
                "ENTITY_Dataset": {"ACTION_TAG": "Allow"},
                "ACTION_SERVICENOW": {"ACTION_TICKET": {"ACTION_INGEST": "Allow"}},
                "ENTITY_Collection": {"ACTION_READ": "Allow", "ACTION_CREATE": "Allow"},
            },
            # "ENTITY_Application": {
            #     "TYPENAMES_applicationType": {
            #         "TYPEVALUES_ingest": {
            #             "ENTITY_Instance": {
            #                 "ACTION_READ": "Allow",
            #                 "ACTION_CREATE": "Allow",
            #                 "ACTION_CONFIGURATION": {"ACTION_READ": "Allow"},
            #             },
            #             "ENTITY_Configuration": {
            #                 "ACTION_READ": "Allow",
            #                 "ACTION_CREATE": "Allow",
            #                 "ACTION_UPDATE": "Allow",
            #             },
            #         },
            #         "TYPEVALUES_preprocess": {
            #             "ACTION_READ": "Allow",
            #             "ENTITY_Instance": {
            #                 "ACTION_READ": "Allow",
            #                 "ACTION_CREATE": "Allow",
            #                 "ACTION_CONFIGURATION": {"ACTION_READ": "Allow"},
            #             },
            #             "ENTITY_Configuration": {
            #                 "ACTION_READ": "Allow",
            #                 "ACTION_CREATE": "Allow",
            #                 "ACTION_UPDATE": "Allow",
            #             },
            #         },
            #     }
            # },
        },
    },
    "role2": {
        "id": "a1df1a9e-4c01-4302-a74d-fe1ec9db7339",
        "name": "ML Engineer",
        "permissions": {
            "ENTITY_Project": {
                "ACTION_READ": "Allow",
                "ACTION_CREATE": "Allow",
                "ENTITY_Apikey": {"ACTION_READ": "Allow", "ACTION_CREATE": "Allow"},
                "ENTITY_Dataset": {"ACTION_TAG": "Allow"},
                "ACTION_SERVICENOW": {"ACTION_TICKET": {"ACTION_INGEST": "Allow"}},
                "ENTITY_Collection": {"ACTION_READ": "Allow", "ACTION_CREATE": "Allow"},
            },
            # "ENTITY_Application": {
            #     "TYPENAMES_applicationType": {
            #         "TYPEVALUES_preprocess": {
            #             "ACTION_READ": "Allow",
            #             "ENTITY_Instance": {
            #                 "ACTION_READ": "Allow",
            #                 "ACTION_CREATE": "Allow",
            #                 "ACTION_CONFIGURATION": {"ACTION_READ": "Allow"},
            #             },
            #             "ENTITY_Configuration": {
            #                 "ACTION_READ": "Allow",
            #                 "ACTION_CREATE": "Allow",
            #                 "ACTION_UPDATE": "Allow",
            #             },
            #         }
            #     }
            # },
        },
    },
    "role3": {
        "id": "e4f2b540-6ae6-407b-8436-26795f641557",
        "name": "ML OPS",
        "permissions": {
            "ENTITY_Project": {
                "ACTION_READ": "Allow",
                "ACTION_SERVICENOW": {"ACTION_TICKET": {"ACTION_INGEST": "Allow"}},
            }
        },
    },
}


@pytest.fixture(scope="function")
def setup_initial_data(test_session):
    organization = models.Organization(
        id=db_data["organization"]["id"],
        name=db_data["organization"]["name"],
        description=db_data["organization"]["description"],
    )
    user1 = models.User(
        id=db_data["user1"]["id"],
        organization_id=db_data["user1"]["organization_id"],
        firstname=db_data["user1"]["firstname"],
        lastname=db_data["user1"]["lastname"],
        email=db_data["user1"]["email"],
        is_superadmin=db_data["user1"]["is_superadmin"],
    )
    user2 = models.User(
        id=db_data["user2"]["id"],
        organization_id=db_data["user2"]["organization_id"],
        firstname=db_data["user2"]["firstname"],
        lastname=db_data["user2"]["lastname"],
        email=db_data["user2"]["email"],
        is_superadmin=db_data["user2"]["is_superadmin"],
    )
    user3 = models.User(
        id=db_data["user3"]["id"],
        organization_id=db_data["user3"]["organization_id"],
        firstname=db_data["user3"]["firstname"],
        lastname=db_data["user3"]["lastname"],
        email=db_data["user3"]["email"],
        is_superadmin=db_data["user3"]["is_superadmin"],
    )
    user4 = models.User(
        id=db_data["user4"]["id"],
        organization_id=db_data["user4"]["organization_id"],
        firstname=db_data["user4"]["firstname"],
        lastname=db_data["user4"]["lastname"],
        email=db_data["user4"]["email"],
        is_superadmin=db_data["user4"]["is_superadmin"],
    )
    user5 = models.User(
        id=db_data["user5"]["id"],
        organization_id=db_data["user5"]["organization_id"],
        firstname=db_data["user5"]["firstname"],
        lastname=db_data["user5"]["lastname"],
        email=db_data["user5"]["email"],
        is_superadmin=db_data["user5"]["is_superadmin"],
    )

    account1 = models.Account(
        id=db_data["account1"]["id"],
        organization_id=db_data["account1"]["organization_id"],
        name=db_data["account1"]["name"],
        description=db_data["account1"]["description"],
    )
    account2 = models.Account(
        id=db_data["account2"]["id"],
        organization_id=db_data["account2"]["organization_id"],
        name=db_data["account2"]["name"],
        description=db_data["account2"]["description"],
    )
    account3 = models.Account(
        id=db_data["account3"]["id"],
        organization_id=db_data["account3"]["organization_id"],
        name=db_data["account3"]["name"],
        description=db_data["account3"]["description"],
    )
    account4 = models.Account(
        id=db_data["account4"]["id"],
        organization_id=db_data["account4"]["organization_id"],
        name=db_data["account4"]["name"],
        description=db_data["account4"]["description"],
    )
    account5 = models.Account(
        id=db_data["account5"]["id"],
        organization_id=db_data["account5"]["organization_id"],
        name=db_data["account5"]["name"],
        description=db_data["account5"]["description"],
    )
    default_account = models.Account(
        id=db_data["default_account"]["id"],
        organization_id=db_data["default_account"]["organization_id"],
        name=db_data["default_account"]["name"],
        description=db_data["default_account"]["description"],
    )

    user1_default_account = models.User_Account(
        id=db_data["user1_default_account"]["id"],
        user_id=db_data["user1_default_account"]["user_id"],
        account_id=db_data["user1_default_account"]["account_id"],
        is_admin=db_data["user1_default_account"]["is_admin"],
    )
    user2_default_account = models.User_Account(
        id=db_data["user2_default_account"]["id"],
        user_id=db_data["user2_default_account"]["user_id"],
        account_id=db_data["user2_default_account"]["account_id"],
        is_admin=db_data["user2_default_account"]["is_admin"],
    )
    user2_account2 = models.User_Account(
        id=db_data["user2_account2"]["id"],
        user_id=db_data["user2_account2"]["user_id"],
        account_id=db_data["user2_account2"]["account_id"],
        is_admin=db_data["user2_account2"]["is_admin"],
    )
    user3_default_account = models.User_Account(
        id=db_data["user3_default_account"]["id"],
        user_id=db_data["user3_default_account"]["user_id"],
        account_id=db_data["user3_default_account"]["account_id"],
        is_admin=db_data["user3_default_account"]["is_admin"],
    )
    user3_account2 = models.User_Account(
        id=db_data["user3_account2"]["id"],
        user_id=db_data["user3_account2"]["user_id"],
        account_id=db_data["user3_account2"]["account_id"],
        is_admin=db_data["user3_account2"]["is_admin"],
    )
    user3_account4 = models.User_Account(
        id=db_data["user3_account4"]["id"],
        user_id=db_data["user3_account4"]["user_id"],
        account_id=db_data["user3_account4"]["account_id"],
        is_admin=db_data["user3_account4"]["is_admin"],
    )

    user4_default_account = models.User_Account(
        id=db_data["user4_default_account"]["id"],
        user_id=db_data["user4_default_account"]["user_id"],
        account_id=db_data["user4_default_account"]["account_id"],
        is_admin=db_data["user4_default_account"]["is_admin"],
    )
    user4_account2 = models.User_Account(
        id=db_data["user4_account2"]["id"],
        user_id=db_data["user4_account2"]["user_id"],
        account_id=db_data["user4_account2"]["account_id"],
        is_admin=db_data["user4_account2"]["is_admin"],
    )
    user4_account4 = models.User_Account(
        id=db_data["user4_account4"]["id"],
        user_id=db_data["user4_account4"]["user_id"],
        account_id=db_data["user4_account4"]["account_id"],
        is_admin=db_data["user4_account4"]["is_admin"],
    )
    user4_account5 = models.User_Account(
        id=db_data["user4_account5"]["id"],
        user_id=db_data["user4_account5"]["user_id"],
        account_id=db_data["user4_account5"]["account_id"],
        is_admin=db_data["user4_account5"]["is_admin"],
    )

    user5_default_account = models.User_Account(
        id=db_data["user5_default_account"]["id"],
        user_id=db_data["user5_default_account"]["user_id"],
        account_id=db_data["user5_default_account"]["account_id"],
        is_admin=db_data["user5_default_account"]["is_admin"],
    )
    user5_account4 = models.User_Account(
        id=db_data["user5_account4"]["id"],
        user_id=db_data["user5_account4"]["user_id"],
        account_id=db_data["user5_account4"]["account_id"],
        is_admin=db_data["user5_account4"]["is_admin"],
    )
    user5_account5 = models.User_Account(
        id=db_data["user5_account5"]["id"],
        user_id=db_data["user5_account5"]["user_id"],
        account_id=db_data["user5_account5"]["account_id"],
        is_admin=db_data["user5_account5"]["is_admin"],
    )

    project1 = models.Project(
        id=db_data["project1"]["id"],
        name=db_data["project1"]["name"],
        account_id=db_data["project1"]["account_id"],
        parent_project_id=db_data["project1"]["parent_project_id"],
        description=db_data["project1"]["description"],
        creator_id=db_data["project1"]["creator_id"],
    )
    project2 = models.Project(
        id=db_data["project2"]["id"],
        name=db_data["project2"]["name"],
        account_id=db_data["project2"]["account_id"],
        parent_project_id=db_data["project2"]["parent_project_id"],
        description=db_data["project2"]["description"],
        creator_id=db_data["project2"]["creator_id"],
    )
    project3 = models.Project(
        id=db_data["project3"]["id"],
        name=db_data["project3"]["name"],
        account_id=db_data["project3"]["account_id"],
        parent_project_id=db_data["project3"]["parent_project_id"],
        description=db_data["project3"]["description"],
        creator_id=db_data["project3"]["creator_id"],
    )
    project4 = models.Project(
        id=db_data["project4"]["id"],
        name=db_data["project4"]["name"],
        account_id=db_data["project4"]["account_id"],
        parent_project_id=db_data["project4"]["parent_project_id"],
        description=db_data["project4"]["description"],
        creator_id=db_data["project4"]["creator_id"],
    )

    user1_project1 = models.User_Project(
        id=db_data["user1_project1"]["id"],
        user_id=db_data["user1_project1"]["user_id"],
        project_id=db_data["user1_project1"]["project_id"],
        is_admin=db_data["user1_project1"]["is_admin"],
        permission_overrides=db_data["user1_project1"]["permission_overrides"],
    )
    user1_project2 = models.User_Project(
        id=db_data["user1_project2"]["id"],
        user_id=db_data["user1_project2"]["user_id"],
        project_id=db_data["user1_project2"]["project_id"],
        is_admin=db_data["user1_project2"]["is_admin"],
        permission_overrides=db_data["user1_project2"]["permission_overrides"],
    )
    user1_project3 = models.User_Project(
        id=db_data["user1_project3"]["id"],
        user_id=db_data["user1_project3"]["user_id"],
        project_id=db_data["user1_project3"]["project_id"],
        is_admin=db_data["user1_project3"]["is_admin"],
        permission_overrides=db_data["user1_project3"]["permission_overrides"],
    )
    user1_project4 = models.User_Project(
        id=db_data["user1_project4"]["id"],
        user_id=db_data["user1_project4"]["user_id"],
        project_id=db_data["user1_project4"]["project_id"],
        is_admin=db_data["user1_project4"]["is_admin"],
        permission_overrides=db_data["user1_project4"]["permission_overrides"],
    )

    user2_project1 = models.User_Project(
        id=db_data["user2_project1"]["id"],
        user_id=db_data["user2_project1"]["user_id"],
        project_id=db_data["user2_project1"]["project_id"],
        is_admin=db_data["user2_project1"]["is_admin"],
        permission_overrides=db_data["user2_project1"]["permission_overrides"],
    )
    user2_project2 = models.User_Project(
        id=db_data["user2_project2"]["id"],
        user_id=db_data["user2_project2"]["user_id"],
        project_id=db_data["user2_project2"]["project_id"],
        is_admin=db_data["user2_project2"]["is_admin"],
        permission_overrides=db_data["user2_project2"]["permission_overrides"],
    )
    user2_project3 = models.User_Project(
        id=db_data["user2_project3"]["id"],
        user_id=db_data["user2_project3"]["user_id"],
        project_id=db_data["user2_project3"]["project_id"],
        is_admin=db_data["user2_project3"]["is_admin"],
        permission_overrides=db_data["user2_project3"]["permission_overrides"],
    )
    user2_project4 = models.User_Project(
        id=db_data["user2_project4"]["id"],
        user_id=db_data["user2_project4"]["user_id"],
        project_id=db_data["user2_project4"]["project_id"],
        is_admin=db_data["user2_project4"]["is_admin"],
        permission_overrides=db_data["user2_project4"]["permission_overrides"],
    )
    user4_project1 = models.User_Project(
        id=db_data["user4_project1"]["id"],
        user_id=db_data["user4_project1"]["user_id"],
        project_id=db_data["user4_project1"]["project_id"],
        is_admin=db_data["user4_project1"]["is_admin"],
        permission_overrides=db_data["user4_project1"]["permission_overrides"],
    )

    role1 = models.Role(
        id=db_data["role1"]["id"],
        name=db_data["role1"]["name"],
        permissions=db_data["role1"]["permissions"],
    )
    role2 = models.Role(
        id=db_data["role2"]["id"],
        name=db_data["role2"]["name"],
        permissions=db_data["role2"]["permissions"],
    )
    role3 = models.Role(
        id=db_data["role3"]["id"],
        name=db_data["role3"]["name"],
        permissions=db_data["role3"]["permissions"],
    )

    test_session.add_all(
        [
            organization,
            user1,
            user2,
            user3,
            user4,
            user5,
            account1,
            account2,
            account3,
            account4,
            account5,
            default_account,
            user1_default_account,
            user2_default_account,
            user3_default_account,
            user4_default_account,
            user5_default_account,
            user2_account2,
            user3_account2,
            user3_account4,
            user4_account2,
            user4_account4,
            user4_account5,
            user5_account4,
            user5_account5,
            project1,
            project2,
            project3,
            project4,
            user1_project1,
            user1_project2,
            user1_project3,
            user1_project4,
            user2_project1,
            user2_project2,
            user2_project3,
            user2_project4,
            user4_project1,
            role1,
            role2,
            role3,
        ]
    )
    test_session.commit()
    yield
    test_session.query(models.User).delete()
    test_session.query(models.Role).delete()
    test_session.query(models.Organization).delete()
    test_session.commit()
