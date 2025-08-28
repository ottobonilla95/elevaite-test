"use client";

import React, { useState, useEffect, useCallback } from "react";
import { CommonMenuItem } from "@repo/ui/components";
import { useUserActions, type UserAction } from "../../hooks/useUserActions";
import { userActionsService } from "../../lib/services/userActionsService";
import type { ExtendedUserObject } from "../../lib/interfaces";

interface DynamicUserMenuProps {
  targetUser: ExtendedUserObject;
  onActionExecuted: (actionId: string, success: boolean, message: string) => void;
  onEditNames: (user: ExtendedUserObject) => void;
  onEditRoles: (user: ExtendedUserObject) => void;
}

export function DynamicUserMenu({
  targetUser,
  onActionExecuted,
  onEditNames,
  onEditRoles,
}: DynamicUserMenuProps): {
  menuItems: CommonMenuItem<ExtendedUserObject>[];
  isLoading: boolean;
} {
  const { generateUserActions, loadingStates, clearUserStateCache } = useUserActions();
  const [actions, setActions] = useState<UserAction[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [executingActions, setExecutingActions] = useState<Set<string>>(new Set());

  // Load actions when component mounts or user changes
  useEffect(() => {
    loadActions();
  }, [targetUser.id]);

  const loadActions = useCallback(async () => {
    setIsLoading(true);
    try {
      const userActions = await generateUserActions(targetUser);
      setActions(userActions);
    } catch (error) {
      console.error("Failed to load user actions:", error);
      setActions([]);
    } finally {
      setIsLoading(false);
    }
  }, [generateUserActions, targetUser]);

  const executeAction = useCallback(async (actionId: string) => {
    if (executingActions.has(actionId)) {
      return; // Already executing
    }

    setExecutingActions(prev => new Set(prev).add(actionId));

    try {
      let result;
      
      switch (actionId) {
        case "edit-names":
          onEditNames(targetUser);
          onActionExecuted(actionId, true, "Edit names dialog opened");
          return;

        case "edit-roles":
          onEditRoles(targetUser);
          onActionExecuted(actionId, true, "Edit roles dialog opened");
          return;

        case "reset-password":
          const newPassword = userActionsService.generateSecurePassword();
          result = await userActionsService.resetUserPassword(targetUser, newPassword, true);
          break;

        case "unlock-account":
          result = await userActionsService.unlockUserAccount(targetUser);
          break;

        case "view-mfa-devices":
          result = await userActionsService.getUserMfaDevices(targetUser);
          if (result.success && (result as any).devices) {
            console.log("MFA Devices:", (result as any).devices);
            // In a real implementation, you might open a modal to display the devices
          }
          break;

        case "revoke-mfa-devices":
          result = await userActionsService.revokeUserMfaDevices(targetUser);
          break;

        default:
          result = {
            success: false,
            message: `Unknown action: ${actionId}`,
          };
      }

      if (result) {
        onActionExecuted(actionId, result.success, result.message);
        
        if (result.success) {
          // Clear cache and reload actions to reflect any state changes
          clearUserStateCache(targetUser.id);
          await loadActions();
        }
      }
    } catch (error) {
      console.error(`Failed to execute action ${actionId}:`, error);
      onActionExecuted(
        actionId,
        false,
        `Failed to execute ${actionId}: ${error instanceof Error ? error.message : "Unknown error"}`
      );
    } finally {
      setExecutingActions(prev => {
        const newSet = new Set(prev);
        newSet.delete(actionId);
        return newSet;
      });
    }
  }, [executingActions, targetUser, onActionExecuted, onEditNames, onEditRoles, clearUserStateCache, loadActions]);

  const handleActionClick = useCallback(async (action: UserAction) => {
    if (action.requiresConfirmation) {
      const confirmed = window.confirm(
        action.confirmationMessage || `Are you sure you want to ${action.label.toLowerCase()}?`
      );
      
      if (!confirmed) {
        return;
      }
    }

    await executeAction(action.id);
  }, [executeAction]);

  // Convert actions to CommonMenuItem format
  const menuItems: CommonMenuItem<ExtendedUserObject>[] = actions.map((action) => ({
    label: action.label,
    onClick: () => handleActionClick(action),
    disabled: executingActions.has(action.id) || loadingStates[`state_${targetUser.id}`],
    className: action.isDestructive ? "destructive-action" : undefined,
  }));

  return {
    menuItems,
    isLoading: isLoading || loadingStates[`state_${targetUser.id}`] || false,
  };
}
