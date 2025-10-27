# Docker Production Deployment Guide

This guide covers deploying Auth API with OPA using Docker Compose (no Kubernetes required).

---

## 🎯 What You're Deploying

**2 containers in one Docker Compose stack:**

1. **OPA** - Authorization policy engine
2. **Auth API** - Your application (talks to OPA and external PostgreSQL)

**Plus a one-time migration container** that runs database migrations on startup.

**Note:** This setup uses an **external PostgreSQL instance** (shared across services). If you need a dedicated PostgreSQL container, see the dev compose file.

---

## 📋 Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- A server/VM with at least 2GB RAM
- Domain name (optional, but recommended)

---

## 🚀 Quick Start

### Step 1: Prepare the Server

```bash
# SSH into your server
ssh user@your-server.com

# Install Docker (if not already installed)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

### Step 2: Clone Your Repository

```bash
# Clone your repo
git clone https://github.com/yourorg/elevaite.git
cd elevaite/python_apps/auth_api
```

### Step 3: Prepare PostgreSQL Database

**Create database and user in your shared PostgreSQL instance:**

```sql
-- Connect to your PostgreSQL server
psql -h your-postgres-host -U postgres

-- Create database
CREATE DATABASE auth_db;

-- Create user
CREATE USER auth_user WITH PASSWORD 'strong_password_here';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE auth_db TO auth_user;

-- Connect to the new database
\c auth_db

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO auth_user;

-- Enable UUID extension (required)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

**See `EXTERNAL_POSTGRES.md` for detailed PostgreSQL setup.**

### Step 4: Configure Environment Variables

```bash
# Copy the template
cp .env.production.template .env.production

# Edit with your values
nano .env.production
```

**Required values to change:**

```bash
# Database URL - Point to your shared PostgreSQL instance
SQLALCHEMY_DATABASE_URL=postgresql://auth_user:strong_password@your-postgres-host:5432/auth_db

# Security keys (generate random keys!)
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
API_KEY_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Email settings
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@yourcompany.com

# Frontend URL
FRONTEND_URL=https://yourapp.com

# CORS origins
CORS_ORIGINS=https://yourapp.com,https://admin.yourapp.com
```

**Generate secure keys:**

```bash
# Generate SECRET_KEY
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# Generate API_KEY_SECRET
python3 -c "import secrets; print('API_KEY_SECRET=' + secrets.token_urlsafe(32))"
```

### Step 5: Deploy!

```bash
# Start all services
docker compose -f docker-compose.prod.yaml --env-file .env.production up -d

# Check logs
docker compose -f docker-compose.prod.yaml logs -f

# Check status
docker compose -f docker-compose.prod.yaml ps
```

**Expected output:**

```
NAME                STATUS              PORTS
auth_api-auth_api   Up (healthy)        0.0.0.0:8004->8004/tcp
auth_api-db         Up (healthy)
auth_api-opa        Up (healthy)
auth_api-migration  Exited (0)
```

### Step 6: Verify It's Working

```bash
# Health check
curl http://localhost:8004/api/health

# Should return:
# {"status":"healthy"}

# Check authorization health (includes OPA check)
curl http://localhost:8004/api/authz/health

# Should return:
# {"status":"healthy","opa":"healthy","message":"Authorization service is operational"}
```

---

## 🔧 Configuration Details

### Docker Compose Architecture

```
┌─────────────────────────────────────────────────┐
│                  Docker Host                     │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐            │
│  │  Auth API    │  │     OPA      │            │
│  │  :8004       │──│   :8181      │            │
│  │              │  │              │            │
│  │ Talks to OPA │  │ Evaluates    │            │
│  │ via internal │  │ policies     │            │
│  │ network      │  │              │            │
│  └──────┬───────┘  └──────────────┘            │
│         │                                       │
│         │ Connects to external PostgreSQL      │
│         ▼                                       │
│  Only Auth API port 8004 is exposed to host    │
└─────────────────────────────────────────────────┘
         │
         │ Network connection
         ▼
┌─────────────────────────────────────────────────┐
│         External PostgreSQL Server               │
│         (Shared across services)                 │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ auth_db  │  │ app_db   │  │ other_db │     │
│  └──────────┘  └──────────┘  └──────────┘     │
└─────────────────────────────────────────────────┘
```

### Network Communication

**Internal (within Docker network):**

- Auth API → OPA: `http://opa:8181`

**External connections:**

- Auth API → PostgreSQL: `postgresql://your-postgres-host:5432/auth_db`
- Internet → Auth API: `http://your-server:8004`

**Why this is secure:**

- OPA is NOT exposed to the internet (only accessible within Docker network)
- Only Auth API port 8004 is exposed to the host
- PostgreSQL connection uses credentials from environment variables

---

## 🔒 Security Considerations

### 1. Use a Reverse Proxy (Recommended)

Don't expose port 8004 directly to the internet. Use Nginx or Traefik:

**Option A: Nginx**

```nginx
# /etc/nginx/sites-available/auth-api
server {
    listen 80;
    server_name auth.yourcompany.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name auth.yourcompany.com;

    # SSL certificates (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/auth.yourcompany.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/auth.yourcompany.com/privkey.pem;

    # Proxy to Auth API
    location / {
        proxy_pass http://localhost:8004;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Option B: Traefik (with Docker labels)**

Add to `docker-compose.prod.yaml`:

```yaml
services:
  auth_api:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.auth-api.rule=Host(`auth.yourcompany.com`)"
      - "traefik.http.routers.auth-api.entrypoints=websecure"
      - "traefik.http.routers.auth-api.tls.certresolver=letsencrypt"
