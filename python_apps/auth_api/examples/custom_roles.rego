package rbac

import rego.v1

# ============================================================================
# CUSTOM ROLE EXAMPLES
# Add these to your rbac.rego or upload as a separate policy module
# ============================================================================

# ----------------------------------------------------------------------------
# Example 1: ANALYST ROLE
# Can view and export data, but not edit
# ----------------------------------------------------------------------------

role_check(assignment) if {
    assignment.role == "analyst"
    input.resource.type == "project"
    input.action in {"view_project", "export_data", "view_reports"}
}

# ----------------------------------------------------------------------------
# Example 2: CONTRIBUTOR ROLE
# Can create and edit their own content, but not delete
# ----------------------------------------------------------------------------

role_check(assignment) if {
    assignment.role == "contributor"
    input.resource.type == "project"
    input.action in {"create_content", "edit_own_content", "view_project"}
}

# Contributor can only edit their own content
role_check(assignment) if {
    assignment.role == "contributor"
    input.resource.type == "content"
    input.action == "edit_content"
    input.resource.owner_id == input.user.id  # Must own the content
}

# ----------------------------------------------------------------------------
# Example 3: REVIEWER ROLE
# Can view and comment, but not edit
# ----------------------------------------------------------------------------

role_check(assignment) if {
    assignment.role == "reviewer"
    input.resource.type == "project"
    input.action in {"view_project", "add_comment", "approve", "reject"}
}

# ----------------------------------------------------------------------------
# Example 4: BILLING_ADMIN ROLE
# Can manage billing but nothing else
# ----------------------------------------------------------------------------

role_check(assignment) if {
    assignment.role == "billing_admin"
    input.resource.type == "account"
    input.action in {
        "view_billing",
        "update_payment_method",
        "view_invoices",
        "download_invoices"
    }
}

# ----------------------------------------------------------------------------
# Example 5: SUPPORT ROLE
# Read-only access to everything for customer support
# ----------------------------------------------------------------------------

role_check(assignment) if {
    assignment.role == "support"
    input.resource.type in {"project", "account", "workflow", "agent"}
    input.action in {"view_project", "view_account", "view_workflow", "view_agent"}
}

# Support can also view user information
role_check(assignment) if {
    assignment.role == "support"
    input.resource.type == "user"
    input.action in {"view_user", "view_activity_log"}
}

# ----------------------------------------------------------------------------
# Example 6: DEVELOPER ROLE
# Can manage workflows and agents, but not account settings
# ----------------------------------------------------------------------------

role_check(assignment) if {
    assignment.role == "developer"
    input.resource.type in {"workflow", "agent"}
    input.action in {
        "create_workflow",
        "edit_workflow",
        "view_workflow",
        "delete_workflow",
        "create_agent",
        "edit_agent",
        "view_agent",
        "delete_agent",
        "execute_workflow",
        "test_agent"
    }
}

# ----------------------------------------------------------------------------
# Example 7: AUDITOR ROLE
# Read-only access with special audit permissions
# ----------------------------------------------------------------------------

role_check(assignment) if {
    assignment.role == "auditor"
    input.resource.type in {"project", "account", "organization"}
    input.action in {
        "view_project",
        "view_account",
        "view_organization",
        "view_audit_log",
        "export_audit_log",
        "view_all_activity"
    }
}

# ----------------------------------------------------------------------------
# Example 8: GUEST ROLE
# Very limited access, can only view specific resources
# ----------------------------------------------------------------------------

role_check(assignment) if {
    assignment.role == "guest"
    input.resource.type == "project"
    input.action == "view_project"
    # Guests can only view, nothing else
}

# ----------------------------------------------------------------------------
# Example 9: OWNER ROLE
# Full control over a specific resource
# ----------------------------------------------------------------------------

role_check(assignment) if {
    assignment.role == "owner"
    input.resource.type == "project"
    input.resource.id == assignment.resource_id
    # Owner can do anything
}

# ----------------------------------------------------------------------------
# Example 10: TEAM_LEAD ROLE
# Can manage team members and assign roles
# ----------------------------------------------------------------------------

role_check(assignment) if {
    assignment.role == "team_lead"
    input.resource.type == "project"
    input.action in {
        "view_project",
        "edit_project",
        "add_team_member",
        "remove_team_member",
        "assign_roles",
        "view_team"
    }
}

# ----------------------------------------------------------------------------
# Example 11: DATA_SCIENTIST ROLE
# Can access data and run experiments
# ----------------------------------------------------------------------------

role_check(assignment) if {
    assignment.role == "data_scientist"
    input.resource.type == "project"
    input.action in {
        "view_project",
        "view_data",
        "export_data",
        "run_experiment",
        "create_model",
        "view_results"
    }
}

# ----------------------------------------------------------------------------
# Example 12: CUSTOM ROLE WITH MULTIPLE RESOURCE TYPES
# ----------------------------------------------------------------------------

role_check(assignment) if {
    assignment.role == "workflow_manager"
    input.resource.type == "workflow"
    input.action in {
        "create_workflow",
        "edit_workflow",
        "view_workflow",
        "delete_workflow",
        "execute_workflow",
        "schedule_workflow"
    }
}

role_check(assignment) if {
    assignment.role == "workflow_manager"
    input.resource.type == "agent"
    input.action in {"view_agent", "execute_agent"}
}

# ----------------------------------------------------------------------------
# Example 13: CONDITIONAL ROLE
# Role with additional conditions
# ----------------------------------------------------------------------------

role_check(assignment) if {
    assignment.role == "premium_user"
    input.resource.type == "project"
    # Check if user has premium subscription
    input.user.subscription_tier == "premium"
    input.action in {
        "view_project",
        "edit_project",
        "use_premium_features",
        "access_advanced_analytics"
    }
}

# ----------------------------------------------------------------------------
# Example 14: TIME-LIMITED ROLE
# Role that expires
# ----------------------------------------------------------------------------

role_check(assignment) if {
    assignment.role == "temp_contractor"
    input.resource.type == "project"
    input.action in {"view_project", "edit_project"}
    # Check if assignment hasn't expired
    assignment.expires_at
    time.now_ns() < time.parse_rfc3339_ns(assignment.expires_at)
}

# ----------------------------------------------------------------------------
# Example 15: HIERARCHICAL ROLE
# Role that inherits from another role
# ----------------------------------------------------------------------------

# Senior developer has all developer permissions plus more
role_check(assignment) if {
    assignment.role == "senior_developer"
    input.resource.type in {"workflow", "agent"}
    input.action in {
        # All developer actions
        "create_workflow", "edit_workflow", "view_workflow", "delete_workflow",
        "create_agent", "edit_agent", "view_agent", "delete_agent",
        # Plus senior-only actions
        "deploy_to_production",
        "manage_api_keys",
        "configure_integrations"
    }
}

