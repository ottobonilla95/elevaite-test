# User Status Field Analysis

## 🎯 Summary

**ISSUE IDENTIFIED:** The `User.status` field is currently being used for **account lifecycle management**, NOT for tracking whether users are signed in.

---

## 📊 Current Status Values

```python
class UserStatus(str, Enum):
    ACTIVE = "active"        # Account is enabled and can log in
    INACTIVE = "inactive"    # Account is disabled (cannot log in)
    SUSPENDED = "suspended"  # Account is suspended (cannot log in)
    PENDING = "pending"      # Account is awaiting activation (cannot log in)
```

---

## 🔍 How Status is Currently Used

### 1. **Account Creation** (Default: ACTIVE)

<augment_code_snippet path="python_apps/auth_api/app/services/auth_orm.py" mode="EXCERPT">
````python
new_user = User(
    email=normalized_email,
    hashed_password=get_password_hash(password),
    full_name=user_data.full_name,
    status=UserStatus.ACTIVE.value,  # Set to active by default
    is_verified=False,
    ...
)
````
</augment_code_snippet>

**New users are created with `status="active"` immediately!**

---

### 2. **Login Check** (Must be ACTIVE)

<augment_code_snippet path="python_apps/auth_api/app/services/auth_orm.py" mode="EXCERPT">
````python
# Check if account is active
if user.status != UserStatus.ACTIVE.value:
    print(f"Account is not active for user: {email}, status: {user.status}")
    return None, False
````
</augment_code_snippet>

**Users can only log in if `status="active"`**

---

### 3. **Authorization Check** (Must be ACTIVE)

<augment_code_snippet path="python_apps/auth_api/app/routers/authz.py" mode="EXCERPT">
````python
# SECURITY CHECK - User must be active
if user.status != "active":
    logger.warning(
        f"Access denied for user {user.id} ({user.email}) - "
        f"User status is '{user.status}', not 'active'"
    )
    return AccessCheckResponse(
        allowed=False,
        deny_reason="user_not_active",
        user_status=user.status,
    )
````
</augment_code_snippet>

**Authorization is denied if `status != "active"`**

---

### 4. **Status is NEVER Changed After Creation**

**Critical Finding:** There are **NO endpoints** in the auth_api that change user status!

- ❌ No endpoint to set status to "inactive"
- ❌ No endpoint to set status to "suspended"
- ❌ No endpoint to set status to "pending"
- ❌ Status is set to "active" on creation and never changed

---

## 🚨 The Problem

### What Status SHOULD Mean (Account Lifecycle)
- **ACTIVE** - Account is enabled, user can log in
- **INACTIVE** - Account is disabled (e.g., user left company)
- **SUSPENDED** - Account is temporarily suspended (e.g., policy violation)
- **PENDING** - Account is awaiting activation (e.g., email verification)

### What You Thought It Meant (Session State)
- **ACTIVE** - User is currently signed in
- **INACTIVE** - User is currently signed out

### What It Actually Does Now
- **ACTIVE** - Set on creation, never changes
- **INACTIVE/SUSPENDED/PENDING** - Never used (no way to set them!)

---

## ✅ What You Actually Need

### For "User is Signed In" Tracking

Use the **`Session`** model instead!

