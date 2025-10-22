# Quick Start: Minimal SDK for Tool Steps

## Simplified Approach

Instead of extracting everything from the PoC, let's take a **pragmatic approach**:

1. **Keep the PoC integration** we already did (importing PoC routers)
2. **Fix the duplicate endpoint warnings** by namespacing
3. **Get tool steps working NOW** via the PoC endpoints
4. **Extract to SDK incrementally** over time

## Why This Approach?

- ✅ **Fastest path to demo** - Tool steps work immediately
- ✅ **No breaking changes** - Both systems coexist
- ✅ **Incremental migration** - Extract to SDK piece by piece
- ✅ **Lower risk** - Can rollback easily

## What We Already Have

The integration we did earlier gives us:
- `/api/poc/workflows` - PoC workflows with tool steps
- `/api/poc/tools` - PoC tool management
- `/api/executions` - PoC execution tracking
- `/api/steps` - PoC step registry

## Next Steps (Immediate)

### 1. Fix Duplicate Warnings
Update `agent_studio/main.py` to namespace conflicting routers properly.

### 2. Create Simple Frontend Example
Show how to:
- Create a workflow with tool steps via `/api/poc/workflows`
- Execute it via `/api/poc/workflows/{id}/execute`
- View results via `/api/executions/{id}`

### 3. Document the Dual API
- Legacy: `/api/workflows` (agent_studio)
- New: `/api/poc/workflows` (PoC with tool steps)

## Future: Gradual SDK Extraction

Once tool steps are demoed and working:

### Phase 1: Extract Core (Week 1)
- Move tool decorators to SDK ✅ (already done)
- Move basic_tools to SDK ✅ (already done)
- Move tool_steps execution logic to SDK
- Keep database models in PoC for now

### Phase 2: Extract Database (Week 2)
- Move SQLModel models to SDK
- Create database migration utilities
- Update PoC to use SDK models

### Phase 3: Extract Services (Week 3)
- Move WorkflowsService to SDK
- Move ExecutionsService to SDK
- Move ToolsService to SDK

### Phase 4: Rebuild agent_studio (Week 4)
- Replace agent_studio implementation with SDK
- Deprecate `/api/poc/*` endpoints
- Migrate all endpoints to use SDK

## Decision Point

**Option A: Continue Full Extraction** (2-3 days)
- Extract all PoC code to SDK now
- Rebuild agent_studio from scratch
- Higher risk, longer timeline

**Option B: Use Current Integration** (30 minutes)
- Fix duplicate warnings
- Document dual API
- Demo tool steps today
- Extract to SDK incrementally

**Recommendation: Option B**

Get tool steps working NOW, then extract to SDK over time as a separate effort.

What do you think?

