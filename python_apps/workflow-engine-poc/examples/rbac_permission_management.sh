#!/bin/bash

# RBAC Permission Management Examples
# This script demonstrates how admins can manage user permissions through the Auth API

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

# Helper function to print section headers
print_section() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# Helper function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Helper function to print info
print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Helper function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if required environment variables are set
if [ -z "$ADMIN_EMAIL" ] || [ -z "$ADMIN_PASSWORD" ]; then
    print_error "Please set ADMIN_EMAIL and ADMIN_PASSWORD environment variables"
    echo "Example: export ADMIN_EMAIL=admin@elevaite.com ADMIN_PASSWORD=admin123"
    exit 1
fi

print_section "Step 1: Admin Login"
print_info "Logging in as admin to get access token..."

LOGIN_RESPONSE=$(curl -s -X POST "$AUTH_API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$ADMIN_EMAIL\",
    \"password\": \"$ADMIN_PASSWORD\"
  }")

ADMIN_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
ADMIN_USER_ID=$(echo $LOGIN_RESPONSE | jq -r '.user.id')

if [ "$ADMIN_TOKEN" == "null" ] || [ -z "$ADMIN_TOKEN" ]; then
    print_error "Failed to login as admin"
    echo $LOGIN_RESPONSE | jq .
    exit 1
fi

print_success "Admin logged in successfully (User ID: $ADMIN_USER_ID)"

# ============================================================================
# Scenario 1: Create a new user and grant viewer access
# ============================================================================

print_section "Scenario 1: Create User and Grant Viewer Access"

# Register a new user
print_info "Registering new user..."
TIMESTAMP=$(date +%s)
NEW_USER_EMAIL="test-user-$TIMESTAMP@elevaite.com"

REGISTER_RESPONSE=$(curl -s -X POST "$AUTH_API_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$NEW_USER_EMAIL\",
    \"password\": \"TestPassword123!\",
    \"full_name\": \"Test User $TIMESTAMP\"
  }")

NEW_USER_ID=$(echo $REGISTER_RESPONSE | jq -r '.user.id')

if [ "$NEW_USER_ID" == "null" ] || [ -z "$NEW_USER_ID" ]; then
    print_error "Failed to register new user"
    echo $REGISTER_RESPONSE | jq .
    exit 1
fi

print_success "User registered (ID: $NEW_USER_ID, Email: $NEW_USER_EMAIL)"

# Get organization, account, and project IDs
print_info "Getting organization, account, and project IDs..."

