import type { ExtendedUserObject } from "../interfaces";

export interface UserActionResult {
  success: boolean;
  message: string;
  error?: string;
}

export interface ResetPasswordData {
  email: string;
  new_password: string;
  is_one_time_password: boolean;
}

export interface UnlockAccountData {
  email: string;
}

class UserActionsService {
  private async makeAuthenticatedRequest(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<Response> {
    const backendUrl = process.env.NEXT_PUBLIC_AUTH_API_URL;
    const tenantId = process.env.NEXT_PUBLIC_AUTH_TENANT_ID ?? "default";

    if (!backendUrl) {
      throw new Error("Auth API URL not configured");
    }

    // Get the auth token from the session
    const response = await fetch("/api/auth/session");
    const session = await response.json();
    const authToken = session?.authToken;

    if (!authToken) {
      throw new Error("No authentication token available");
    }

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      "X-Tenant-ID": tenantId,
      Authorization: `Bearer ${authToken}`,
      ...((options.headers as Record<string, string>) || {}),
    };

    const url = `${backendUrl}/api/auth${endpoint}`;

    return fetch(url, {
      ...options,
      headers,
    });
  }

  async resetUserPassword(
    targetUser: ExtendedUserObject,
    newPassword: string,
    isOneTimePassword: boolean = true
  ): Promise<UserActionResult> {
    try {
      const resetData: ResetPasswordData = {
        email: targetUser.email,
        new_password: newPassword,
        is_one_time_password: isOneTimePassword,
      };
      // console.log("Sending password reset request:", resetData);

      const response = await this.makeAuthenticatedRequest(
        "/admin/reset-password",
        {
          method: "POST",
          body: JSON.stringify(resetData),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const result = await response.json();
      return {
        success: true,
        message: result.message || "Password reset successfully",
      };
    } catch (error) {
      console.error("Failed to reset password:", error);
      return {
        success: false,
        message: "Failed to reset password",
        error: error instanceof Error ? error.message : "Unknown error",
      };
    }
  }

  async unlockUserAccount(
    targetUser: ExtendedUserObject
  ): Promise<UserActionResult> {
    try {
      const response = await this.makeAuthenticatedRequest(
        `/admin/unlock-account?email=${encodeURIComponent(targetUser.email)}`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const result = await response.json();
      return {
        success: true,
        message: result.message || "Account unlocked successfully",
      };
    } catch (error) {
      console.error("Failed to unlock account:", error);
      return {
        success: false,
        message: "Failed to unlock account",
        error: error instanceof Error ? error.message : "Unknown error",
      };
    }
  }

  async getUserMfaDevices(
    targetUser: ExtendedUserObject
  ): Promise<UserActionResult & { devices?: any[] }> {
    try {
      const userId = (targetUser as any).id;
      const response = await this.makeAuthenticatedRequest(
        `/admin/mfa-devices/${userId}`,
        {
          method: "GET",
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const devices = await response.json();
      return {
        success: true,
        message: "MFA devices retrieved successfully",
        devices,
      };
    } catch (error) {
      console.error("Failed to get MFA devices:", error);
      return {
        success: false,
        message: "Failed to retrieve MFA devices",
        error: error instanceof Error ? error.message : "Unknown error",
      };
    }
  }

  async revokeUserMfaDevices(
    targetUser: ExtendedUserObject
  ): Promise<UserActionResult> {
    try {
      const userId = (targetUser as any).id;
      const response = await this.makeAuthenticatedRequest(
        `/admin/revoke-mfa-devices/${userId}`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const result = await response.json();
      return {
        success: true,
        message: result.message || "MFA devices revoked successfully",
      };
    } catch (error) {
      console.error("Failed to revoke MFA devices:", error);
      return {
        success: false,
        message: "Failed to revoke MFA devices",
        error: error instanceof Error ? error.message : "Unknown error",
      };
    }
  }

  async checkUserState(
    targetUser: ExtendedUserObject
  ): Promise<UserActionResult & { state?: any }> {
    try {
      // For now, we'll use the existing user data
      // In the future, this could call a specific endpoint for detailed user state
      const state = {
        isLocked: (targetUser as any).locked_until !== null,
        hasFailedLogins: (targetUser as any).failed_login_attempts > 0,
        isActive: (targetUser as any).status === "active",
        isPasswordTemporary: (targetUser as any).is_password_temporary === true,
        failedLoginAttempts: (targetUser as any).failed_login_attempts || 0,
        lockedUntil: (targetUser as any).locked_until,
      };

      return {
        success: true,
        message: "User state retrieved successfully",
        state,
      };
    } catch (error) {
      console.error("Failed to check user state:", error);
      return {
        success: false,
        message: "Failed to check user state",
        error: error instanceof Error ? error.message : "Unknown error",
      };
    }
  }

  // Generate a secure random password
  // Generate a secure random password that ALWAYS meets backend validation
  generateSecurePassword(length: number = 12): string {
    // Ensure we have at least one of each required type
    const uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    const lowercase = "abcdefghijklmnopqrstuvwxyz";
    const numbers = "0123456789";
    const specialChars = "!@#$%^&*(),.?\":{}|<>";

    // Start with at least one of each required type
    let password = "";
    password += uppercase[Math.floor(Math.random() * uppercase.length)];
    password += lowercase[Math.floor(Math.random() * lowercase.length)];
    password += numbers[Math.floor(Math.random() * numbers.length)];
    password += specialChars[Math.floor(Math.random() * specialChars.length)];

    // Fill the rest randomly from all characters
    const allChars = uppercase + lowercase + numbers + specialChars;
    for (let i = password.length; i < length; i++) {
      password += allChars[Math.floor(Math.random() * allChars.length)];
    }

    // Shuffle the password to randomize position of required characters
    return password.split('').sort(() => Math.random() - 0.5).join('');
  }
}

export const userActionsService = new UserActionsService();
