"use client";

import { useState, useCallback, useMemo } from "react";
import { useSession } from "next-auth/react";
import type { ExtendedUserObject } from "../lib/interfaces";

export interface UserAction {
  id: string;
  label: string;
  icon?: React.ReactNode;
  requiresConfirmation?: boolean;
  confirmationMessage?: string;
  isDestructive?: boolean;
  isLoading?: boolean;
}

export interface UserActionContext {
  targetUser: ExtendedUserObject;
  currentUser: any;
  isCurrentUserSuperuser: boolean;
  isCurrentUserApplicationAdmin: boolean;
  isCurrentUserAnyAdmin: boolean;
}

interface UserState {
  isLocked: boolean;
  hasFailedLogins: boolean;
  isActive: boolean;
  hasMfaDevices: boolean;
  isPasswordTemporary: boolean;
}

interface ActionPermissions {
  canEditNames: boolean;
  canEditRoles: boolean;
  canResetPassword: boolean;
  canUnlockAccount: boolean;
  canViewMfaDevices: boolean;
  canRevokeMfaDevices: boolean;
}

export function useUserActions() {
  const { data: session } = useSession();
  const [loadingStates, setLoadingStates] = useState<Record<string, boolean>>(
    {}
  );
  const [userStatesCache, setUserStatesCache] = useState<
    Record<string, UserState>
  >({});

  const currentUser = session?.user;
  const isCurrentUserSuperuser = (currentUser as any)?.is_superuser === true;
  const isCurrentUserApplicationAdmin =
    (currentUser as any)?.application_admin === true;
  const isCurrentUserAnyAdmin =
    isCurrentUserSuperuser || isCurrentUserApplicationAdmin;

  // Check if user state is cached and still valid (cache for 5 minutes)
  const isUserStateCached = useCallback(
    (userId: string): boolean => {
      return userStatesCache[userId] !== undefined;
    },
    [userStatesCache]
  );

  // Fetch user state from backend
  const fetchUserState = useCallback(
    async (targetUser: ExtendedUserObject): Promise<UserState> => {
      const userId = targetUser.id;

      // Return cached state if available
      if (isUserStateCached(userId)) {
        return userStatesCache[userId];
      }

      try {
        setLoadingStates((prev) => ({ ...prev, [`state_${userId}`]: true }));

        // For now, derive state from the user object
        // In a real implementation, this could call a specific API endpoint
        const userState: UserState = {
          isLocked:
            targetUser.status === "locked" ||
            (targetUser as any).locked_until !== null,
          hasFailedLogins: (targetUser as any).failed_login_attempts > 0,
          isActive: targetUser.status === "active",
          hasMfaDevices: false, // Would need API call to determine
          isPasswordTemporary:
            (targetUser as any).is_password_temporary === true,
        };

        // Cache the state
        setUserStatesCache((prev) => ({
          ...prev,
          [userId]: userState,
        }));

        return userState;
      } catch (error) {
        console.error("Failed to fetch user state:", error);
        // Return default state on error
        return {
          isLocked: false,
          hasFailedLogins: false,
          isActive: true,
          hasMfaDevices: false,
          isPasswordTemporary: false,
        };
      } finally {
        setLoadingStates((prev) => ({ ...prev, [`state_${userId}`]: false }));
      }
    },
    [isUserStateCached, userStatesCache]
  );

  // Determine permissions based on current user role and target user
  const getActionPermissions = useCallback(
    (
      targetUser: ExtendedUserObject,
      userState: UserState
    ): ActionPermissions => {
      const basePermissions: ActionPermissions = {
        canEditNames: false,
        canEditRoles: false,
        canResetPassword: false,
        canUnlockAccount: false,
        canViewMfaDevices: false,
        canRevokeMfaDevices: false,
      };

      if (!isCurrentUserAnyAdmin) {
        return basePermissions;
      }

      // Both superusers and application admins can perform these actions
      if (isCurrentUserAnyAdmin) {
        basePermissions.canEditNames = true;
        basePermissions.canEditRoles = true;
        basePermissions.canResetPassword = true;
        basePermissions.canUnlockAccount = userState.isLocked; // Only show if user is actually locked
      }

      // Superuser-only actions
      if (isCurrentUserSuperuser) {
        basePermissions.canViewMfaDevices = true;
        basePermissions.canRevokeMfaDevices = userState.hasMfaDevices; // Only show if user has MFA devices
      }

      return basePermissions;
    },
    [isCurrentUserAnyAdmin, isCurrentUserSuperuser]
  );

  // Generate dynamic actions based on permissions and user state
  const generateUserActions = useCallback(
    async (targetUser: ExtendedUserObject): Promise<UserAction[]> => {
      const userState = await fetchUserState(targetUser);
      const permissions = getActionPermissions(targetUser, userState);

      const actions: UserAction[] = [];

      if (permissions.canEditNames) {
        actions.push({
          id: "edit-names",
          label: "Edit User Name",
        });
      }

      if (permissions.canEditRoles) {
        actions.push({
          id: "edit-roles",
          label: "Edit User Roles",
        });
      }

      if (permissions.canResetPassword) {
        actions.push({
          id: "reset-password",
          label: "Reset Password",
          requiresConfirmation: true,
          confirmationMessage: `Are you sure you want to reset the password for ${targetUser.email}?`,
          isDestructive: true,
        });
      }

      if (permissions.canUnlockAccount) {
        actions.push({
          id: "unlock-account",
          label: "Unlock Account",
          requiresConfirmation: true,
          confirmationMessage: `Are you sure you want to unlock the account for ${targetUser.email}?`,
        });
      }

      if (permissions.canViewMfaDevices) {
        actions.push({
          id: "view-mfa-devices",
          label: "View MFA Devices",
        });
      }

      if (permissions.canRevokeMfaDevices) {
        actions.push({
          id: "revoke-mfa-devices",
          label: "Revoke MFA Devices",
          requiresConfirmation: true,
          confirmationMessage: `Are you sure you want to revoke all MFA devices for ${targetUser.email}?`,
          isDestructive: true,
        });
      }

      return actions;
    },
    [fetchUserState, getActionPermissions]
  );

  // Clear cache for a specific user (useful after performing actions)
  const clearUserStateCache = useCallback((userId: string) => {
    setUserStatesCache((prev) => {
      const newCache = { ...prev };
      delete newCache[userId];
      return newCache;
    });
  }, []);

  // Clear all cache
  const clearAllCache = useCallback(() => {
    setUserStatesCache({});
  }, []);

  return {
    generateUserActions,
    loadingStates,
    clearUserStateCache,
    clearAllCache,
    isCurrentUserSuperuser,
    isCurrentUserApplicationAdmin,
    isCurrentUserAnyAdmin,
  };
}
