# Docker Deployment - Quick Reference Card

Cheat sheet for common Docker Compose operations.

---

## 🚀 Initial Deployment

```bash
# 1. Copy environment template
cp .env.production.template .env.production

# 2. Generate secrets
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
python3 -c "import secrets; print('API_KEY_SECRET=' + secrets.token_urlsafe(32))"

# 3. Edit .env.production with your values
nano .env.production

# 4. Start everything
docker compose -f docker-compose.prod.yaml --env-file .env.production up -d

# 5. Check status
docker compose -f docker-compose.prod.yaml ps

# 6. View logs
docker compose -f docker-compose.prod.yaml logs -f
```

---

## 📊 Monitoring

```bash
# Check all containers
docker compose -f docker-compose.prod.yaml ps

# View logs (all services)
docker compose -f docker-compose.prod.yaml logs -f

# View logs (specific service)
docker compose -f docker-compose.prod.yaml logs -f auth_api
docker compose -f docker-compose.prod.yaml logs -f opa
docker compose -f docker-compose.prod.yaml logs -f db

# Last 100 lines
docker compose -f docker-compose.prod.yaml logs --tail=100

# Resource usage
docker stats

# Disk usage
docker system df
```

---

## 🏥 Health Checks

```bash
# Auth API health
curl http://localhost:8004/api/health

# Authorization health (includes OPA check)
curl http://localhost:8004/api/authz/health

# OPA health (internal)
docker compose -f docker-compose.prod.yaml exec opa wget -O- http://localhost:8181/health

# Database health
docker compose -f docker-compose.prod.yaml exec db pg_isready -U auth_user
```

---

## 🔄 Updates & Restarts

```bash
# Pull latest code
git pull origin main

# Rebuild and restart (with new code)
docker compose -f docker-compose.prod.yaml --env-file .env.production up -d --build

# Restart all services (no rebuild)
docker compose -f docker-compose.prod.yaml restart

# Restart specific service
docker compose -f docker-compose.prod.yaml restart auth_api

# Stop all services
docker compose -f docker-compose.prod.yaml stop

# Start all services
docker compose -f docker-compose.prod.yaml start
```

---

## 🗄️ Database Operations

```bash
# Connect to database
docker compose -f docker-compose.prod.yaml exec db psql -U auth_user -d auth_db

# Run migrations
docker compose -f docker-compose.prod.yaml run --rm migration alembic upgrade head

# Backup database
docker compose -f docker-compose.prod.yaml exec -T db \
  pg_dump -U auth_user auth_db | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Restore database
gunzip < backup_20250115_120000.sql.gz | \
  docker compose -f docker-compose.prod.yaml exec -T db \
  psql -U auth_user -d auth_db

# View database size
docker compose -f docker-compose.prod.yaml exec db \
  psql -U auth_user -d auth_db -c "SELECT pg_size_pretty(pg_database_size('auth_db'));"
```

---

## 🐛 Debugging

```bash
# Shell into Auth API container
docker compose -f docker-compose.prod.yaml exec auth_api bash

# Shell into database
docker compose -f docker-compose.prod.yaml exec db bash

# Shell into OPA
docker compose -f docker-compose.prod.yaml exec opa sh

# Check environment variables
docker compose -f docker-compose.prod.yaml exec auth_api env

# Test OPA policy directly
docker compose -f docker-compose.prod.yaml exec opa \
  opa eval -d /policies/rbac.rego 'data.rbac.allow' \
  -i <(echo '{"user":{"status":"active","assignments":[]},"action":"view","resource":{}}')
```

---

## 🧹 Cleanup

```bash
# Stop and remove containers (keeps data)
docker compose -f docker-compose.prod.yaml down

# Stop and remove containers + volumes (⚠️ DELETES DATA!)
docker compose -f docker-compose.prod.yaml down -v

# Remove unused images
docker image prune -a

# Remove all unused resources
docker system prune -a --volumes
```

---

## 🔐 Security

```bash
# Check .env.production permissions
ls -la .env.production
# Should be: -rw------- (600)

# Fix permissions if needed
chmod 600 .env.production
chown root:root .env.production

# View secrets (be careful!)
cat .env.production

# Rotate secrets
# 1. Generate new secrets
# 2. Update .env.production
# 3. Restart: docker compose restart auth_api
```

---

## 📈 Scaling

```bash
# Scale Auth API to 3 instances
docker compose -f docker-compose.prod.yaml up -d --scale auth_api=3

# Check scaled instances
docker compose -f docker-compose.prod.yaml ps auth_api

# Scale back to 1
docker compose -f docker-compose.prod.yaml up -d --scale auth_api=1
```

**Note:** For proper load balancing with multiple instances, you need a reverse proxy (Nginx/Traefik).

---

## 🔍 Troubleshooting

### Auth API won't start

