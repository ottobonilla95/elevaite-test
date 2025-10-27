# Admin API Quick Reference

## 🚀 User Status Management

### Update Status (Generic)
```bash
POST /api/admin/users/{user_id}/status
Authorization: Bearer <superuser-token>

{
  "status": "suspended",  # active | inactive | suspended | pending
  "reason": "Optional reason"
}
```

### Convenience Endpoints
```bash
# Suspend user
POST /api/admin/users/{user_id}/suspend?reason=Policy%20violation

# Activate user
POST /api/admin/users/{user_id}/activate?reason=Suspension%20ended

# Deactivate user
POST /api/admin/users/{user_id}/deactivate?reason=User%20left%20company
```

---

## 👥 Session Management

### View User Sessions
```bash
GET /api/admin/users/{user_id}/sessions
Authorization: Bearer <admin-or-superuser-token>

# Response shows:
# - total_sessions: All sessions
# - active_sessions: Currently signed in (if > 0)
# - sessions: Array with details
```

### Revoke All Sessions
```bash
POST /api/admin/users/{user_id}/revoke-sessions
Authorization: Bearer <superuser-token>

# Forces user to re-login on all devices
```

---

## 📊 Status Values

| Status | Can Login? | Use For |
|--------|------------|---------|
| `active` | ✅ Yes | Normal users |
| `inactive` | ❌ No | Closed accounts |
| `suspended` | ❌ No | Temporary ban |
| `pending` | ❌ No | Awaiting verification |

---

## 🔒 Authorization

| Endpoint | Required Role |
|----------|---------------|
| Update status | Superuser |
| Suspend/activate/deactivate | Superuser |
| View sessions | Admin or Superuser |
| Revoke sessions | Superuser |

---

## 💡 Common Workflows

### Suspend User for Security
```bash
# 1. Suspend account
POST /api/admin/users/5/suspend?reason=Security%20incident

# 2. Revoke all sessions
POST /api/admin/users/5/revoke-sessions
```

### Check If User Is Online
```bash
GET /api/admin/users/5/sessions

# If active_sessions > 0, user is signed in
```

### Reactivate After Suspension
```bash
POST /api/admin/users/5/activate?reason=Suspension%20period%20ended
```

---

## 🧪 Testing

```bash
cd python_apps/auth_api
pytest tests/unit/test_admin_endpoints.py tests/integration/test_admin_api.py -v
```

**Result: 25/25 tests passing** ✅

---

## 📝 Notes

- **Status** = Account lifecycle (enabled/disabled)
- **Sessions** = Sign-in state (online/offline)
- Cannot modify your own status
- All changes are audit logged