<augment_code_snippet path="python_apps/auth_api/app/db/models.py" mode="EXCERPT">
````python
class Session(Base, TimestampMixin):
    """User session model for tracking active sessions."""
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    refresh_token: Mapped[str] = mapped_column(String(255), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(default=True)  # ← THIS!
    
    user: Mapped["User"] = relationship(back_populates="sessions")
````
</augment_code_snippet>

**The `Session.is_active` field tracks whether a session is active!**

---

## 🔧 Recommendations

### Option 1: Keep Status for Account Lifecycle (Recommended)

**Use `User.status` for account management:**
- ACTIVE - Account enabled
- INACTIVE - Account disabled
- SUSPENDED - Account suspended
- PENDING - Account awaiting activation

**Use `Session.is_active` for session tracking:**
- TRUE - User has an active session (signed in)
- FALSE - Session is expired/logged out

**Add admin endpoints to manage status:**
```python
@router.post("/admin/users/{user_id}/suspend")
async def suspend_user(user_id: int, ...):
    """Suspend a user account (admin only)."""
    # Set status to "suspended"
    
@router.post("/admin/users/{user_id}/activate")
async def activate_user(user_id: int, ...):
    """Activate a user account (admin only)."""
    # Set status to "active"
```

---

### Option 2: Rename Status Field (Breaking Change)

If you want status to mean "signed in":

1. Rename `User.status` → `User.account_status`
2. Add `User.is_online` or use `Session.is_active`
3. Update all references
4. Create migration

**Not recommended** - more work, less standard

---

## 📋 Current Behavior Summary

| Field | Purpose | Values | When Set | When Changed |
|-------|---------|--------|----------|--------------|
| `User.status` | Account lifecycle | active, inactive, suspended, pending | On creation (→ "active") | **NEVER** (no endpoints!) |
| `Session.is_active` | Session state | true, false | On login (→ true) | On logout (→ false) |
| `User.last_login` | Last login time | datetime | On login | On each login |

---

## 🎯 Action Items

### Immediate (Fix Current System)

1. **Add admin endpoints to manage user status:**
   - `POST /admin/users/{user_id}/suspend` - Suspend account
   - `POST /admin/users/{user_id}/activate` - Activate account
   - `POST /admin/users/{user_id}/deactivate` - Deactivate account

2. **Use Session model for "signed in" tracking:**
   - Query `Session.is_active` to check if user is signed in
   - Don't use `User.status` for this purpose

3. **Update documentation:**
   - Clarify that `status` is for account lifecycle
   - Document that `Session.is_active` is for session state

### Future (Optional Enhancements)

1. **Add account status management UI:**
   - Admin dashboard to suspend/activate users
   - Audit log for status changes

2. **Add automated status changes:**
   - Set to PENDING on registration (if email verification required)
   - Set to ACTIVE after email verification
   - Set to INACTIVE after X days of inactivity

3. **Add status-based features:**
   - Send email when account is suspended
   - Allow users to request reactivation
   - Auto-suspend accounts with suspicious activity

---

## 🔍 Code Locations

### Where Status is Checked
- `python_apps/auth_api/app/services/auth_orm.py:357` - Login check
- `python_apps/auth_api/app/routers/authz.py:64` - Authorization check
- `python_apps/auth_api/app/routers/auth.py:1763` - Token validation
- `python_apps/auth_api/app/routers/auth.py:1856` - Token validation

### Where Status is Set
- `python_apps/auth_api/app/services/auth_orm.py:560` - User creation (→ "active")
- **NOWHERE ELSE!** (No endpoints to change it)

### Where Sessions are Managed
- `python_apps/auth_api/app/services/auth_orm.py` - Session creation/validation
- `python_apps/auth_api/app/routers/auth.py` - Login/logout endpoints

---

## 💡 Quick Fix Example

To check if a user is currently signed in:

```python
# ❌ WRONG - Don't use status for this
if user.status == "active":
    # This just means account is enabled, not that user is signed in!

# ✅ CORRECT - Use sessions
from sqlalchemy import select
from app.db.models import Session

result = await session.execute(
    select(Session).where(
        Session.user_id == user.id,
        Session.is_active == True,
        Session.expires_at > datetime.now(timezone.utc)
    )
)
active_sessions = result.scalars().all()

if active_sessions:
    # User has active sessions (is signed in)
else:
    # User has no active sessions (is signed out)
```

---

## ✅ Conclusion

**The `User.status` field is for account lifecycle management, NOT for tracking sign-in state.**

**To track if users are signed in, use the `Session` model instead.**

**You need to add admin endpoints to actually manage user status (suspend/activate/deactivate).**