ORG_RESPONSE=$(curl -s -X GET "$AUTH_API_URL/api/rbac/organizations?limit=1" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
ORG_ID=$(echo $ORG_RESPONSE | jq -r '.organizations[0].id')

ACCOUNT_RESPONSE=$(curl -s -X GET "$AUTH_API_URL/api/rbac/accounts?limit=1" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
ACCOUNT_ID=$(echo $ACCOUNT_RESPONSE | jq -r '.accounts[0].id')

PROJECT_RESPONSE=$(curl -s -X GET "$AUTH_API_URL/api/rbac/projects?limit=1" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
PROJECT_ID=$(echo $PROJECT_RESPONSE | jq -r '.projects[0].id')

print_success "Org: $ORG_ID, Account: $ACCOUNT_ID, Project: $PROJECT_ID"

# Grant viewer access
print_info "Granting viewer access to project..."

ASSIGNMENT_RESPONSE=$(curl -s -X POST "$AUTH_API_URL/api/rbac/user_role_assignments" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": $NEW_USER_ID,
    \"role\": \"viewer\",
    \"resource_type\": \"project\",
    \"resource_id\": \"$PROJECT_ID\"
  }")

print_success "Viewer role assigned"
echo $ASSIGNMENT_RESPONSE | jq .

# ============================================================================
# Scenario 2: Promote user from viewer to editor
# ============================================================================

print_section "Scenario 2: Promote User from Viewer to Editor"

print_info "Updating role assignment to editor..."

UPDATE_RESPONSE=$(curl -s -X POST "$AUTH_API_URL/api/rbac/user_role_assignments" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": $NEW_USER_ID,
    \"role\": \"editor\",
    \"resource_type\": \"project\",
    \"resource_id\": \"$PROJECT_ID\"
  }")

print_success "User promoted to editor"
echo $UPDATE_RESPONSE | jq .

# ============================================================================
# Scenario 3: List user's role assignments
# ============================================================================

print_section "Scenario 3: List User's Role Assignments"

print_info "Fetching all role assignments for user..."

LIST_RESPONSE=$(curl -s -X GET "$AUTH_API_URL/api/rbac/user_role_assignments?user_id=$NEW_USER_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

print_success "Role assignments retrieved"
echo $LIST_RESPONSE | jq .

# ============================================================================
# Scenario 4: Check authorization
# ============================================================================

print_section "Scenario 4: Check User Authorization"

# Check if user can view project
print_info "Checking if user can view project..."

VIEW_CHECK=$(curl -s -X POST "$AUTH_API_URL/api/authz/check_access" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": $NEW_USER_ID,
    \"action\": \"view_project\",
    \"resource\": {
      \"type\": \"project\",
      \"id\": \"$PROJECT_ID\",
      \"account_id\": \"$ACCOUNT_ID\",
      \"organization_id\": \"$ORG_ID\"
    }
  }")

VIEW_ALLOWED=$(echo $VIEW_CHECK | jq -r '.allowed')
if [ "$VIEW_ALLOWED" == "true" ]; then
    print_success "User CAN view project"
else
    print_error "User CANNOT view project"
fi
echo $VIEW_CHECK | jq .

# Check if user can edit project
print_info "Checking if user can edit project..."

EDIT_CHECK=$(curl -s -X POST "$AUTH_API_URL/api/authz/check_access" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": $NEW_USER_ID,
    \"action\": \"edit_project\",
    \"resource\": {
      \"type\": \"project\",
      \"id\": \"$PROJECT_ID\",
      \"account_id\": \"$ACCOUNT_ID\",
      \"organization_id\": \"$ORG_ID\"
    }
  }")

EDIT_ALLOWED=$(echo $EDIT_CHECK | jq -r '.allowed')
if [ "$EDIT_ALLOWED" == "true" ]; then
    print_success "User CAN edit project"
else
    print_error "User CANNOT edit project"
fi
echo $EDIT_CHECK | jq .

# ============================================================================
# Scenario 5: Test with workflow engine
# ============================================================================

print_section "Scenario 5: Test Access with Workflow Engine"

# Login as the new user to get their access token
print_info "Logging in as new user..."

USER_LOGIN_RESPONSE=$(curl -s -X POST "$AUTH_API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$NEW_USER_EMAIL\",
    \"password\": \"TestPassword123!\"
  }")

USER_TOKEN=$(echo $USER_LOGIN_RESPONSE | jq -r '.access_token')

# Create API key for the user
print_info "Creating API key for user..."

API_KEY_RESPONSE=$(curl -s -X POST "$AUTH_API_URL/api/auth/api-keys" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Test API Key\",
    \"expires_in_days\": 30
  }")

API_KEY=$(echo $API_KEY_RESPONSE | jq -r '.api_key')

print_success "API key created"

# Test listing workflows (should succeed - editor has view_project)
print_info "Testing workflow list access..."

WORKFLOWS_RESPONSE=$(curl -s -X GET "$WORKFLOW_ENGINE_URL/workflows/" \
  -H "X-elevAIte-apikey: $API_KEY" \
  -H "X-elevAIte-ProjectId: $PROJECT_ID" \
  -H "X-elevAIte-AccountId: $ACCOUNT_ID" \
  -H "X-elevAIte-OrganizationId: $ORG_ID")

if echo $WORKFLOWS_RESPONSE | jq -e '.detail' > /dev/null 2>&1; then
    print_error "Failed to list workflows"
    echo $WORKFLOWS_RESPONSE | jq .
else
    print_success "Successfully listed workflows"
    echo $WORKFLOWS_RESPONSE | jq 'if type == "array" then "[\(length) workflows]" else . end'
fi

# ============================================================================
# Scenario 6: Revoke access
# ============================================================================

print_section "Scenario 6: Revoke User Access"

print_info "Deleting role assignment..."

DELETE_RESPONSE=$(curl -s -X DELETE "$AUTH_API_URL/api/rbac/user_role_assignments/$NEW_USER_ID/$PROJECT_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -w "\nHTTP_STATUS:%{http_code}")

HTTP_STATUS=$(echo "$DELETE_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)

if [ "$HTTP_STATUS" == "204" ] || [ "$HTTP_STATUS" == "200" ]; then
    print_success "Role assignment deleted successfully"
else
    print_error "Failed to delete role assignment (HTTP $HTTP_STATUS)"
fi

# Verify access is revoked
print_info "Verifying access is revoked..."

REVOKE_CHECK=$(curl -s -X POST "$AUTH_API_URL/api/authz/check_access" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": $NEW_USER_ID,
    \"action\": \"view_project\",
    \"resource\": {
      \"type\": \"project\",
      \"id\": \"$PROJECT_ID\",
      \"account_id\": \"$ACCOUNT_ID\",
      \"organization_id\": \"$ORG_ID\"
    }
  }")

REVOKE_ALLOWED=$(echo $REVOKE_CHECK | jq -r '.allowed')
if [ "$REVOKE_ALLOWED" == "false" ]; then
    print_success "Access successfully revoked"
else
    print_error "Access still allowed (unexpected)"
fi
echo $REVOKE_CHECK | jq .

print_section "Demo Complete!"
print_success "All permission management scenarios completed successfully"

