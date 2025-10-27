# RBAC SDK Progress Log

Status: in-flight

## Milestone 1 — Basic SDK + PoC
- [x] Sync client: check_access(user_id, action, resource)
- [x] FastAPI guard: require_permission(...)
- [x] Resource builders: project/account/org from headers
- [x] Principal resolvers: user header; api key or user
- [x] API key validation helpers
  - [x] HTTP validator (calls Auth API) with small TTL cache
  - [x] Local JWT validator (offline)
- [x] Auth API: /api/auth/validate-apikey (JWT-based)

Notes:
- Header names: X-elevAIte-UserId, X-elevAIte-OrganizationId, X-elevAIte-AccountId, X-elevAIte-ProjectId, X-elevAIte-apikey
- RBAC service URL (dev): http://localhost:8101

## Milestone 2 — Async + Guarantees (current)
- [x] Async client: check_access_async(...) using httpx
- [x] Async guard: require_permission_async(...)
- [ ] Integration test to verify the handler does not start before guard completes (slow RBAC)
- [ ] Default timeouts/retries; fail-closed on timeout

How to use (local JWT keys):
- Set in the API service env:
  - RBAC_SDK_APIKEY_ENABLE_LOCAL_JWT=true
  - API_KEY_ALGORITHM=HS256 (or RS256/ES256)
  - API_KEY_SECRET=... (HS*) or API_KEY_PUBLIC_KEY=... (RS*/ES*)
- Guard example:

````python
from rbac_sdk import require_permission_async, resource_builders, principal_resolvers

_guard = require_permission_async(
    action="view_project",
    resource_builder=resource_builders.project_from_headers(),
    principal_resolver=principal_resolvers.api_key_or_user(),
)
````

## Milestone 3 — Robustness
- [ ] Async retries with backoff; configurable timeouts
- [ ] Bearer JWT resolver (Authorization: Bearer ...)
- [ ] Global SDK config (timeouts, base URLs)
- [ ] Diagnostics hooks (correlation ID, minimal structured logs)

## Milestone 4 — API Key UX (optional direction)
- [ ] Opaque API keys (short ID + long secret) in Auth API
- [ ] CRUD: create/list/revoke/rotate with scopes + tenant binding
- [ ] Auth-side validation (lookup + hash), SDK http validator uses endpoint

## Open Questions
- Standardize on local JWT API keys vs opaque keys? (we can support both)
- Do we want immediate revocation guarantees? (if yes, prefer opaque keys or JWT + denylist)

## Next Actions
- Implement integration test for async guard timing
- Add small retry/backoff in async client and fail-closed semantics
- Optionally wire guard on GET /workflows (PoC) or ETL route for live testing

