"use client";

import { useEffect, useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { signOut } from "next-auth/react";
import { safeRedirect } from "../lib/urlUtils";

// Define a global variable to store the timeout ID
declare global {
  interface Window {
    sessionValidationTimeout?: ReturnType<typeof setTimeout>;
    sessionValidationIntervalId?: ReturnType<typeof setInterval>;
    lastSessionValidation?: number;
    isLoggingOut?: boolean; // Add flag to prevent multiple logout attempts
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

  // Enhanced logout function with reliable redirect
  const handleLogout = useCallback(
    async (reason?: string) => {
      // Prevent multiple logout attempts
      if (window.isLoggingOut) {
        return;
      }
      window.isLoggingOut = true;

      try {
        console.info(`Session ended${reason ? `: ${reason}` : ""}`);

        // Clear any client-side storage immediately
        if (typeof window !== "undefined") {
          try {
            localStorage.clear();
            sessionStorage.clear();
          } catch (e) {
            console.warn("Error clearing storage:", e);
          }
        }

        // Try NextAuth signOut first
        try {
          await signOut({ redirect: false }); // Don't let NextAuth handle redirect
        } catch (signOutError) {
          console.warn("NextAuth signOut failed:", signOutError);
        }

        // Force redirect to login page - multiple fallback methods
        try {
          router.push("/login");

          // Backup redirect in case router.push fails
          setTimeout(() => {
            if (window.location.pathname !== "/login") {
              safeRedirect("/login");
            }
          }, 500);
        } catch (routerError) {
          console.warn(
            "Router redirect failed, using safe redirect:",
            routerError
          );
          safeRedirect("/login");
        }
      } catch (error) {
        console.error("Error during logout:", error);
        // Ultimate fallback: force page reload to login
        safeRedirect("/login");
      } finally {
        // Reset the logout flag after a delay
        setTimeout(() => {
          window.isLoggingOut = false;
        }, 2000);
      }
    },
    [router]
  );

  const checkSession = useCallback(async (): Promise<boolean> => {
    // Prevent multiple simultaneous validations
    if (isValidating || window.isLoggingOut) return true;

    // Don't validate too frequently (at most once per minute)
    const now = Date.now();
    if (
      window.lastSessionValidation &&
      now - window.lastSessionValidation < 60000
    ) {
      return true; // Assume valid if validated recently
    }

    // Skip validation if we're on authentication-related pages
    const currentPath = window.location.pathname;
    const authPaths = ["/login", "/reset-password", "/forgot-password"];

    if (
      authPaths.some(
        (path) => currentPath === path || currentPath.includes(path)
      )
    ) {
      return true; // Assume valid on auth pages
    }

    // Also skip validation if we're in the process of resetting a password
    if (window.location.search.includes("token=")) {
      return true; // Assume valid on reset token pages
    }

    setIsValidating(true);
    window.lastSessionValidation = now;

    try {
      // Get the session data from localStorage if available
      let refreshToken = "";
      try {
        const sessionData = localStorage.getItem("next-auth.session-token");
        if (sessionData) {
          refreshToken = sessionData;
        }
      } catch (error) {
        // Fail silently
      }

      // Call the server action to validate the session with timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        controller.abort();
      }, 8000); // 8 second timeout

      const response = await fetch("/api/auth/validate-session", {
        headers: {
          "X-Refresh-Token": refreshToken || "",
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        // Only log out if we get a 401 Unauthorized or 403 Forbidden
        if (response.status === 401 || response.status === 403) {
          await handleLogout("session expired");
          return false;
        }

        // For other errors (500, 503, 504), don't logout - might be temporary backend issues
        console.warn(
          `Session validation failed with status ${response.status}, treating as temporary issue`
        );
        return true;
      }

      const data = (await response.json()) as {
        valid: boolean;
        reason?: string;
      };

      if (!data.valid) {
        // Only log out for certain critical reasons
        const criticalReasons = [
          "session_invalidated",
          "user_not_found",
          "token_expired",
          "unauthorized",
        ];

        if (criticalReasons.includes(data.reason ?? "")) {
          await handleLogout(`invalid session: ${data.reason}`);
          return false;
        }

        // For other reasons, assume valid to prevent excessive logouts
        console.warn(
          `Session validation returned invalid but non-critical reason: ${data.reason}`
        );
        return true;
      }

      return true;
    } catch (error: unknown) {
      // Handle specific error types
      if (error instanceof Error && error.name === "AbortError") {
        console.warn(
          "Session validation timed out - treating as temporary issue"
        );
        return true;
      }

      if (
        error instanceof Error &&
        (error.message?.includes("fetch failed") ||
          error.message?.includes("ECONNREFUSED") ||
          error.message?.includes("network"))
      ) {
        console.warn(
          "Network error during session validation - treating as temporary issue"
        );
        return true;
      }

      console.warn("Session validation error:", error instanceof Error ? error.message : String(error));
      return true; // Assume valid on error to prevent excessive logouts
    } finally {
      setIsValidating(false);
    }
  }, [router, isValidating, handleLogout]);

  // Validate session on user interaction
  useEffect(() => {
    // Add event listeners for user interactions
    const handleUserInteraction = (): void => {
      // Skip if already logging out
      if (window.isLoggingOut) return;

      // Debounce to prevent too many calls
      if (window.sessionValidationTimeout) {
        clearTimeout(window.sessionValidationTimeout);
      }

      window.sessionValidationTimeout = setTimeout(() => {
        void checkSession(); // void operator to explicitly ignore the Promise
      }, 2000); // 2 second debounce (increased from 1 second)
    };

    // Add event listeners
    document.addEventListener("click", handleUserInteraction);
    document.addEventListener("keydown", handleUserInteraction);
    document.addEventListener("focus", handleUserInteraction); // Add focus events

    // Set up periodic validation (every 2 minutes), but delay the first check
    const initialDelay = setTimeout(() => {
      // Set up the interval after the initial delay
      const intervalId = setInterval(() => {
        if (!window.isLoggingOut) {
          void checkSession(); // void operator to explicitly ignore the Promise
        }
      }, 120000); // Check every 2 minutes (increased from 1 minute)

      // Store the interval ID so we can clear it on cleanup
      window.sessionValidationIntervalId = intervalId;
    }, 45000); // 45 second initial delay (increased from 30 seconds)

    return () => {
      // Clean up
      document.removeEventListener("click", handleUserInteraction);
      document.removeEventListener("keydown", handleUserInteraction);
      document.removeEventListener("focus", handleUserInteraction);
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

