#!/bin/bash
# Test script for dynamic policy management
# This demonstrates how to manage OPA policies via API

set -e

# Configuration
AUTH_API_URL="http://localhost:8004/auth-api"
SUPERUSER_TOKEN="your-superuser-token-here"  # Replace with actual token

echo "🧪 Testing Dynamic Policy Management"
echo "===================================="
echo ""

# Function to make authenticated requests
auth_request() {
    curl -s -X "$1" "$AUTH_API_URL$2" \
        -H "Authorization: Bearer $SUPERUSER_TOKEN" \
        -H "Content-Type: application/json" \
        ${3:+-d "$3"}
}

# Test 1: List existing policies
echo "📋 Test 1: List existing policies"
echo "GET /api/policies"
auth_request GET "/api/policies" | jq '.'
echo ""

# Test 2: Generate policy for Workflow service
echo "🔧 Test 2: Generate policy for Workflow service"
echo "POST /api/policies/generate"
WORKFLOW_POLICY='{
  "service_name": "workflow_engine",
  "resource_type": "workflow",
  "belongs_to": "project",
  "actions": {
    "superadmin": ["create_workflow", "edit_workflow", "view_workflow", "delete_workflow", "execute_workflow"],
    "admin": ["create_workflow", "edit_workflow", "view_workflow", "delete_workflow", "execute_workflow"],
    "editor": ["create_workflow", "edit_workflow", "view_workflow", "execute_workflow"],
    "viewer": ["view_workflow"]
  }
}'
auth_request POST "/api/policies/generate" "$WORKFLOW_POLICY" | jq '.'
echo ""

# Test 3: Generate policy for Agent service
echo "🤖 Test 3: Generate policy for Agent service"
echo "POST /api/policies/generate"
AGENT_POLICY='{
  "service_name": "agent_studio",
  "resource_type": "agent",
  "belongs_to": "project",
  "actions": {
    "superadmin": ["create_agent", "edit_agent", "view_agent", "delete_agent", "execute_agent"],
    "admin": ["create_agent", "edit_agent", "view_agent", "delete_agent", "execute_agent"],
    "editor": ["create_agent", "edit_agent", "view_agent", "execute_agent"],
    "viewer": ["view_agent"]
  }
}'
auth_request POST "/api/policies/generate" "$AGENT_POLICY" | jq '.'
echo ""

# Test 4: Generate policy for Report service
echo "📊 Test 4: Generate policy for Report service"
echo "POST /api/policies/generate"
REPORT_POLICY='{
  "service_name": "reports",
  "resource_type": "report",
  "belongs_to": "project",
  "actions": {
    "superadmin": ["create_report", "edit_report", "view_report", "delete_report", "export_report"],
    "admin": ["create_report", "edit_report", "view_report", "delete_report", "export_report"],
    "editor": ["create_report", "edit_report", "view_report", "export_report"],
    "viewer": ["view_report", "export_report"]
  }
}'
auth_request POST "/api/policies/generate" "$REPORT_POLICY" | jq '.'
echo ""

# Test 5: Upload custom policy
echo "✍️  Test 5: Upload custom policy (analyst role)"
echo "POST /api/policies/upload"
CUSTOM_POLICY='{
  "module_name": "rbac/custom_analyst",
  "rego_code": "package rbac\n\nimport rego.v1\n\n# Analyst can export data from any project they have access to\nrole_check(assignment) if {\n    assignment.role == \"analyst\"\n    input.resource.type in {\"report\", \"workflow\", \"agent\"}\n    input.action in {\"export_data\", \"view_analytics\"}\n}"
}'
auth_request POST "/api/policies/upload" "$CUSTOM_POLICY" | jq '.'
echo ""

# Test 6: List policies again (should see new ones)
echo "📋 Test 6: List all policies (after adding new ones)"
echo "GET /api/policies"
auth_request GET "/api/policies" | jq '.'
echo ""

# Test 7: Get specific policy
echo "🔍 Test 7: Get workflow policy"
echo "GET /api/policies/rbac/workflow_engine"
auth_request GET "/api/policies/rbac/workflow_engine" | jq '.'
echo ""

# Test 8: Test authorization with new policy
echo "✅ Test 8: Test authorization with workflow policy"
echo "POST /api/authz/check_access"
AUTH_CHECK='{
  "user_id": 1,
  "action": "view_workflow",
  "resource": {
    "type": "workflow",
    "id": "workflow-123",
    "project_id": "proj-456",
    "account_id": "acct-789",
    "organization_id": "org-001"
  }
}'
auth_request POST "/api/authz/check_access" "$AUTH_CHECK" | jq '.'
echo ""

# Test 9: Delete a policy
echo "🗑️  Test 9: Delete custom analyst policy"
echo "DELETE /api/policies/rbac/custom_analyst"
auth_request DELETE "/api/policies/rbac/custom_analyst" | jq '.'
echo ""

# Test 10: Verify deletion
echo "📋 Test 10: List policies (after deletion)"
echo "GET /api/policies"
auth_request GET "/api/policies" | jq '.'
echo ""

echo "✅ All tests completed!"
echo ""
echo "💡 Tips:"
echo "  - Policies are stored in OPA memory (restart OPA to clear)"
echo "  - Use /api/policies/generate for standard CRUD permissions"
echo "  - Use /api/policies/upload for custom rego code"
echo "  - All policy changes take effect immediately (no restart needed)"

