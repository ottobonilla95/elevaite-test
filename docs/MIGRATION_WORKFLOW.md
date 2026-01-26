# Database Migration Workflow

This document explains the end-to-end workflow for database migrations from development to production.

## Overview: Migrations are Idempotent ✅

**Key Point**: Alembic migrations only run if needed. Running migrations multiple times is safe and fast.

- **First run**: Creates tables, applies changes (~5-30 seconds)
- **Subsequent runs**: Checks version, does nothing (~1 second)

Alembic stores the current migration version in the `alembic_version` table and only applies new migrations.

## New Developer Onboarding

### Day 1: Clone and Run

```bash
# 1. Clone the repo
git clone git@github.com:iopexses/elevaite.git
cd elevaite

# 2. Install dependencies
npm install

# 3. Copy environment file
cp .env.example .env
# Edit .env with your API keys

# 4. Start everything (migrations run automatically)
npm run dev
```

**What happens automatically:**
1. ✅ PostgreSQL starts (empty database)
2. ✅ Migrations create all schemas and tables
3. ✅ Services start and work immediately

**No manual migration steps required!** The `npm run dev` command handles everything.

### Day 2+: Normal Development

```bash
# Just start dev server
npm run dev

# Output:
# 🗄️  Running database migrations...
#   ✓ auth_default already up-to-date
#   ✓ workflow_default already up-to-date
#   ✓ ingestion-service already up-to-date
# 🔧 Starting backend services...
```

Fast startup because migrations are already applied.

## Developer Workflow: Making Schema Changes

### Step 1: Make Your Code Changes

```bash
# Example: Add a new field to User model
# Edit: python_apps/auth_api/app/db/models.py
```

```python
class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    avatar_url: Optional[str] = None  # ← New field
    # ... other fields
```

### Step 2: Generate Migration

```bash
cd python_apps/auth_api
uv run alembic revision --autogenerate -m "add_user_avatar"
```

Alembic generates a migration file:
```
migrations/versions/abc123def456_add_user_avatar.py
```

### Step 3: Review the Generated Migration

**IMPORTANT**: Always review auto-generated migrations!

```python
def upgrade() -> None:
    # Auto-generated code
    op.add_column('user', sa.Column('avatar_url', sa.String(), nullable=True))


def downgrade() -> None:
    # Auto-generated code
    op.drop_column('user', 'avatar_url')
```

Check:
- ✅ Column types are correct
- ✅ Nullable/default values are appropriate
- ✅ Downgrade function properly reverses the change

### Step 4: Test Locally

```bash
# Run the new migration
npm run migrate

# Or restart dev (auto-runs migrations)
npm run dev

# Test your feature with the new schema
```

### Step 5: Commit and Push

```bash
git add python_apps/auth_api/migrations/versions/abc123def456_add_user_avatar.py
git add python_apps/auth_api/app/db/models.py
git commit -m "feat: add user avatar support"
git push origin feature/user-avatars
```

### Step 6: Create Pull Request

**What happens automatically in CI:**
1. ✅ Migration syntax validated (`alembic check`)
2. ✅ Checks for duplicate revision IDs
3. ✅ Linting and tests run
4. ✅ PR must pass before merge allowed

### Step 7: Merge to Develop → Auto-Deploy to Staging

```bash
# Teammate approves and merges PR
git checkout develop
git pull
```

**What happens automatically in staging deployment:**

```yaml
Helm Deploy to Staging:
  1. Build Docker images (includes new migration file)
  2. Push images to registry
  3. ↓
  4. Helm pre-upgrade hook runs (migrations-job.yaml)
  5. ├─ Wait for PostgreSQL
  6. ├─ Run auth-api migrations (all tenants)
  7. │  ✓ auth_default: Running upgrade abc123def456 -> new_migration
  8. │  ✓ auth_toshiba: Running upgrade abc123def456 -> new_migration
  9. │  ✓ auth_iopex: Running upgrade abc123def456 -> new_migration
  10. ├─ Run workflow-engine migrations (no changes)
  11. └─ Run ingestion-service migrations (no changes)
  12. ↓
  13. Deploy new pods (migrations succeeded)
  14. ✅ Staging deployment complete
```

**If migrations fail:**
- ❌ Deployment is blocked
- 🔄 Old version keeps running
- 👀 Team is notified to fix the issue

