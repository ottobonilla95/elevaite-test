"use client";

import { useEffect, useCallback, useState } from "react";
import { redirect } from "next/navigation";

// Define a global variable to store the timeout ID
declare global {
  interface Window {
    sessionValidationTimeout?: ReturnType<typeof setTimeout>;
    sessionValidationIntervalId?: ReturnType<typeof setInterval>;
    lastSessionValidation?: number;
  }
}

/**
 * Hook to validate the session on user interactions
 */
export function useSessionValidation(): {
  checkSession: () => Promise<boolean>;
} {
  const [isValidating, setIsValidating] = useState(false);

  const checkSession = useCallback(async (): Promise<boolean> => {
    // Prevent multiple simultaneous validations
    if (isValidating) return true; // Assume valid if already validating

    // Don't validate too frequently (at most once per minute)
    const now = Date.now();
    if (
      window.lastSessionValidation &&
      now - window.lastSessionValidation < 60000
    ) {
      return true; // Assume valid if validated recently
    }

    // Skip validation if we're on authentication-related pages
    // This is critical for the reset-password page to work properly
    if (
      window.location.pathname === "/login" ||
      window.location.pathname === "/reset-password" ||
      window.location.pathname.includes("/reset-password") ||
      window.location.pathname === "/forgot-password" ||
      window.location.pathname.includes("/forgot-password")
    ) {
      return true; // Assume valid on auth pages
    }

    // Also skip validation if we're in the process of resetting a password
    // This is determined by checking if we're on a page with a reset token
    if (window.location.search.includes("token=")) {
      return true; // Assume valid on reset token pages
    }

    setIsValidating(true);
    window.lastSessionValidation = now;

    try {
      let accessToken = "";
      let refreshToken = "";

      try {
        const sessionResponse = await fetch("/api/auth/session");
        if (sessionResponse.ok) {
          const sessionData = (await sessionResponse.json()) as {
            authToken?: string;
            user?: {
              refreshToken?: string;
            };
          };
          accessToken = sessionData.authToken ?? "";
          refreshToken = sessionData.user?.refreshToken ?? "";
        }
      } catch (error) {
        // Fail silently - we'll proceed without tokens
      }

      if (!accessToken) {
        return false;
      }

      const authApiUrl =
        process.env.NEXT_PUBLIC_AUTH_API_URL || "http://localhost:8004";
      const tenantId = process.env.NEXT_PUBLIC_AUTH_TENANT_ID || "default";

      const headers: Record<string, string> = {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
        "X-Tenant-ID": tenantId,
      };

      // Add refresh token header if we have one
      if (refreshToken) {
        headers["X-Refresh-Token"] = refreshToken;
      }

      const response = await fetch(`${authApiUrl}/api/auth/validate-session`, {
        headers,
      });

      if (!response.ok) {
        // Only log out if we get a 401 Unauthorized
        if (response.status === 401) {
           redirect("/login");
           return false;
        }
        return true; // For other errors, assume valid to prevent excessive logouts
      }

      const data = (await response.json()) as {
        valid: boolean;
        reason?: string;
        user_id?: number;
        email?: string;
        is_password_temporary?: boolean;
      };

      if (!data.valid) {
        if (
          data.reason === "session_invalidated" ||
          data.reason === "user_not_found" ||
          data.reason === "user_inactive"
        ) {
          redirect("/login");
 	  return false;
        }
        return true; // For other reasons, assume valid to prevent excessive logouts
      }

      return true;
    } catch (error) {
      return true; // Assume valid on error to prevent excessive logouts
    } finally {
      setIsValidating(false);
    }
  }, []);

  // Validate session on user interaction
  useEffect(() => {
    // Add event listeners for user interactions
    const handleUserInteraction = (): void => {
      // Debounce to prevent too many calls
      if (window.sessionValidationTimeout) {
        clearTimeout(window.sessionValidationTimeout);
      }

      window.sessionValidationTimeout = setTimeout(() => {
        void checkSession();
      }, 5000);
    };

    // Add event listeners
    document.addEventListener("click", handleUserInteraction);
    document.addEventListener("keydown", handleUserInteraction);

    const initialDelay = setTimeout(() => {
      // Set up the interval after the initial delay
      const intervalId = setInterval(() => {
        void checkSession();
      }, 300000); // Check every 5 minutes

      // Store the interval ID so we can clear it on cleanup
      window.sessionValidationIntervalId = intervalId;
    }, 30000); // 30 second initial delay

    return () => {
      // Clean up
      document.removeEventListener("click", handleUserInteraction);
      document.removeEventListener("keydown", handleUserInteraction);
      clearTimeout(initialDelay);

      if (window.sessionValidationIntervalId) {
        clearInterval(window.sessionValidationIntervalId);
      }

      if (window.sessionValidationTimeout) {
        clearTimeout(window.sessionValidationTimeout);
      }
    };
  }, []);

  return { checkSession };
}
