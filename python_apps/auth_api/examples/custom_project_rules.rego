package rbac

import rego.v1

# ============================================================================
# CUSTOM PROJECT-SPECIFIC RULES
# Example: Only project owners can delete projects
# ============================================================================

# Project owner can do anything
role_check(assignment) if {
    assignment.role == "owner"
    input.resource.type == "project"
    input.resource.id == assignment.resource_id
    # Owner can do any action
}

# Only owners can delete projects
role_check(assignment) if {
    assignment.role == "owner"
    input.resource.type == "project"
    input.action == "delete_project"
    input.resource.id == assignment.resource_id
}

# Prevent non-owners from deleting (explicit deny)
deny_reason := "only_owner_can_delete" if {
    input.action == "delete_project"
    input.resource.type == "project"
    not some assignment in input.user.assignments
    assignment.role == "owner"
    assignment.resource_id == input.resource.id
}

# ============================================================================
# TIME-BASED ACCESS RULES
# Example: Temporary access that expires
# ============================================================================

# Check if assignment has expired
assignment_is_valid(assignment) if {
    # If no expiry, always valid
    not assignment.expires_at
}

assignment_is_valid(assignment) if {
    # If has expiry, check if still valid
    assignment.expires_at
    time.now_ns() < time.parse_rfc3339_ns(assignment.expires_at)
}

# Only allow if assignment hasn't expired
role_check(assignment) if {
    assignment.role == "temp_editor"
    input.resource.type == "project"
    input.action in {"edit_project", "view_project"}
    assignment_is_valid(assignment)
}

# ============================================================================
# ATTRIBUTE-BASED RULES
# Example: Department-based access
# ============================================================================

# Users can only access projects in their department
valid_resource_match(assignment) if {
    assignment.resource_type == "project"
    input.resource.id == assignment.resource_id
    # Check department match
    input.user.department == input.resource.department
}

# ============================================================================
# USER-SPECIFIC OVERRIDES
# Example: Specific user gets special permissions
# ============================================================================

# Specific user bypass (for emergencies or special cases)
allow if {
    input.user.id == 999  # Emergency admin user
    input.user.status == "active"
}

# Specific user can access specific project
role_check(assignment) if {
    input.user.id == 42  # Specific user ID
    input.resource.type == "project"
    input.resource.id == "special-project-123"
    input.action in {"view_project", "edit_project"}
}

# ============================================================================
# CONDITIONAL RULES
# Example: Different rules based on resource state
# ============================================================================

# Archived projects are read-only for everyone except admins
role_check(assignment) if {
    input.resource.type == "project"
    input.resource.status == "archived"
    assignment.role == "admin"
    # Admins can still edit archived projects
}

role_check(assignment) if {
    input.resource.type == "project"
    input.resource.status == "archived"
    assignment.role in {"editor", "viewer"}
    input.action == "view_project"  # Only view for non-admins
}

# Active projects follow normal rules
role_check(assignment) if {
    input.resource.type == "project"
    input.resource.status == "active"
    assignment.role == "editor"
    input.action in {"edit_project", "view_project"}
}

