#!/usr/bin/env python3
"""
Quick script to create a new role

Usage:
    python scripts/create_role.py analyst "view_project,export_data,view_reports"
    python scripts/create_role.py developer "create_workflow,edit_workflow,execute_workflow" --resource-type workflow
"""

import sys
import httpx
import asyncio
from typing import List


AUTH_API_URL = "http://localhost:8004/auth-api"
SUPERUSER_TOKEN = "your-superuser-token-here"  # Update this!


def generate_role_policy(
    role_name: str,
    actions: List[str],
    resource_type: str = "project",
    description: str = "",
) -> str:
    """Generate Rego policy for a new role"""

    actions_str = ", ".join([f'"{action}"' for action in actions])

    rego = f"""package rbac

import rego.v1

# ----------------------------------------------------------------------------
# {role_name.upper()} ROLE
# {description or f"Custom role: {role_name}"}
# Permissions: {", ".join(actions)}
# Resource type: {resource_type}
# ----------------------------------------------------------------------------

role_check(assignment) if {{
    assignment.role == "{role_name}"
    input.resource.type == "{resource_type}"
    input.action in {{{actions_str}}}
}}
"""
    return rego


async def create_role(
    role_name: str,
    actions: List[str],
    resource_type: str = "project",
    description: str = "",
):
    """Create a new role by uploading policy to OPA"""

    print(f"Creating role: {role_name}")
    print(f"  Resource type: {resource_type}")
    print(f"  Actions: {', '.join(actions)}")
    print()

    # Generate policy
    rego_code = generate_role_policy(role_name, actions, resource_type, description)

    print("Generated policy:")
    print("-" * 80)
    print(rego_code)
    print("-" * 80)
    print()

    # Upload to OPA
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{AUTH_API_URL}/api/policies/upload",
                json={"module_name": f"rbac/{role_name}_role", "rego_code": rego_code},
                headers={
                    "Authorization": f"Bearer {SUPERUSER_TOKEN}",
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )

            if response.status_code == 200:
                print(f"✅ Role '{role_name}' created successfully!")
                print()
                print("Next steps:")
                print("1. Assign the role to a user:")
                print("   POST /api/rbac/role-assignments")
                print("   {")
                print('     "user_id": 1,')
                print(f'     "role": "{role_name}",')
                print(f'     "resource_type": "{resource_type}",')
                print('     "resource_id": "your-resource-id"')
                print("   }")
                print()
                print("2. Test authorization:")
                print("   POST /api/authz/check_access")
                print("   {")
                print('     "user_id": 1,')
                print(f'     "action": "{actions[0]}",')
                print(f'     "resource": {{"type": "{resource_type}", "id": "..."}}')
                print("   }")
            else:
                print(f"❌ Failed to create role: {response.status_code}")
                print(f"   Response: {response.text}")

        except Exception as e:
            print(f"❌ Error: {e}")


async def list_roles():
    """List all existing roles"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{AUTH_API_URL}/api/policies",
                headers={"Authorization": f"Bearer {SUPERUSER_TOKEN}"},
                timeout=10.0,
            )

            if response.status_code == 200:
                policies = response.json()
                print("Existing policy modules:")
                for policy in policies:
                    print(f"  - {policy['name']}")
            else:
                print(f"Failed to list policies: {response.status_code}")

        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main entry point"""

    if len(sys.argv) < 2:
        print("Usage:")
        print("  Create role:")
        print(
            "    python scripts/create_role.py <role_name> <actions> [--resource-type TYPE] [--description DESC]"
        )
        print()
        print("  Examples:")
        print(
            "    python scripts/create_role.py analyst 'view_project,export_data,view_reports'"
        )
        print(
            "    python scripts/create_role.py developer 'create_workflow,edit_workflow' --resource-type workflow"
        )
        print()
        print("  List existing roles:")
        print("    python scripts/create_role.py --list")
        sys.exit(1)

    if sys.argv[1] == "--list":
        asyncio.run(list_roles())
        return

    role_name = sys.argv[1]

    if len(sys.argv) < 3:
        print("Error: Actions required")
        print(
            "Example: python scripts/create_role.py analyst 'view_project,export_data'"
        )
        sys.exit(1)

    actions = [a.strip() for a in sys.argv[2].split(",")]

    # Parse optional arguments
    resource_type = "project"
    description = ""

    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == "--resource-type" and i + 1 < len(sys.argv):
            resource_type = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--description" and i + 1 < len(sys.argv):
            description = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    asyncio.run(create_role(role_name, actions, resource_type, description))


if __name__ == "__main__":
    main()