```

### 2. Firewall Rules

```bash
# Only allow HTTP/HTTPS from internet
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp  # SSH

# Block direct access to Auth API port
sudo ufw deny 8004/tcp

# Enable firewall
sudo ufw enable
```

### 3. Environment File Permissions

```bash
# Restrict access to .env.production
chmod 600 .env.production
chown root:root .env.production
```

### 4. Database Backups

```bash
# Backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker compose -f docker-compose.prod.yaml exec -T db \
  pg_dump -U auth_user auth_db | gzip > backup_${DATE}.sql.gz

# Add to crontab for daily backups
0 2 * * * /path/to/backup-script.sh
```

---

## 📊 Monitoring & Logs

### View Logs

```bash
# All services
docker compose -f docker-compose.prod.yaml logs -f

# Just Auth API
docker compose -f docker-compose.prod.yaml logs -f auth_api

# Just OPA
docker compose -f docker-compose.prod.yaml logs -f opa

# Last 100 lines
docker compose -f docker-compose.prod.yaml logs --tail=100
```

### Health Checks

```bash
# Check all container health
docker compose -f docker-compose.prod.yaml ps

# Auth API health
curl http://localhost:8004/api/health

# Authorization health (includes OPA)
curl http://localhost:8004/api/authz/health
```

### Resource Usage

```bash
# See CPU/memory usage
docker stats

# See disk usage
docker system df
```

---

## 🔄 Updates & Maintenance

### Update to New Version

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker compose -f docker-compose.prod.yaml --env-file .env.production up -d --build

# Check logs
docker compose -f docker-compose.prod.yaml logs -f
```

### Run Database Migrations

Migrations run automatically on startup via the `migration` service. But if you need to run manually:

```bash
docker compose -f docker-compose.prod.yaml run --rm migration alembic upgrade head
```

### Restart Services

```bash
# Restart all
docker compose -f docker-compose.prod.yaml restart

# Restart just Auth API
docker compose -f docker-compose.prod.yaml restart auth_api
```

### Stop Services

```bash
# Stop (keeps data)
docker compose -f docker-compose.prod.yaml stop

# Stop and remove containers (keeps data)
docker compose -f docker-compose.prod.yaml down

# Stop and remove EVERYTHING including data (⚠️ DANGEROUS!)
docker compose -f docker-compose.prod.yaml down -v
```

---

## 🐛 Troubleshooting

### Auth API won't start

```bash
# Check logs
docker compose -f docker-compose.prod.yaml logs auth_api

# Common issues:
# 1. Missing environment variables
# 2. Database not ready
# 3. OPA not healthy
```

### OPA not healthy

```bash
# Check OPA logs
docker compose -f docker-compose.prod.yaml logs opa

# Verify policy file exists
ls -la policies/rbac.rego

# Test OPA directly
docker compose -f docker-compose.prod.yaml exec opa wget -O- http://localhost:8181/health
```

### Database connection errors

```bash
# Check database is running
docker compose -f docker-compose.prod.yaml ps db

# Check database logs
docker compose -f docker-compose.prod.yaml logs db

# Connect to database manually
docker compose -f docker-compose.prod.yaml exec db psql -U auth_user -d auth_db
```

### Migration failed

```bash
# Check migration logs
docker compose -f docker-compose.prod.yaml logs migration

# Run migration manually with verbose output
docker compose -f docker-compose.prod.yaml run --rm migration alembic upgrade head
```

---

## 📈 Scaling

### Vertical Scaling (More Resources)

Edit `docker-compose.prod.yaml`:

```yaml
services:
  auth_api:
    deploy:
      resources:
        limits:
          cpus: "4" # Increase CPU
          memory: 4G # Increase memory
```

### Horizontal Scaling (Multiple Instances)

For multiple Auth API instances, you'll need:

1. Load balancer (Nginx, HAProxy, Traefik)
2. Shared database (already done)
3. Session storage in database (already done)

```bash
# Scale to 3 instances
docker compose -f docker-compose.prod.yaml up -d --scale auth_api=3
```

**Note:** Each Auth API instance gets its own OPA sidecar automatically!

---

## 🎯 Production Checklist

Before going live:

- [ ] Changed all default passwords
- [ ] Generated secure SECRET_KEY and API_KEY_SECRET
- [ ] Configured SMTP for email
- [ ] Set correct FRONTEND_URL
- [ ] Set correct CORS_ORIGINS
- [ ] Set up reverse proxy (Nginx/Traefik)
- [ ] Configured SSL/TLS certificates
- [ ] Set up firewall rules
- [ ] Configured database backups
- [ ] Tested health endpoints
- [ ] Tested authorization (active/inactive users)
- [ ] Set up monitoring/alerting
- [ ] Documented rollback procedure

---

## 🆘 Support

If you run into issues:

1. Check logs: `docker compose logs -f`
2. Check health: `curl http://localhost:8004/api/authz/health`
3. Verify environment variables are set correctly
4. Check firewall/network settings

---

That's it! You now have a production-ready Auth API with authorization running on Docker! 🚀
