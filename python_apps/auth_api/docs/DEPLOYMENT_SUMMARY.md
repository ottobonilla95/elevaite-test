# Auth API Deployment - Summary

Quick overview of deployment options and what's included.

---

## 📦 What's Included

### Core Application
- **Auth API** - FastAPI application with authentication + authorization
- **OPA** - Open Policy Agent for policy evaluation
- **Database** - Uses external PostgreSQL (shared across services)

### Features
- ✅ Authentication (login, MFA, sessions, passwords)
- ✅ Authorization (RBAC with OPA policy evaluation)
- ✅ User status validation (security fix!)
- ✅ RBAC management (organizations, accounts, projects, roles)

---

## 🚀 Deployment Options

### Option 1: Docker Compose (Recommended for You)

**Best for:**
- Dev/staging/small production
- Shared PostgreSQL instance
- Simple deployment
- Low to medium traffic

**What you deploy:**
```
Docker Compose Stack:
├── Auth API container
└── OPA container

External (already running):
└── PostgreSQL server (shared)
```

**Files:**
- `docker-compose.prod.yaml` - Production setup
- `docker-compose.dev.yaml` - Development setup
- `.env.production.template` - Environment variables

**Deploy command:**
```bash
docker compose -f docker-compose.prod.yaml --env-file .env.production up -d
```

**Guides:**
- `DOCKER_DEPLOYMENT.md` - Full deployment guide
- `EXTERNAL_POSTGRES.md` - PostgreSQL setup
- `DOCKER_QUICK_REFERENCE.md` - Command cheat sheet

---

### Option 2: Kubernetes

**Best for:**
- High availability requirements
- Auto-scaling needs
- Large production deployments
- Multi-region

**What you deploy:**
```
Kubernetes Deployment:
├── Pods (Auth API + OPA sidecar)
├── Service (load balancer)
├── Ingress (routing)
├── ConfigMaps (OPA policy)
└── Secrets (credentials)

External:
└── Managed PostgreSQL (RDS/Cloud SQL)
```

**Guides:**
- `DEPLOYMENT_COMPARISON.md` - Docker vs K8s comparison
- K8s guide: (create when ready to migrate)

---

## 🗄️ Database Setup

### PostgreSQL Requirements

**Create database and user:**
```sql
CREATE DATABASE auth_db;
CREATE USER auth_user WITH PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE auth_db TO auth_user;
\c auth_db
GRANT ALL ON SCHEMA public TO auth_user;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

**Tables created by migration:**
- `users` (existing)
- `sessions` (existing)
- `organizations` (new)
- `accounts` (new)
- `projects` (new)
- `user_role_assignments` (new)

**See:** `EXTERNAL_POSTGRES.md` for detailed setup

---

## 🔧 Configuration

### Required Environment Variables

```bash
# Database (point to your shared PostgreSQL)
SQLALCHEMY_DATABASE_URL=postgresql://auth_user:pass@postgres-host:5432/auth_db

# Security (generate random keys!)
SECRET_KEY=<random-key>
API_KEY_SECRET=<random-key>

# Email (for MFA, password reset)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@yourcompany.com

# Frontend
FRONTEND_URL=https://yourapp.com

# CORS
CORS_ORIGINS=https://yourapp.com,https://admin.yourapp.com
```

**Generate keys:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 📊 Architecture

### Docker Deployment

```
┌─────────────────────────────────────┐
│      Your Server (Docker Host)      │
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │  Auth API    │  │     OPA     │ │
│  │  :8004       │──│   :8181     │ │
│  └──────┬───────┘  └─────────────┘ │
│         │                           │
│         │ Network connection        │
└─────────┼───────────────────────────┘
          │
          ▼
┌─────────────────────────────────────┐
│   PostgreSQL Server (Shared)        │
│                                     │
│  ┌──────────┐  ┌──────────┐       │
│  │ auth_db  │  │ app_db   │  ...  │
│  └──────────┘  └──────────┘       │
└─────────────────────────────────────┘
```

### Key Points

- **Auth API** runs in Docker container
- **OPA** runs in separate Docker container (same network)
- **PostgreSQL** runs externally (shared with other services)
- Only port **8004** exposed to internet
- OPA only accessible within Docker network

---

## 🔒 Security

### What's Protected

1. **User Status Check** - Only ACTIVE users can access resources
2. **OPA Policy** - Declarative authorization rules
3. **Role-Based Access** - Organizations → Accounts → Projects hierarchy
4. **Network Isolation** - OPA not exposed to internet
5. **Credential Management** - Environment variables, not hardcoded

### Security Checklist

- [ ] Generated strong SECRET_KEY and API_KEY_SECRET
- [ ] PostgreSQL uses strong password
- [ ] CORS_ORIGINS set to specific domains (not *)
- [ ] SSL/TLS for PostgreSQL connection
- [ ] Reverse proxy (Nginx) with HTTPS
- [ ] Firewall rules configured
- [ ] Database backups configured

---

## 📈 Scaling

### Vertical Scaling (More Resources)

Edit `docker-compose.prod.yaml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 4G
```

### Horizontal Scaling (More Instances)

```bash
# Scale to 3 Auth API instances
docker compose -f docker-compose.prod.yaml up -d --scale auth_api=3

