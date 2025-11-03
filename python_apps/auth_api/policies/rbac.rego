# https://www.openpolicyagent.org/docs/latest/faq/#how-do-i-write-policies-securely

package rbac

import rego.v1

default allow := false

# ============================================================================
# PERMISSION OVERRIDES (Highest Priority)
# ============================================================================
# Permission overrides allow fine-grained control beyond role-based permissions.
# Deny takes precedence over allow (security best practice).

# Explicit deny - if action is in deny list, deny immediately
deny if {
	input.user.overrides
	input.action in input.user.overrides.deny
}

# Explicit allow - if action is in allow list and not denied, allow
allow if {
	not deny
	input.user.overrides
	input.action in input.user.overrides.allow
}

# ============================================================================
# ROLE-BASED ACCESS CONTROL (Fallback)
# ============================================================================
# If no overrides apply, fall back to role-based permissions

allow if {
	not deny
	not input.user.overrides
	some assignment in input.user.assignments
	valid_resource_match(assignment)
	role_check(assignment)
}

# Also allow role-based access if overrides exist but don't cover this action
allow if {
	not deny
	input.user.overrides
	not input.action in input.user.overrides.allow
	not input.action in input.user.overrides.deny
	some assignment in input.user.assignments
	valid_resource_match(assignment)
	role_check(assignment)
}

valid_resource_match(assignment) if {
	assignment.role == "superadmin"
	assignment.resource_type == "organization"
	assignment.resource_id == input.resource.organization_id
}

valid_resource_match(assignment) if {
	assignment.role == "admin"
	assignment.resource_type == "account"
	assignment.resource_id == input.resource.account_id
}

valid_resource_match(assignment) if {
	assignment.role != "superadmin"
	assignment.role != "admin"
	assignment.resource_type == "project"
	input.resource.id == assignment.resource_id
}

role_check(assignment) if {
	assignment.role == "superadmin"
}

role_check(assignment) if {
	assignment.role == "admin"
	input.resource.type in {"account", "project"}
	input.action in {"manage_account", "edit_project", "view_project"}
}

role_check(assignment) if {
	assignment.role == "editor"
	input.resource.type == "project"
	input.action in {"edit_project", "view_project"}
}

role_check(assignment) if {
	assignment.role == "viewer"
	input.resource.type == "project"
	input.action == "view_project"
}
