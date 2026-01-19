#!/usr/bin/env python3
"""
Run Alembic migrations for all tenant schemas.

Usage:
    python scripts/migrate_tenant_schemas.py [--tenants tenant1,tenant2,...]

If --tenants is not provided, uses DEFAULT_TENANTS from multitenancy config.
"""

import os
import sys
import argparse
import subprocess

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.multitenancy import DEFAULT_TENANTS, multitenancy_settings


def migrate_schema(schema_name: str, alembic_args: list[str] = None) -> bool:
    """Run alembic upgrade for a specific schema."""
    alembic_args = alembic_args or ["upgrade", "head"]
    
    env = os.environ.copy()
    env["ALEMBIC_SCHEMA"] = schema_name
    
    cmd = ["alembic"] + alembic_args
    print(f"\n{'='*60}")
    print(f"Migrating schema: {schema_name}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    result = subprocess.run(
        cmd,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        env=env,
    )
    
    if result.returncode != 0:
        print(f"ERROR: Migration failed for schema {schema_name}")
        return False
    
    print(f"SUCCESS: Schema {schema_name} migrated")
    return True


def main():
    parser = argparse.ArgumentParser(description="Run Alembic migrations for tenant schemas")
    parser.add_argument(
        "--tenants",
        type=str,
        help="Comma-separated list of tenant IDs (default: all configured tenants)",
    )
    parser.add_argument(
        "--public-only",
        action="store_true",
        help="Only migrate the public schema (no tenant schemas)",
    )
    parser.add_argument(
        "alembic_args",
        nargs="*",
        default=["upgrade", "head"],
        help="Arguments to pass to alembic (default: upgrade head)",
    )
    
    args = parser.parse_args()
    
    # First, run migrations on public schema (no ALEMBIC_SCHEMA set)
    print("\n" + "="*60)
    print("Migrating public schema...")
    print("="*60)
    result = subprocess.run(
        ["alembic"] + args.alembic_args,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )
    if result.returncode != 0:
        print("ERROR: Public schema migration failed")
        sys.exit(1)
    print("SUCCESS: Public schema migrated")
    
    if args.public_only:
        print("\n--public-only specified, skipping tenant schemas")
        sys.exit(0)
    
    # Determine tenant list
    if args.tenants:
        tenants = [t.strip() for t in args.tenants.split(",")]
    else:
        tenants = DEFAULT_TENANTS
    
    schema_prefix = multitenancy_settings.schema_prefix or ""
    
    # Migrate each tenant schema
    failed = []
    for tenant_id in tenants:
        schema_name = f"{schema_prefix}{tenant_id}"
        if not migrate_schema(schema_name, args.alembic_args):
            failed.append(schema_name)
    
    # Summary
    print("\n" + "="*60)
    print("MIGRATION SUMMARY")
    print("="*60)
    print(f"Total tenant schemas: {len(tenants)}")
    print(f"Successful: {len(tenants) - len(failed)}")
    print(f"Failed: {len(failed)}")
    if failed:
        print(f"Failed schemas: {', '.join(failed)}")
        sys.exit(1)
    
    print("\nAll migrations completed successfully!")


if __name__ == "__main__":
    main()

