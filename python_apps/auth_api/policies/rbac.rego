# https://www.openpolicyagent.org/docs/latest/faq/#how-do-i-write-policies-securely

package rbac

import rego.v1

default allow := false

# ============================================================================
# PERMISSION PRECEDENCE (Role-Ceiling Model)
# ============================================================================
# 1. User-level permission overrides (deny takes precedence over allow)
# 2. Role permissions set the ceiling (maximum permissions)
# 3. Group denials can restrict role permissions (never expand)
#
# Formula: effective_permissions = role_permissions - user_denies - group_denials

# ============================================================================
# DENY RULES (Evaluated First)
# ============================================================================

# User-level explicit deny (highest priority deny)
deny if {
	input.user.overrides
	input.action in input.user.overrides.deny
}

# Group-level deny - restricts role permissions
# Groups can only deny actions, they cannot grant new permissions
deny_by_group if {
	some membership in input.user.group_memberships
	valid_group_resource_match(membership)
	some group_permission in membership.permissions
	group_permission.service_name == input.service
	input.action in group_permission.deny_actions
}

# ============================================================================
# ALLOW RULES
# ============================================================================

# User-level explicit allow (bypasses role check, but not deny)
allow if {
	not deny
	not deny_by_group
	input.user.overrides
	input.action in input.user.overrides.allow
}

# Role-based allow with group restrictions
# Role permissions set the ceiling, groups can only restrict
allow if {
	not deny
	not deny_by_group
	role_allows_action
}

# ============================================================================
# ROLE PERMISSION EVALUATION
# ============================================================================

# Check if any role assignment grants the action
role_allows_action if {
	some assignment in input.user.assignments
	valid_resource_match(assignment)
	role_grants_action(assignment)
}

# Role grants action via role_permissions from database
role_grants_action(assignment) if {
	some role_permission in assignment.role_permissions
	role_permission.service_name == input.service
	action_in_allowed(input.action, role_permission.allowed_actions)
}

# Legacy role check (fallback for assignments without role_permissions)
role_grants_action(assignment) if {
	not assignment.role_permissions
	legacy_role_check(assignment)
}

# Check if action is in allowed list (supports wildcard "*")
action_in_allowed(action, allowed) if {
	"*" in allowed
}

action_in_allowed(action, allowed) if {
	action in allowed
}

# ============================================================================
# RESOURCE MATCHING
# ============================================================================

# Organization-level assignment matches organization resource
valid_resource_match(assignment) if {
	assignment.resource_type == "organization"
	assignment.resource_id == input.resource.organization_id
}

# Account-level assignment matches account or child project
valid_resource_match(assignment) if {
	assignment.resource_type == "account"
	assignment.resource_id == input.resource.account_id
}

# Project-level assignment matches specific project
valid_resource_match(assignment) if {
	assignment.resource_type == "project"
	assignment.resource_id == input.resource.id
}

# Group membership resource matching
valid_group_resource_match(membership) if {
	membership.resource_type == "organization"
	membership.resource_id == input.resource.organization_id
}

valid_group_resource_match(membership) if {
	membership.resource_type == "account"
	membership.resource_id == input.resource.account_id
}

valid_group_resource_match(membership) if {
	membership.resource_type == "project"
	membership.resource_id == input.resource.id
}

# ============================================================================
# LEGACY ROLE SUPPORT (Backward Compatibility)
# ============================================================================
# Supports old-style role assignments without role_permissions

legacy_role_check(assignment) if {
	assignment.role == "superadmin"
}

legacy_role_check(assignment) if {
	assignment.role == "admin"
	input.resource.type in {"account", "project"}
	input.action in {"manage_account", "edit_project", "view_project"}
}

legacy_role_check(assignment) if {
	assignment.role == "editor"
	input.resource.type == "project"
	input.action in {"edit_project", "view_project"}
}

legacy_role_check(assignment) if {
	assignment.role == "viewer"
	input.resource.type == "project"
	input.action == "view_project"
}
