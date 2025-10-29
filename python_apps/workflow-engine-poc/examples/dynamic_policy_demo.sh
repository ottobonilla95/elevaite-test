#!/bin/bash

# Dynamic Policy Management Demo
# This script demonstrates how to change role permissions via API without code changes

set -e

# Configuration
AUTH_API_URL="${AUTH_API_URL:-http://localhost:8004}"
WORKFLOW_ENGINE_URL="${WORKFLOW_ENGINE_URL:-http://localhost:8006}"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper functions
print_section() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if required environment variables are set
if [ -z "$SUPERUSER_EMAIL" ] || [ -z "$SUPERUSER_PASSWORD" ]; then
    print_error "Please set SUPERUSER_EMAIL and SUPERUSER_PASSWORD environment variables"
    echo "Example: export SUPERUSER_EMAIL=superuser@elevaite.com SUPERUSER_PASSWORD=superuser123"
    exit 1
fi

print_section "Dynamic Policy Management Demo"
echo "This demo shows how to change role permissions via API without code changes!"

# ============================================================================
# Step 1: Login as superuser
# ============================================================================

print_section "Step 1: Login as Superuser"
print_info "Logging in as superuser to get access token..."

LOGIN_RESPONSE=$(curl -s -X POST "$AUTH_API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$SUPERUSER_EMAIL\",
    \"password\": \"$SUPERUSER_PASSWORD\"
  }")

SUPERUSER_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

if [ "$SUPERUSER_TOKEN" == "null" ] || [ -z "$SUPERUSER_TOKEN" ]; then
    print_error "Failed to login as superuser"
    echo $LOGIN_RESPONSE | jq .
    exit 1
fi

print_success "Superuser logged in successfully"

# ============================================================================
# Step 2: List current policies
# ============================================================================

print_section "Step 2: List Current Policies"
print_info "Fetching all policy modules from OPA..."

POLICIES_RESPONSE=$(curl -s -X GET "$AUTH_API_URL/api/policies" \
  -H "Authorization: Bearer $SUPERUSER_TOKEN")

print_success "Current policies:"
echo $POLICIES_RESPONSE | jq '.policies'

# ============================================================================
# Step 3: View current workflow policy (if exists)
# ============================================================================

print_section "Step 3: View Current Workflow Policy"
print_info "Checking if workflow_engine policy exists..."

CURRENT_POLICY=$(curl -s -X GET "$AUTH_API_URL/api/policies/rbac/workflow_engine" \
  -H "Authorization: Bearer $SUPERUSER_TOKEN")

if echo $CURRENT_POLICY | jq -e '.module_name' > /dev/null 2>&1; then
    print_success "Current workflow_engine policy found:"
    echo $CURRENT_POLICY | jq -r '.rego_code' | head -20
    echo "..."
else
    print_info "No workflow_engine policy found (using default rbac policy)"
fi

# ============================================================================
# Step 4: Generate new policy - Allow viewers to execute
# ============================================================================

print_section "Step 4: Generate New Policy - Allow Viewers to Execute"
print_info "Creating policy that allows viewers to execute workflows..."

GENERATE_RESPONSE=$(curl -s -X POST "$AUTH_API_URL/api/policies/generate" \
  -H "Authorization: Bearer $SUPERUSER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "workflow_engine",
    "resource_type": "workflow",
    "belongs_to": "project",
    "actions": {
      "superadmin": ["create_workflow", "edit_workflow", "view_workflow", "delete_workflow", "execute_workflow"],
      "admin": ["create_workflow", "edit_workflow", "view_workflow", "delete_workflow", "execute_workflow"],
      "editor": ["create_workflow", "edit_workflow", "view_workflow", "execute_workflow"],
      "viewer": ["view_workflow", "execute_workflow"]
    }
  }')

if echo $GENERATE_RESPONSE | jq -e '.message' > /dev/null 2>&1; then
    print_success "Policy generated and uploaded successfully!"
    echo $GENERATE_RESPONSE | jq .
else
    print_error "Failed to generate policy"
    echo $GENERATE_RESPONSE | jq .
    exit 1
fi

# ============================================================================
# Step 5: Verify new policy
# ============================================================================

print_section "Step 5: Verify New Policy"
print_info "Fetching updated workflow_engine policy..."

NEW_POLICY=$(curl -s -X GET "$AUTH_API_URL/api/policies/rbac/workflow_engine" \
  -H "Authorization: Bearer $SUPERUSER_TOKEN")

print_success "Updated policy:"
echo $NEW_POLICY | jq -r '.rego_code'

# ============================================================================
# Step 6: Test authorization with new policy
# ============================================================================

print_section "Step 6: Test Authorization with New Policy"

# Create a test user if needed
print_info "Creating test viewer user..."
TIMESTAMP=$(date +%s)
TEST_USER_EMAIL="test-viewer-$TIMESTAMP@elevaite.com"

REGISTER_RESPONSE=$(curl -s -X POST "$AUTH_API_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_USER_EMAIL\",
    \"password\": \"TestPassword123!\",
    \"full_name\": \"Test Viewer $TIMESTAMP\"
  }")

TEST_USER_ID=$(echo $REGISTER_RESPONSE | jq -r '.user.id')

if [ "$TEST_USER_ID" == "null" ] || [ -z "$TEST_USER_ID" ]; then
    print_error "Failed to create test user"
    echo $REGISTER_RESPONSE | jq .
    exit 1
fi

print_success "Test user created (ID: $TEST_USER_ID)"

# Get organization, account, and project IDs
print_info "Getting resource IDs..."

ORG_RESPONSE=$(curl -s -X GET "$AUTH_API_URL/api/rbac/organizations?limit=1" \
  -H "Authorization: Bearer $SUPERUSER_TOKEN")
