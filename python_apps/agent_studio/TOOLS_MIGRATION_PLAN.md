# Tools Migration Plan

## Overview
Migrate 30+ tools from `agents/tools.py` (5500 lines) to workflow-core-sdk with proper organization.

## Tool Categories Identified

### 1. **MITIE RFQ Tools** (3 tools)
- `extract_rfq_json` - Extract structured data from RFQ documents
- `calculate_mitie_quote` - Calculate quotes based on extracted data
- `generate_mitie_pdf` - Generate PDF quotes

**Target:** `workflow_core_sdk/tools/mitie/`

### 2. **ServiceNow Tools** (2 tools + imports)
- `ServiceNow_ITSM` - ITSM operations (create/get/update incidents)
- `ServiceNow_CSM` - CSM operations (create/get/update cases)
- Already has imports from `tools/servicenow/`

**Target:** `workflow_core_sdk/tools/servicenow/`

### 3. **Salesforce Tools** (5 tools + imports)
- `get_salesforce_accounts` - Get Salesforce accounts
- `get_salesforce_opportunities` - Get opportunities
- `get_salesforce_opportunities_by_account` - Get opportunities by account
- `create_salesforce_insertion_order` - Create insertion orders
- `Salesforce_CSM` - CSM operations
- Already has imports from `tools/salesforce/`

**Target:** `workflow_core_sdk/tools/salesforce/`

### 4. **Kevel Ad Platform Tools** (3 tools)
- `create_insertion_order` - Create Kevel insertion orders
- `kevel_get_sites` - Get Kevel sites
- `kevel_get_ad_types` - Get ad types
- `kevel_debug_api` - Debug API

**Target:** `workflow_core_sdk/tools/kevel/`

### 5. **Database Tools** (3 tools)
- `redis_cache_operation` - Redis cache operations
- `postgres_query` - PostgreSQL queries
- `sql_database` - SQL database queries

**Target:** `workflow_core_sdk/tools/database/`

### 6. **Search & Retrieval Tools** (7 tools)
- `query_retriever` - Query retriever for machine types
- `query_retriever2` - Alternative query retriever
- `customer_query_retriever` - Customer-specific queries
- `media_context_retriever` - Media context retrieval
- `vectorizer_conversative_search` - Conservative vector search
- `document_search` - Document search
- `document_metadata_search` - Document metadata search

**Target:** `workflow_core_sdk/tools/search/`

### 7. **Web Tools** (2 tools)
- `web_search` - Google search
- `url_to_markdown` - Convert URLs to markdown

**Target:** `workflow_core_sdk/tools/web/`

### 8. **AI/Image Tools** (1 tool)
- `image_generation` - Generate images with AI

**Target:** `workflow_core_sdk/tools/ai/`

### 9. **Utility Tools** (5 tools)
- `add_numbers` - Simple math
- `print_to_console` - Console output
- `weather_forecast` - Weather data
- `arlo_api` - Arlo API integration

**Target:** `workflow_core_sdk/tools/utilities/`

### 10. **Customer/Order Tools** (3 tools)
- `get_customer_order` - Get customer orders
- `get_customer_location` - Get customer location
- `add_customer` - Add customer

**Target:** `workflow_core_sdk/tools/customer/`

## Migration Strategy

### Phase 1: Setup Structure (Priority 1)
1. Create directory structure in SDK:
   ```
   workflow_core_sdk/tools/
   ├── __init__.py (update to export all tools)
   ├── mitie/
   ├── servicenow/
   ├── salesforce/
   ├── kevel/
   ├── database/
   ├── search/
   ├── web/
   ├── ai/
   ├── utilities/
   └── customer/
   ```

### Phase 2: High-Value Tools First (Priority 1)
Migrate in this order based on business value:

1. **ServiceNow Tools** - Already partially migrated, critical for ITSM
2. **Salesforce Tools** - Already partially migrated, critical for CRM
3. **MITIE RFQ Tools** - Large custom business logic
4. **Kevel Tools** - Ad platform integration

### Phase 3: Supporting Tools (Priority 2)
5. **Search & Retrieval Tools** - Core functionality
6. **Database Tools** - Infrastructure
7. **Web Tools** - Common utilities

### Phase 4: Nice-to-Have Tools (Priority 3)
8. **AI/Image Tools** - Enhancement features
9. **Utility Tools** - Helpers
10. **Customer/Order Tools** - Demo/example tools

## Migration Process Per Tool

For each tool:

1. **Create module file** in appropriate category directory
2. **Copy function** with `@function_schema` decorator
3. **Update imports** to use SDK patterns
4. **Add to category `__init__.py`** for exports
5. **Register in tool_registry** (automatic via `@function_schema`)
6. **Test** the tool works in isolation
7. **Update Agent Studio** to import from SDK instead of local

## File Organization Pattern

Each category should follow this pattern:

```python
# workflow_core_sdk/tools/category_name/__init__.py
from .tool1 import tool1_function
from .tool2 import tool2_function

__all__ = ["tool1_function", "tool2_function"]
```

```python
# workflow_core_sdk/tools/category_name/tool1.py
from workflow_core_sdk.tools.registry import function_schema

@function_schema
def tool1_function(param: str) -> str:
    """Tool description"""
    # Implementation
    pass
```

## Dependencies to Handle

Many tools have external dependencies:
- `google-api-python-client` - Google APIs
- `beautifulsoup4` - Web scraping
- `markdownify` - HTML to Markdown
- `redis` - Redis cache
- `psycopg2` - PostgreSQL
- `requests` - HTTP requests
- ServiceNow/Salesforce SDKs

**Strategy:** Add optional dependencies to SDK with proper error handling if not installed.

## Testing Strategy

1. **Unit tests** for each tool in SDK
2. **Integration tests** for tools that need external services
3. **Mock external APIs** for testing
4. **Verify tool_registry** picks up all tools

## Backward Compatibility

During migration:
- Keep original `agents/tools.py` working
- Agent Studio can import from both locations
- Gradually deprecate local tools as SDK versions are verified
- Use feature flags to switch between local/SDK tools

## Success Criteria

- ✅ All 30+ tools migrated to SDK
- ✅ Organized into logical categories
- ✅ All tools registered in tool_registry
- ✅ Tests passing for all tools
- ✅ Agent Studio using SDK tools
- ✅ Original tools.py can be archived

## Next Steps

1. Start with Phase 1: Create directory structure
2. Migrate ServiceNow tools (already partially done)
3. Migrate Salesforce tools (already partially done)
4. Continue with remaining categories in priority order

