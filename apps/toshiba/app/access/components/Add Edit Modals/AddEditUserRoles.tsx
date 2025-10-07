import { CommonCheckbox } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { type ExtendedUserObject } from "../../../lib/interfaces";
import { updateUserRoles } from "../../../lib/services/userService";
import { AddEditBaseDialog } from "./AddEditBaseDialog";
import "./AddEditUserRoles.scss";

interface AddEditUserRolesProps {
  user: ExtendedUserObject;
  onClose: () => void;
  onSuccess?: () => void;
}

export function AddEditUserRoles(props: AddEditUserRolesProps): JSX.Element {
  const [isApplicationAdmin, setIsApplicationAdmin] = useState(false);
  const [isManager, setIsManager] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // Initialize state with current user roles
  useEffect(() => {
    console.log("Selected user:", props.user);

    // Set initial values based on current user roles
    const currentIsAdmin = (props.user as any)?.application_admin === true;
    const currentIsManager = (props.user as any)?.is_manager === true;

    setIsApplicationAdmin(currentIsAdmin);
    setIsManager(currentIsManager);

    console.log("Current roles - Admin:", currentIsAdmin, "Manager:", currentIsManager);
  }, [props.user]);

  // Check if roles have changed
  useEffect(() => {
    const currentIsAdmin = (props.user as any)?.application_admin === true;
    const currentIsManager = (props.user as any)?.is_manager === true;

    const adminChanged = isApplicationAdmin !== currentIsAdmin;
    const managerChanged = isManager !== currentIsManager;

    setHasChanges(adminChanged || managerChanged);
  }, [isApplicationAdmin, isManager, props.user]);

  async function handleClick(): Promise<void> {
    if (!hasChanges) {
      props.onClose();
      return;
    }

    setIsLoading(true);

    try {
      const result = await updateUserRoles(parseInt(props.user.id), {
        application_admin: isApplicationAdmin,
        is_manager: isManager,
      });

      if (result.success) {
        console.log("Roles updated successfully:", result.message);
        props.onSuccess?.();
        props.onClose();
      } else {
        console.error("Failed to update roles:", result.message);
        // You could add a toast notification here for the error
        alert(`Failed to update roles: ${result.message}`);
      }
    } catch (error) {
      console.error("Error updating user roles:", error);
      alert("An unexpected error occurred while updating roles.");
    } finally {
      setIsLoading(false);
    }
  }

  // Handle role conflicts (optional - prevent both admin and manager being true)
  const handleAdminChange = (value: boolean) => {
    setIsApplicationAdmin(value);
    // If making someone an admin, remove manager role to avoid conflicts
    if (value && isManager) {
      setIsManager(false);
    }
  };

  const handleManagerChange = (value: boolean) => {
    setIsManager(value);
    // If making someone a manager, remove admin role to avoid conflicts
    if (value && isApplicationAdmin) {
      setIsApplicationAdmin(false);
    }
  };

  return (
    <div className="add-edit-user-roles-container">
      <AddEditBaseDialog
        header="Edit User roles"
        subHeader={[props.user.firstname, props.user.lastname]
          .filter(Boolean)
          .join(" ")}
        onClose={props.onClose}
        onClick={handleClick}
        buttonLabel="Apply"
        disabled={!hasChanges}
        loading={isLoading}
      >
        <div className="user-roles-section">
          <h4>User Roles</h4>
          <p className="roles-description">
            Select the appropriate role for this user. Users can have only one role at a time.
          </p>

          <div className="role-options">
            <CommonCheckbox
              label="Toshiba Admin"
              defaultTrue={isApplicationAdmin}
              onChange={handleAdminChange}
              info="Full access to both chatbot and dashboard, plus user management capabilities"
            />

            <CommonCheckbox
              label="Manager"
              defaultTrue={isManager}
              onChange={handleManagerChange}
              info="Access to analytics dashboard only"
            />

            <div className="role-info">
              <small>
                <strong>Field Service Engineer:</strong> Leave both unchecked for chatbot-only access
              </small>
            </div>
          </div>

          {hasChanges && (
            <div className="changes-indicator">
              <small style={{ color: "#ff6b35" }}>
                ⚠️ You have unsaved changes
              </small>
            </div>
          )}
        </div>
      </AddEditBaseDialog>
    </div>
  );
}