# Add load balancer (Nginx/Traefik)
```

**Note:** Each Auth API instance gets its own OPA container automatically!

### When to Migrate to Kubernetes

- Traffic > 10k requests/min
- Need 99.9%+ uptime
- Need auto-scaling
- Multi-region deployment

---

## 🆘 Quick Commands

### Deploy
```bash
docker compose -f docker-compose.prod.yaml --env-file .env.production up -d
```

### Check Status
```bash
docker compose -f docker-compose.prod.yaml ps
```

### View Logs
```bash
docker compose -f docker-compose.prod.yaml logs -f
```

### Health Check
```bash
curl http://localhost:8004/api/health
curl http://localhost:8004/api/authz/health
```

### Restart
```bash
docker compose -f docker-compose.prod.yaml restart
```

### Update
```bash
git pull
docker compose -f docker-compose.prod.yaml up -d --build
```

### Backup Database
```bash
pg_dump -h postgres-host -U auth_user auth_db | gzip > backup.sql.gz
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `DEPLOYMENT_SUMMARY.md` | This file - quick overview |
| `DOCKER_DEPLOYMENT.md` | **START HERE** - Full deployment guide |
| `EXTERNAL_POSTGRES.md` | PostgreSQL setup guide |
| `DOCKER_QUICK_REFERENCE.md` | Command cheat sheet |
| `DEPLOYMENT_COMPARISON.md` | Docker vs Kubernetes |
| `QUICKSTART_AUTHZ.md` | Quick start for testing |
| `IMPLEMENTATION_COMPLETE.md` | What we built |

---

## 🎯 Recommended Path

### For Your Use Case (Dev-Level Traffic, Shared PostgreSQL)

1. **Read** `DOCKER_DEPLOYMENT.md` (comprehensive guide)
2. **Set up** PostgreSQL database (see `EXTERNAL_POSTGRES.md`)
3. **Configure** `.env.production` with your values
4. **Deploy** with Docker Compose
5. **Test** endpoints
6. **Add** reverse proxy (Nginx) for SSL
7. **Monitor** and iterate

### Timeline

- **Day 1:** Set up PostgreSQL, configure environment
- **Day 1:** Deploy Auth API with Docker Compose
- **Day 2:** Set up reverse proxy, SSL certificates
- **Day 2:** Test all endpoints, create test data
- **Day 3:** Integrate with your applications
- **Ongoing:** Monitor, backup, maintain

---

## 💡 Key Decisions Made

### Why Docker Compose?
- ✅ Simpler than Kubernetes
- ✅ Perfect for dev-level traffic
- ✅ Easy to debug and maintain
- ✅ Can migrate to K8s later if needed

### Why External PostgreSQL?
- ✅ Share one PostgreSQL across services
- ✅ Easier to manage backups centrally
- ✅ Lower resource usage
- ✅ Simpler for dev/staging

### Why OPA as Separate Container?
- ✅ Use official OPA image
- ✅ Easy to update OPA independently
- ✅ Clear separation of concerns
- ✅ Reusable pattern (same for K8s)

---

## 🎊 You're Ready!

Everything is set up for a simple Docker deployment with external PostgreSQL.

**Next step:** Read `DOCKER_DEPLOYMENT.md` and deploy! 🚀

---

## 🆘 Need Help?

1. Check the relevant guide (see Documentation Files above)
2. Check `DOCKER_QUICK_REFERENCE.md` for commands
3. Check logs: `docker compose logs -f`
4. Check health: `curl http://localhost:8004/api/authz/health`

**Common issues:**
- Can't connect to PostgreSQL → Check `EXTERNAL_POSTGRES.md`
- OPA not healthy → Check policy files are mounted
- Auth API won't start → Check environment variables