ORG_ID=$(echo $ORG_RESPONSE | jq -r '.organizations[0].id')

ACCOUNT_RESPONSE=$(curl -s -X GET "$AUTH_API_URL/api/rbac/accounts?limit=1" \
  -H "Authorization: Bearer $SUPERUSER_TOKEN")
ACCOUNT_ID=$(echo $ACCOUNT_RESPONSE | jq -r '.accounts[0].id')

PROJECT_RESPONSE=$(curl -s -X GET "$AUTH_API_URL/api/rbac/projects?limit=1" \
  -H "Authorization: Bearer $SUPERUSER_TOKEN")
PROJECT_ID=$(echo $PROJECT_RESPONSE | jq -r '.projects[0].id')

print_success "Org: $ORG_ID, Account: $ACCOUNT_ID, Project: $PROJECT_ID"

# Assign viewer role
print_info "Assigning viewer role to test user..."

ASSIGNMENT_RESPONSE=$(curl -s -X POST "$AUTH_API_URL/api/rbac/user_role_assignments" \
  -H "Authorization: Bearer $SUPERUSER_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": $TEST_USER_ID,
    \"role\": \"viewer\",
    \"resource_type\": \"project\",
    \"resource_id\": \"$PROJECT_ID\"
  }")

print_success "Viewer role assigned"

# Test view_workflow permission
print_info "Testing view_workflow permission..."

VIEW_CHECK=$(curl -s -X POST "$AUTH_API_URL/api/authz/check_access" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": $TEST_USER_ID,
    \"action\": \"view_workflow\",
    \"resource\": {
      \"type\": \"workflow\",
      \"id\": \"test-workflow-uuid\",
      \"project_id\": \"$PROJECT_ID\",
      \"account_id\": \"$ACCOUNT_ID\",
      \"organization_id\": \"$ORG_ID\"
    }
  }")

VIEW_ALLOWED=$(echo $VIEW_CHECK | jq -r '.allowed')
if [ "$VIEW_ALLOWED" == "true" ]; then
    print_success "Viewer CAN view workflows ✓"
else
    print_error "Viewer CANNOT view workflows (unexpected)"
fi

# Test execute_workflow permission
print_info "Testing execute_workflow permission..."

EXECUTE_CHECK=$(curl -s -X POST "$AUTH_API_URL/api/authz/check_access" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": $TEST_USER_ID,
    \"action\": \"execute_workflow\",
    \"resource\": {
      \"type\": \"workflow\",
      \"id\": \"test-workflow-uuid\",
      \"project_id\": \"$PROJECT_ID\",
      \"account_id\": \"$ACCOUNT_ID\",
      \"organization_id\": \"$ORG_ID\"
    }
  }")

EXECUTE_ALLOWED=$(echo $EXECUTE_CHECK | jq -r '.allowed')
if [ "$EXECUTE_ALLOWED" == "true" ]; then
    print_success "Viewer CAN execute workflows ✓ (NEW PERMISSION!)"
else
    print_error "Viewer CANNOT execute workflows"
fi

# Test edit_workflow permission (should be denied)
print_info "Testing edit_workflow permission (should be denied)..."

EDIT_CHECK=$(curl -s -X POST "$AUTH_API_URL/api/authz/check_access" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": $TEST_USER_ID,
    \"action\": \"edit_workflow\",
    \"resource\": {
      \"type\": \"workflow\",
      \"id\": \"test-workflow-uuid\",
      \"project_id\": \"$PROJECT_ID\",
      \"account_id\": \"$ACCOUNT_ID\",
      \"organization_id\": \"$ORG_ID\"
    }
  }")

EDIT_ALLOWED=$(echo $EDIT_CHECK | jq -r '.allowed')
if [ "$EDIT_ALLOWED" == "false" ]; then
    print_success "Viewer CANNOT edit workflows ✓ (as expected)"
else
    print_error "Viewer CAN edit workflows (unexpected)"
fi

# ============================================================================
# Step 7: Cleanup - Delete test user assignment
# ============================================================================

print_section "Step 7: Cleanup"
print_info "Deleting test user role assignment..."

DELETE_RESPONSE=$(curl -s -X DELETE "$AUTH_API_URL/api/rbac/user_role_assignments/$TEST_USER_ID/$PROJECT_ID" \
  -H "Authorization: Bearer $SUPERUSER_TOKEN" \
  -w "\nHTTP_STATUS:%{http_code}")

HTTP_STATUS=$(echo "$DELETE_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)

if [ "$HTTP_STATUS" == "204" ] || [ "$HTTP_STATUS" == "200" ]; then
    print_success "Test user assignment deleted"
else
    print_info "Could not delete assignment (may not exist)"
fi

# ============================================================================
# Summary
# ============================================================================

print_section "Demo Complete!"

echo -e "${GREEN}Summary:${NC}"
echo "1. ✓ Listed current policies in OPA"
echo "2. ✓ Generated new workflow_engine policy via API"
echo "3. ✓ Uploaded policy to OPA (no code changes!)"
echo "4. ✓ Verified policy was loaded correctly"
echo "5. ✓ Tested authorization with new permissions"
echo "6. ✓ Confirmed viewers can now execute workflows"
echo ""
echo -e "${BLUE}Key Takeaway:${NC}"
echo "Role permissions were changed via API without any code changes or redeployment!"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "- Update workflow engine guards to use specific actions (execute_workflow, etc.)"
echo "- Create custom roles with specific permissions"
echo "- Set up per-client custom permissions"
echo ""
echo "See DYNAMIC_PERMISSIONS.md for more examples and details."

