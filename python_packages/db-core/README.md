# DB-Core

A Python package for implementing database multitenancy in FastAPI applications
using SQLAlchemy and PostgreSQL.

## Features

- Multiple multitenancy strategies:
  - Schema-based: Each tenant gets its own PostgreSQL schema
  - Row-level: Shared schema with tenant discriminator column
- Automatic tenant identification from request headers
- Tenant-aware database sessions
- Tenant-aware models with automatic filtering
- Support for both synchronous and asynchronous database operations
- Configurable tenant validation and authorization

## Installation

```bash
# Using pip
pip install db-core

# Using uv (recommended)
uv pip install db-core
```

## Quick Start

```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import Column, String

# Import the db-core package
from db_core import (
    TenantMiddleware,
    get_tenant_db,
    init_db,
    TenantModelMixin,
    MultitenancySettings,
)
from db_core.db import Base
from db_core.config import TenantStrategy

# Create the FastAPI app
app = FastAPI()

# Define multitenancy settings
settings = MultitenancySettings(
    strategy=TenantStrategy.SCHEMA,  # or TenantStrategy.ROW_LEVEL
    tenant_id_header="X-Tenant-ID",
    db_url="postgresql://user:password@localhost/dbname",
)

# Initialize the database
init_db(settings=settings)

# Add tenant middleware to the app
app.add_middleware(TenantMiddleware, settings=settings)

# Define a tenant-aware model
class User(Base, TenantModelMixin):
    __tablename__ = "users"
    
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)

# Define an API endpoint with tenant database session
@app.get("/users/")
def list_users(db: Session = Depends(get_tenant_db)):
    return User.get_all(db)
```

## Multitenancy Strategies

### Schema-Based Multitenancy

With schema-based multitenancy, each tenant gets its own PostgreSQL schema,
providing strong data isolation.

```python
settings = MultitenancySettings(
    strategy=TenantStrategy.SCHEMA,
    tenant_id_header="X-Tenant-ID",
    db_url="postgresql://user:password@localhost/dbname",
    schema_prefix="tenant_",  # Each schema will be named tenant_{tenant_id}
)
```

### Row-Level Multitenancy

With row-level multitenancy, all tenants share the same schema, and a tenant
discriminator column is added to each table.

```python
settings = MultitenancySettings(
    strategy=TenantStrategy.ROW_LEVEL,
    tenant_id_header="X-Tenant-ID",
    db_url="postgresql://user:password@localhost/dbname",
    tenant_column_name="tenant_id",  # Name of the tenant column
)
```

## Tenant Identification

By default, the tenant ID is extracted from the `X-Tenant-ID` request header.
You can customize this by setting the `tenant_id_header` option:

```python
settings = MultitenancySettings(
    tenant_id_header="X-Tenant",
)
```

## Async Support

DB-Core supports both synchronous and asynchronous database operations:

```python
# Sync initialization
init_db(settings=settings)

# Async initialization
init_db(settings=settings, is_async=True)

# Sync dependency
@app.get("/users/")
def list_users(db: Session = Depends(get_tenant_db)):
    return User.get_all(db)

# Async dependency
@app.get("/users/")
async def list_users(db: AsyncSession = Depends(get_tenant_async_db)):
    result = await db.execute(select(User))
    return result.scalars().all()
```

## Model Methods

The `TenantModelMixin` provides several helper methods for working with
tenant-aware models:

```python
# Get all instances (automatically filtered by tenant)
users = User.get_all(db)

# Get an instance by ID (automatically filtered by tenant)
user = User.get_by_id(db, user_id)

# Save an instance (automatically sets tenant_id for row-level multitenancy)
user = User(name="John", email="john@example.com")
user.save(db)

# Delete an instance
user.delete(db)
```

## Development

```bash
# Clone the repository
git clone https://github.com/yourusername/db-core.git
cd db-core

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
uv pip install -e ".[dev]"

# Run tests
pytest
```

## License

MIT
