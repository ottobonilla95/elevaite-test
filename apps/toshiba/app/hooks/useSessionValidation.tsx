"use client";

import { useEffect, useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { signOut } from "next-auth/react";

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
  const router = useRouter();
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
      // Get the session data from localStorage if available
      // This is where next-auth stores the session data including the refresh token
      let refreshToken = "";
      try {
        const sessionData = localStorage.getItem("next-auth.session-token");
        if (sessionData) {
          // Try to extract refresh token from session data if it's stored there
          refreshToken = sessionData;
        }
      } catch (error) {
        // Fail silently
      }

      // Call the server action to validate the session
      const response = await fetch("/api/auth/validate-session", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Refresh-Token": refreshToken || "",
        },
      });

      if (!response.ok) {
        // Only log out if we get a 401 Unauthorized
        if (response.status === 401) {
          await signOut({ callbackUrl: "/login" });
          return false;
        }
        return true; // For other errors, assume valid to prevent excessive logouts
      }

      const data = (await response.json()) as {
        valid: boolean;
        reason?: string;
      };

      if (!data.valid) {
        // Only log out for certain reasons
        if (
          data.reason === "session_invalidated" ||
          data.reason === "user_not_found"
        ) {
          await signOut({ callbackUrl: "/login" });
          return false;
        }
        return true; // For other reasons, assume valid
      }

      return true;
    } catch (error) {
      return true; // Assume valid on error to prevent excessive logouts
    } finally {
      setIsValidating(false);
    }
  }, [router, isValidating]);

  // Validate session on user interaction
  useEffect(() => {
    // Add event listeners for user interactions
    const handleUserInteraction = (): void => {
      // Debounce to prevent too many calls
      if (window.sessionValidationTimeout) {
        clearTimeout(window.sessionValidationTimeout);
      }

      window.sessionValidationTimeout = setTimeout(() => {
        void checkSession(); // void operator to explicitly ignore the Promise
      }, 1000); // 1 second debounce
    };

    // Add event listeners
    document.addEventListener("click", handleUserInteraction);
    document.addEventListener("keydown", handleUserInteraction);

    // Set up periodic validation (every minute), but delay the first check
    // to avoid immediate validation after login
    const initialDelay = setTimeout(() => {
      // Set up the interval after the initial delay
      const intervalId = setInterval(() => {
        void checkSession(); // void operator to explicitly ignore the Promise
      }, 60000); // Check every minute

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
  }, [checkSession]);

  return { checkSession };
}
