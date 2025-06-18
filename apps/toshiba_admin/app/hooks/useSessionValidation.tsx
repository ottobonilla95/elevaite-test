"use client";

import { useEffect, useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { signOut } from "next-auth/react";

// Define a global variable to store the timeout ID
declare global {
  interface Window {
    sessionValidationTimeout?: NodeJS.Timeout;
    sessionValidationIntervalId?: NodeJS.Timeout;
    lastSessionValidation?: number;
  }
}

/**
 * Hook to validate the session on user interactions
 */
export function useSessionValidation() {
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
      console.log(
        "Skipping session validation on auth page:",
        window.location.pathname
      );
      return true; // Assume valid on auth pages
    }

    // Also skip validation if we're in the process of resetting a password
    // This is determined by checking if we're on a page with a reset token
    if (window.location.search.includes("token=")) {
      console.log(
        "Skipping session validation on page with reset token:",
        window.location.pathname + window.location.search
      );
      return true; // Assume valid on reset token pages
    }

    setIsValidating(true);
    window.lastSessionValidation = now;

    try {
      console.log("Validating session...");

      // Get the current session to extract tokens
      // We need to call the session endpoint to get the current session data
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
        console.error("Error getting session data:", error);
      }

      // Call the server action to validate the session
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };

      // Add Authorization header if we have an access token
      if (accessToken) {
        headers.Authorization = `Bearer ${accessToken}`;
      }

      // Add refresh token header if we have one
      if (refreshToken) {
        headers["X-Refresh-Token"] = refreshToken;
      }

      const response = await fetch("/api/auth/validate-session", {
        method: "POST",
        headers,
      });

      if (!response.ok) {
        console.error(
          "Session validation failed with status:",
          response.status
        );

        // Only log out if we get a 401 Unauthorized
        if (response.status === 401) {
          console.log("Unauthorized response, logging out");
          await signOut({ callbackUrl: "/login" });
          return false;
        }
        return true; // For other errors, assume valid to prevent excessive logouts
      }

      const data = (await response.json()) as {
        valid: boolean;
        reason?: string;
      };
      console.log("Session validation response:", data);

      if (!data.valid) {
        console.log("Session is invalid, reason:", data.reason);

        // Only log out for certain reasons
        if (
          data.reason === "session_invalidated" ||
          data.reason === "user_not_found"
        ) {
          console.log("Session invalidated or user not found, logging out");
          await signOut({ callbackUrl: "/login" });
          return false;
        }
        return true; // For other reasons, assume valid
      }

      console.log("Session is valid");
      return true;
    } catch (error) {
      console.error("Error validating session:", error);
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
