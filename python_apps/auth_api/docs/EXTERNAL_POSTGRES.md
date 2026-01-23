# Using External PostgreSQL with Auth API

This guide covers using a shared PostgreSQL instance instead of running PostgreSQL in Docker Compose.

---

## 🎯 Why Use External PostgreSQL?

**Good reasons:**
- ✅ Share one PostgreSQL instance across multiple services
- ✅ Easier to manage backups centrally
- ✅ Lower resource usage (one DB instead of many)
- ✅ Simpler for dev/staging environments
- ✅ Managed PostgreSQL services (RDS, Cloud SQL, etc.)

**When it makes sense:**
- Dev/staging environments
- Low to medium traffic
- Multiple services sharing one database server
- Using managed database services

---

## 📋 Setup Options

### Option 1: Shared PostgreSQL Server (Recommended for You)

You have one PostgreSQL instance running, and multiple services connect to it.

```
┌─────────────────────────────────────────┐
│         PostgreSQL Server               │
│         (Single Instance)               │
│                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────┐ │
│  │ auth_db  │  │ app_db   │  │ ...  │ │
│  └──────────┘  └──────────┘  └──────┘ │
└─────────────────────────────────────────┘
         ▲              ▲
         │              │
    ┌────┴────┐    ┌────┴────┐
    │ Auth    │    │ Other   │
    │ API     │    │ Service │
    └─────────┘    └─────────┘
```

### Option 2: Managed Database Service

Using AWS RDS, Google Cloud SQL, Azure Database, etc.

```
┌─────────────────────────────────────────┐
│      AWS RDS / Cloud SQL / Azure        │
│      (Managed PostgreSQL)               │
│                                         │
│  - Automatic backups                    │
│  - High availability                    │
│  - Monitoring included                  │
└─────────────────────────────────────────┘
         ▲
         │
    ┌────┴────┐
    │ Auth    │
    │ API     │
    └─────────┘
```

---

## 🚀 Quick Start

### Step 1: Prepare Your PostgreSQL Instance

#### Create Database and User

```sql
-- Connect to your PostgreSQL server
psql -h your-postgres-host -U postgres

-- Create database for Auth API
CREATE DATABASE auth_db;

-- Create user for Auth API
CREATE USER auth_user WITH PASSWORD 'strong_password_here';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE auth_db TO auth_user;

-- Connect to the new database
\c auth_db

-- Grant schema privileges (PostgreSQL 15+)
GRANT ALL ON SCHEMA public TO auth_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO auth_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO auth_user;

-- Enable UUID extension (required for RBAC tables)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

#### Verify Connection

```bash
# Test connection from your server
psql -h your-postgres-host -U auth_user -d auth_db -c "SELECT 1;"

# Should return:
#  ?column?
# ----------
#         1
```

### Step 2: Configure Auth API

#### Update .env.production

```bash
# Copy template
cp .env.production.template .env.production

# Edit the database URL
nano .env.production
```

**Set the database URL:**
```bash
# Format: postgresql://username:password@host:port/database
SQLALCHEMY_DATABASE_URL=postgresql://auth_user:strong_password@your-postgres-host:5432/auth_db

# Examples:
# Local PostgreSQL: postgresql://auth_user:pass@localhost:5432/auth_db
# Remote server: postgresql://auth_user:pass@192.168.1.100:5432/auth_db
# AWS RDS: postgresql://auth_user:pass@mydb.abc123.us-west-1.rds.amazonaws.com:5432/auth_db
# Cloud SQL: postgresql://auth_user:pass@10.1.2.3:5432/auth_db
```

### Step 3: Deploy Auth API

```bash
cd python_apps/auth_api

# Start Auth API + OPA (no PostgreSQL container)
docker compose -f docker-compose.prod.yaml --env-file .env.production up -d

# Check logs
docker compose -f docker-compose.prod.yaml logs -f

# Verify it's working
curl http://localhost:8004/api/health
```

**That's it!** Auth API will connect to your external PostgreSQL instance.

---

## 🔧 Development Setup

For development, you have two options:

### Option A: Use External PostgreSQL (Shared)

```bash
# Set environment variable
export SQLALCHEMY_DATABASE_URL=postgresql://auth_user:pass@your-dev-postgres:5432/auth_db

# Start Auth API + OPA only (no DB container)
docker compose -f docker-compose.dev.yaml up -d auth_api opa
```

### Option B: Use Included PostgreSQL (Isolated)

```bash
# Start with included PostgreSQL
docker compose -f docker-compose.dev.yaml --profile with-db up -d

# This starts: Auth API + OPA + PostgreSQL
```

---

## 🗄️ Database Schema

Auth API creates these tables in your PostgreSQL database:

### Existing Auth Tables (from before)
- `users` - User accounts
- `sessions` - Active sessions
- `user_activity` - Activity logs
- `mfa_verifications` - MFA codes
- `device_fingerprints` - Trusted devices

### New RBAC Tables (added by migration)
- `organizations` - Top-level hierarchy
- `accounts` - Belong to organizations
- `projects` - Belong to accounts
- `user_role_assignments` - User roles on resources

**Total:** ~9 tables, all prefixed with nothing (no schema prefix)

---

## 🔒 Security Considerations

### 1. Network Access

**Ensure Auth API can reach PostgreSQL:**

```bash
# Test from Auth API container
docker compose -f docker-compose.prod.yaml exec auth_api \
  psql -h your-postgres-host -U auth_user -d auth_db -c "SELECT 1;"
