"use client";

import { useEffect, useCallback, useState } from "react";
import { logout } from "../lib/actions";

declare global {
  interface Window {
    lastSessionValidation?: number;
  }
}

/**
 * Hook for periodic session validation
 */
export function useSessionValidation(): {
  checkSession: () => Promise<boolean>;
} {
  const [isValidating, setIsValidating] = useState(false);

  const checkSession = useCallback(async (): Promise<boolean> => {
    if (isValidating) {
      return true;
    }

    // Don't validate on auth pages
    const pathname = window.location.pathname;
    if (
      pathname === "/login" ||
      pathname === "/forgot-password" ||
      pathname === "/reset-password" ||
      pathname === "/verify-email" ||
      pathname === "/resend-verification"
    ) {
      return true;
    }

    const now = Date.now();
    if (
      window.lastSessionValidation &&
      now - window.lastSessionValidation < 500
    ) {
      return true;
    }

    setIsValidating(true);
    window.lastSessionValidation = now;

    try {
      const response = await fetch("/api/auth/validate-session");

      if (!response.ok && response.status === 401) {
        await logout();
        return false;
      }

      return true;
    } catch (error) {
      return true;
    } finally {
      setIsValidating(false);
    }
  }, []);

  // Session validation on page load and periodic checks
  useEffect(() => {
    // Check session immediately on page load (but not on auth pages)
    const pathname = window.location.pathname;
    if (
      pathname !== "/login" &&
      pathname !== "/forgot-password" &&
      pathname !== "/reset-password" &&
      pathname !== "/verify-email" &&
      pathname !== "/resend-verification"
    ) {
      void checkSession();
    }

    // Set up periodic validation
    const intervalId = setInterval(() => {
      void checkSession();
    }, 300000); // 5 minutes

    return () => {
      clearInterval(intervalId);
    };
  }, [checkSession]);

  return { checkSession };
}
