# Alembic DB Migrations for toshiba_data Scheme

The toshiba_data scheme is maintained by the Alembic migrations defined within this folder.

## Pointing to a Target database

You have two options.

Option 1: create a `toshiba_data_schema/.env` file.

* Use `.env-template` as an example and provide the connection url.

Option 2: provide database url on command line when calling alembic. For example:

```bash
ALEMBIC_SQLALCHEMY_URL="postgresql://USERNAME:PASSWORD@HOST.PATH:5432/toshiba_data" uv run alembic current
```

Note: if you're using port forwarding (see elevaite-infra/db/port-forward-db-aws.sh) then you'll want to use the appropriate localhost url, eg:

```bash
ALEMBIC_SQLALCHEMY_URL="postgresql://USERNAME:PASSWORD@localhost/toshiba_data" uv run alembic current
```

## Common commands

Prerequisite:

* Setup your local env via the following first:

```bash
cd elevaite/toshiba_apps/toshiba_backends/toshiba_data_schema
uv sync
```

The following commands don't require a DB connection:

```bash
# Get list of all available versions
uv run alembic history
```

The following commands require that you've provided a DB connection with valid credentials:

```bash
# Get current migration status of database
uv run alembic current

# Upgrade database to latest
uv run alembic upgrade head
```