```

**Firewall rules:**
- Allow Auth API server IP to connect to PostgreSQL port 5432
- Block public internet access to PostgreSQL

### 2. Connection Pooling

Auth API uses SQLAlchemy with connection pooling (already configured):

```python
# Default pool settings (in Auth API code)
pool_size=5          # 5 connections per worker
max_overflow=10      # Up to 15 total connections
pool_timeout=30      # Wait 30s for connection
pool_recycle=3600    # Recycle connections after 1 hour
```

**For 4 workers:** ~20 connections max

### 3. SSL/TLS Connections

For production, use SSL:

```bash
# .env.production
SQLALCHEMY_DATABASE_URL=postgresql://auth_user:pass@host:5432/auth_db?sslmode=require

# SSL modes:
# - disable: No SSL (dev only!)
# - require: SSL required
# - verify-ca: Verify certificate authority
# - verify-full: Verify CA and hostname
```

### 4. Password Security

**Don't hardcode passwords!**

```bash
# Bad ❌
SQLALCHEMY_DATABASE_URL=postgresql://auth_user:password123@host:5432/auth_db

# Good ✅ - Use environment variable
SQLALCHEMY_DATABASE_URL=${DATABASE_URL}

# Or use secrets management
SQLALCHEMY_DATABASE_URL=$(cat /run/secrets/database_url)
```

---

## 📊 Monitoring

### Check Active Connections

```sql
-- Connect to PostgreSQL
psql -h your-postgres-host -U postgres

-- View connections to auth_db
SELECT 
    datname,
    usename,
    application_name,
    client_addr,
    state,
    COUNT(*)
FROM pg_stat_activity
WHERE datname = 'auth_db'
GROUP BY datname, usename, application_name, client_addr, state;
```

### Check Database Size

```sql
SELECT 
    pg_size_pretty(pg_database_size('auth_db')) as size;
```

### Check Table Sizes

```sql
\c auth_db

SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## 🔄 Migrations

Migrations run automatically on startup via the `migration` service.

### Manual Migration

```bash
# Run migration manually
docker compose -f docker-compose.prod.yaml run --rm migration alembic upgrade head

# Check current version
docker compose -f docker-compose.prod.yaml run --rm migration alembic current

# View migration history
docker compose -f docker-compose.prod.yaml run --rm migration alembic history
```

### Rollback Migration

```bash
# Rollback one version
docker compose -f docker-compose.prod.yaml run --rm migration alembic downgrade -1

# Rollback to specific version
docker compose -f docker-compose.prod.yaml run --rm migration alembic downgrade <revision>
```

---

## 🐛 Troubleshooting

### Connection Refused

```bash
# Check PostgreSQL is running
psql -h your-postgres-host -U postgres -c "SELECT 1;"

# Check firewall allows connection
telnet your-postgres-host 5432

# Check Auth API can resolve hostname
docker compose -f docker-compose.prod.yaml exec auth_api ping your-postgres-host
```

### Authentication Failed

```bash
# Verify credentials
psql -h your-postgres-host -U auth_user -d auth_db

# Check pg_hba.conf allows connection
# On PostgreSQL server:
cat /etc/postgresql/*/main/pg_hba.conf
```

### Permission Denied

```sql
-- Grant all privileges
\c auth_db
GRANT ALL ON SCHEMA public TO auth_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO auth_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO auth_user;
```

### Too Many Connections

```sql
-- Check max connections
SHOW max_connections;

-- Check current connections
SELECT COUNT(*) FROM pg_stat_activity;

-- Increase max_connections (postgresql.conf)
max_connections = 100
```

---

## 📈 Performance Tips

### 1. Connection Pooling

Already configured in Auth API. No action needed!

### 2. Indexes

Migrations create indexes automatically:
- `users.email` (unique)
- `user_role_assignments.user_id`
- `user_role_assignments.resource_id`
- `organizations.name` (unique)

### 3. Vacuum

```sql
-- Analyze tables for query optimization
ANALYZE;

-- Vacuum to reclaim space
VACUUM;

-- Full vacuum (requires downtime)
VACUUM FULL;
```

### 4. Monitoring Slow Queries

```sql
-- Enable slow query logging (postgresql.conf)
log_min_duration_statement = 1000  # Log queries > 1 second

-- View slow queries
SELECT 
    query,
    calls,
    total_time,
    mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

---

## 🎯 Summary

**What you need:**
1. ✅ PostgreSQL instance (existing or new)
2. ✅ Create `auth_db` database
3. ✅ Create `auth_user` user with permissions
4. ✅ Set `SQLALCHEMY_DATABASE_URL` in `.env.production`
5. ✅ Deploy Auth API (it connects to external DB)

**What you DON'T need:**
- ❌ PostgreSQL in Docker Compose
- ❌ Separate database per service (can share one PostgreSQL)
- ❌ Complex networking setup

**Architecture:**
```
Your PostgreSQL Server
├── auth_db (Auth API)
├── app_db (Your App)
├── workflow_db (Workflow Engine)
└── ... (other services)

Auth API Container
├── Connects to: your-postgres-host:5432/auth_db
└── No PostgreSQL container needed!
```

Simple and clean! 🚀