### Step 8: Deploy to Production

```bash
# Merge develop to main
git checkout main
git merge develop
git push
```

**Same automatic process runs for production** (but with production database).

## Full Environment Flow

```
┌─────────────────────────────────────────────────────────────┐
│ LOCAL DEVELOPMENT                                            │
├─────────────────────────────────────────────────────────────┤
│ 1. Developer: npm run dev                                    │
│    ├─ PostgreSQL starts                                      │
│    ├─ Migrations auto-run (if needed)                        │
│    └─ Services start                                         │
│                                                               │
│ 2. Developer makes schema changes                            │
│ 3. Developer: alembic revision --autogenerate                │
│ 4. Developer: npm run migrate (test locally)                 │
│ 5. Developer: git commit + push                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ CI PIPELINE (GitHub Actions)                                 │
├─────────────────────────────────────────────────────────────┤
│ ✅ Validate migration syntax                                 │
│ ✅ Check for conflicts                                       │
│ ✅ Run tests                                                 │
│ ✅ Build Docker images                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGING DEPLOYMENT (Automatic on merge to develop)          │
├─────────────────────────────────────────────────────────────┤
│ 1. Helm starts deployment                                    │
│ 2. Migrations Job runs (pre-upgrade hook)                    │
│    ├─ Connects to staging database                           │
│    ├─ Runs migrations for all services/tenants               │
│    └─ Succeeds or blocks deployment                          │
│ 3. If migrations succeed:                                     │
│    ├─ Deploy new pods                                         │
│    ├─ Wait for rollout                                        │
│    └─ Run smoke tests                                         │
│ 4. Notify team (Slack/etc)                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PRODUCTION DEPLOYMENT (Automatic on merge to main)          │
├─────────────────────────────────────────────────────────────┤
│ Same as staging, but:                                        │
│ ├─ Uses production database                                  │
│ ├─ More tenants (default, toshiba, iopex, customer1, ...)   │
│ ├─ Stricter rollback policy                                  │
│ └─ More extensive smoke tests                                │
└─────────────────────────────────────────────────────────────┘
```

## What Happens to Other Developers?

### Scenario: Alice adds a migration, Bob pulls latest code

**Alice's workflow:**
```bash
# Alice adds user_avatar field
alembic revision --autogenerate -m "add_user_avatar"
git commit + push
# PR merged to develop
```

**Bob's workflow (next day):**
```bash
# Bob pulls latest code
git checkout develop
git pull

# Bob starts dev server
npm run dev

# Output:
# 🗄️  Running database migrations...
#   ✓ Applied new migrations to auth_default (add_user_avatar)
#   ✓ workflow_default already up-to-date
# 🔧 Starting backend services...
```

**Bob's database is automatically updated!** No manual steps required.

## Common Scenarios

### Scenario 1: Fresh Start (New Dev)

```bash
npm run dev
# Creates all tables from scratch using all migration files
```

### Scenario 2: Daily Development (Existing Dev)

```bash
npm run dev
# Checks version, sees no new migrations, starts immediately
```

### Scenario 3: After Pulling New Migration

```bash
git pull
npm run dev
# Applies new migration, then starts services
```

### Scenario 4: Multiple Migrations in Same PR

```bash
# Create multiple migrations
alembic revision --autogenerate -m "add_user_avatar"
alembic revision --autogenerate -m "add_user_preferences"

# Test locally
npm run migrate
# Both migrations apply in order

# Push both files
git add migrations/versions/*.py
git commit -m "feat: user profile enhancements"
```

### Scenario 5: Migration Conflict (Two Devs)

**Problem:**
- Alice creates migration `abc123_add_avatar.py` (parent: `xyz789`)
- Bob creates migration `def456_add_preferences.py` (parent: `xyz789`)
- Both have same parent!

**Solution:**
- CI detects conflict (duplicate down_revision)
- One developer rebases and regenerates their migration:

```bash
git checkout develop
git pull  # Get Alice's migration
cd python_apps/auth_api
rm migrations/versions/def456_add_preferences.py  # Delete old
alembic revision --autogenerate -m "add_user_preferences"  # Regenerate (now parent is abc123)
```

## Database State in Each Environment

