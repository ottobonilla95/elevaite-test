"""
Tenant Seed Data Initializer

Seeds new tenant databases with demo data after migrations.
"""

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlmodel import Session

from db_core import register_tenant_initializer
from db_core.utils import get_schema_name
from workflow_core_sdk.multitenancy import multitenancy_settings
from workflow_core_sdk.db.database import engine

from .loader import SeedDataLoader

logger = logging.getLogger(__name__)


def _seed_tenant_sync(schema_name: str) -> dict[str, int]:
    """Load seed data synchronously with the tenant's schema in search_path."""
    with Session(engine) as session:
        session.execute(text(f'SET search_path TO "{schema_name}", public'))
        session.commit()
        return SeedDataLoader(session).load_all()


@register_tenant_initializer
async def seed_tenant_data(tenant_id: str, session: AsyncSession) -> None:
    """
    Seed a new tenant's database with demo data.

    Runs after migrations and populates the schema with demo prompts, tools,
    agents, and workflows. Seeding failures are logged but don't block tenant creation.
    """
    schema_name = get_schema_name(tenant_id, multitenancy_settings)
    logger.info(f"Seeding demo data for tenant '{tenant_id}' in schema '{schema_name}'")

    try:
        results = await asyncio.to_thread(_seed_tenant_sync, schema_name)
        total = sum(results.values())
        logger.info(
            f"Seeding completed for tenant '{tenant_id}': {total} entities created ({results})"
        )
    except Exception as e:
        logger.error(f"Failed to seed data for tenant '{tenant_id}': {e}")