```bash
# Check logs
docker compose -f docker-compose.prod.yaml logs auth_api

# Check if database is ready
docker compose -f docker-compose.prod.yaml ps db

# Check if OPA is ready
docker compose -f docker-compose.prod.yaml ps opa

# Restart Auth API
docker compose -f docker-compose.prod.yaml restart auth_api
```

### OPA not healthy

```bash
# Check OPA logs
docker compose -f docker-compose.prod.yaml logs opa

# Verify policy file
docker compose -f docker-compose.prod.yaml exec opa ls -la /policies/

# Test OPA health
docker compose -f docker-compose.prod.yaml exec opa wget -O- http://localhost:8181/health
```

### Database connection errors

```bash
# Check database is running
docker compose -f docker-compose.prod.yaml ps db

# Check database logs
docker compose -f docker-compose.prod.yaml logs db

# Test connection
docker compose -f docker-compose.prod.yaml exec db \
  psql -U auth_user -d auth_db -c "SELECT 1;"
```

### Migration failed

```bash
# Check migration logs
docker compose -f docker-compose.prod.yaml logs migration

# Run migration manually
docker compose -f docker-compose.prod.yaml run --rm migration alembic upgrade head

# Check current migration version
docker compose -f docker-compose.prod.yaml run --rm migration alembic current
```

---

## 📝 Common Tasks

### View API Documentation

```bash
# Open in browser
# http://your-server:8004/auth-api/docs
```

### Create Superuser

```bash
# Connect to database
docker compose -f docker-compose.prod.yaml exec db psql -U auth_user -d auth_db

# Run SQL
UPDATE users SET is_superuser = true WHERE email = 'admin@example.com';
```

### Check Active Sessions

```bash
docker compose -f docker-compose.prod.yaml exec db \
  psql -U auth_user -d auth_db -c \
  "SELECT COUNT(*) FROM sessions WHERE is_active = true;"
```

### View Recent User Activity

```bash
docker compose -f docker-compose.prod.yaml exec db \
  psql -U auth_user -d auth_db -c \
  "SELECT * FROM user_activity ORDER BY timestamp DESC LIMIT 10;"
```

---

## 🎯 Environment Variables Quick Reference

```bash
# Required
DB_PASSWORD=<strong-password>
SECRET_KEY=<random-key>
API_KEY_SECRET=<random-key>
SMTP_USER=<email>
SMTP_PASSWORD=<password>
FRONTEND_URL=<url>

# Optional (with defaults)
DB_USER=auth_user
DB_NAME=auth_db
AUTH_API_PORT=8004
ACCESS_TOKEN_EXPIRE_MINUTES=90
REFRESH_TOKEN_EXPIRE_MINUTES=10080
CORS_ORIGINS=*
LOG_LEVEL=INFO
```

---

## 🆘 Emergency Commands

### Service is down - Quick restart

```bash
docker compose -f docker-compose.prod.yaml restart
```

### Database is corrupted - Restore from backup

```bash
# Stop services
docker compose -f docker-compose.prod.yaml stop

# Restore database
gunzip < backup_latest.sql.gz | \
  docker compose -f docker-compose.prod.yaml exec -T db \
  psql -U auth_user -d auth_db

# Start services
docker compose -f docker-compose.prod.yaml start
```

### Out of disk space - Clean up

```bash
# Remove old images
docker image prune -a -f

# Remove old containers
docker container prune -f

# Remove old volumes (⚠️ careful!)
docker volume prune -f
```

### Complete reset (⚠️ NUCLEAR OPTION - DELETES EVERYTHING!)

```bash
docker compose -f docker-compose.prod.yaml down -v
docker system prune -a -f --volumes
# Then redeploy from scratch
```

---

## 📞 Support Checklist

When asking for help, provide:

```bash
# 1. Container status
docker compose -f docker-compose.prod.yaml ps

# 2. Recent logs
docker compose -f docker-compose.prod.yaml logs --tail=100

# 3. Health check results
curl http://localhost:8004/api/health
curl http://localhost:8004/api/authz/health

# 4. Resource usage
docker stats --no-stream

# 5. Docker version
docker --version
docker compose version
```

---

## 🎓 Aliases (Optional)

Add to `~/.bashrc` or `~/.zshrc`:

```bash
alias dc='docker compose -f docker-compose.prod.yaml --env-file .env.production'
alias dcup='dc up -d'
alias dcdown='dc down'
alias dclogs='dc logs -f'
alias dcps='dc ps'
alias dcrestart='dc restart'
```

Then you can use:
```bash
dcup        # Instead of: docker compose -f docker-compose.prod.yaml --env-file .env.production up -d
dclogs      # Instead of: docker compose -f docker-compose.prod.yaml --env-file .env.production logs -f
dcps        # Instead of: docker compose -f docker-compose.prod.yaml --env-file .env.production ps
```

---

**Keep this file handy for quick reference!** 📌