| Environment | When Migrations Run | Who Runs Them |
|-------------|---------------------|---------------|
| **Local** | On `npm run dev` | Your machine (via script) |
| **Preview** | On PR deploy (optional) | GitHub Actions → Kubernetes Job |
| **Staging** | On merge to `develop` | GitHub Actions → Kubernetes Job |
| **Production** | On merge to `main` | GitHub Actions → Kubernetes Job |

All environments stay in sync because:
1. Migration files are in git
2. Each environment runs migrations automatically
3. Alembic ensures correct order and idempotency

## Best Practices

### ✅ Do This

1. **Always review auto-generated migrations**
   ```bash
   alembic revision --autogenerate -m "description"
   # Then open and review the generated file
   ```

2. **Test migrations locally before pushing**
   ```bash
   npm run migrate
   # Test your feature
   # Check database state
   ```

3. **Write descriptive migration messages**
   ```bash
   # Good
   alembic revision -m "add_user_avatar_and_bio_fields"

   # Bad
   alembic revision -m "update"
   ```

4. **Commit migration files with related code changes**
   ```bash
   git add python_apps/auth_api/migrations/versions/abc123_*.py
   git add python_apps/auth_api/app/db/models.py
   git commit -m "feat: add user profile fields"
   ```

5. **Check migration status regularly**
   ```bash
   npm run migrate:status
   ```

### ❌ Don't Do This

1. **Don't modify existing migration files**
   - Create a new migration instead
   - Old migrations may have already run in staging/prod

2. **Don't skip testing migrations locally**
   - Broken migrations block deployments
   - Test before pushing

3. **Don't commit database data or .env files**
   - Only commit migration files
   - Never commit credentials

4. **Don't manually CREATE/ALTER tables**
   - Always use migrations
   - Manual changes will be lost or cause conflicts

## Troubleshooting

### Problem: Migration fails locally

```bash
# View error
npm run migrate

# Check current state
npm run migrate:status

# Reset database (development only!)
npm run dev:death
npm run dev
```

### Problem: Migration conflict after git pull

```bash
# Check status
cd python_apps/auth_api
uv run alembic history

# If conflicts, regenerate your migration
rm migrations/versions/your_migration.py
alembic revision --autogenerate -m "your_description"
```

### Problem: Need to rollback a migration

```bash
cd python_apps/auth_api

# Rollback one migration
ALEMBIC_SCHEMA=auth_default uv run alembic downgrade -1

# Or create a new "reverting" migration
alembic revision -m "revert_problematic_change"
# Manually write the reverse operations
```

### Problem: Staging deployment failed due to migration

1. Check Kubernetes migration Job logs:
   ```bash
   kubectl logs job/elevaite-migrations -n staging
   ```

2. Fix the migration locally
3. Push fix to develop
4. Re-deploy automatically

## FAQ

**Q: Do migrations run every time I start `npm run dev`?**
A: Migrations *check* every time (fast), but only *apply* if there are new migrations.

**Q: What if I forget to run migrations?**
A: Services will fail to start because tables don't exist. Just run `npm run migrate`.

**Q: Can I skip migrations to start faster?**
A: Yes! Use `npm run dev:skip-migrations` if you know you're up-to-date.

**Q: What happens if my migration breaks staging?**
A: Deployment is blocked, old version keeps running. Fix and redeploy.

**Q: How do I see what migrations are pending?**
A: Run `npm run migrate:status`

**Q: Do I need to manually run migrations in production?**
A: No! They run automatically via Helm pre-upgrade hook.

**Q: What if two developers create migrations at the same time?**
A: CI will detect the conflict. One dev rebases and regenerates their migration.

**Q: Can I test a migration without actually running it?**
A: Yes! Use `alembic upgrade --sql` to see the SQL without executing.

**Q: How do I create a data migration (not schema)?**
A: Create an empty revision: `alembic revision -m "migrate_user_data"` and write custom Python code.

## Summary

The migration system is designed to be **automatic and invisible** for day-to-day work:

- ✅ New devs: `npm run dev` just works
- ✅ Daily development: `npm run dev` is fast (migrations skip if up-to-date)
- ✅ Making changes: `alembic revision --autogenerate` + commit
- ✅ Deployments: Fully automatic via Helm hooks
- ✅ Team sync: Everyone gets migrations automatically on `git pull` + `npm run dev`

**You rarely need to think about migrations** - the system handles it!
