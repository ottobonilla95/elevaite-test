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

  // Store original values to show current status
  const [originalIsAdmin, setOriginalIsAdmin] = useState(false);
  const [originalIsManager, setOriginalIsManager] = useState(false);

  // Initialize state with current user roles
  useEffect(() => {
    console.log("Selected user:", props.user);

    const currentIsAdmin = (props.user as any)?.application_admin === true;
    const currentIsManager = (props.user as any)?.is_manager === true;

    // Set both current state and original values
    setIsApplicationAdmin(currentIsAdmin);
    setIsManager(currentIsManager);
    setOriginalIsAdmin(currentIsAdmin);
    setOriginalIsManager(currentIsManager);

    console.log("Current roles - Admin:", currentIsAdmin, "Manager:", currentIsManager);
  }, [props.user]);

  // Check if roles have changed
  useEffect(() => {
    const adminChanged = isApplicationAdmin !== originalIsAdmin;
    const managerChanged = isManager !== originalIsManager;

    setHasChanges(adminChanged || managerChanged);
  }, [isApplicationAdmin, isManager, originalIsAdmin, originalIsManager]);

  // Get current role name for display
  const getCurrentRole = (): string => {
    if (originalIsAdmin) return "Toshiba Admin";
    if (originalIsManager) return "Manager";
    return "Field Service Engineer";
  };

  // Get new role name for display (when changes are made)
  const getNewRole = (): string => {
    if (isApplicationAdmin) return "Toshiba Admin";
    if (isManager) return "Manager";
    return "Field Service Engineer";
  };

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
        alert(`Failed to update roles: ${result.message}`);
      }
    } catch (error) {
      console.error("Error updating user roles:", error);
      alert("An unexpected error occurred while updating roles.");
    } finally {
      setIsLoading(false);
    }
  }

  const handleAdminChange = (value: boolean) => {
    setIsApplicationAdmin(value);
    if (value && isManager) {
      setIsManager(false);
    }
  };

  const handleManagerChange = (value: boolean) => {
    setIsManager(value);
    if (value && isApplicationAdmin) {
      setIsApplicationAdmin(false);
    }
  };

  return (
    <div className="add-edit-user-roles-container">
      <AddEditBaseDialog
        header="Edit User Roles"
        subHeader={[props.user.firstname, props.user.lastname]
          .filter(Boolean)
          .join(" ")}
        onClose={props.onClose}
        onClick={handleClick}
        buttonLabel="Apply Changes"
        disabled={!hasChanges}
        loading={isLoading}
      >
        <div className="user-roles-section">

          <div className="current-role-status">
            <strong>Current Role:</strong>{" "}
            <span className="role-badge current">{getCurrentRole()}</span>
          </div>

          <h4>Select New Role</h4>
          <p className="roles-description">
            Select the appropriate role for this user. Users can have only one role at a time.
          </p>

          <div className="role-options">
            <CommonCheckbox
              label="Toshiba Admin"
              checked={isApplicationAdmin}
              onChange={handleAdminChange}
              info="Full access to both chatbot and dashboard, plus user management capabilities"
            />

            <CommonCheckbox
              label="Manager"
              checked={isManager}
              onChange={handleManagerChange}
              info="Access to analytics dashboard only"
            />

            <div className="role-info">
              <small>
                <strong>Field Service Engineer:</strong> Leave both unchecked for chatbot-only access
              </small>
            </div>
          </div>
        </div>
      </AddEditBaseDialog>
    </div>
  );
}