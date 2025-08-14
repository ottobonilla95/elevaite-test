"use client";

import { useEffect, useCallback, useState, useRef } from "react";
import { logout } from "../lib/actions";
import { useUserActivity, isUserInactive } from "./useUserActivity";

declare global {
  interface Window {
    lastSessionValidation?: number;
    sessionConfig?: {
      inactivityTimeoutMinutes: number;
      activityCheckIntervalMinutes: number;
      sessionExtensionMinutes: number;
    };
  }
}

/**
 * Hook for periodic session validation
 */
export function useSessionValidation(): {
  checkSession: () => Promise<boolean>;
  extendSession: () => Promise<boolean>;
} {
  const [isValidating, setIsValidating] = useState(false);
  const [isExtending, setIsExtending] = useState(false);
  const lastExtensionRef = useRef<number>(0);

  const sessionConfig = (typeof window !== "undefined"
    ? window.sessionConfig
    : null) || {
    inactivityTimeoutMinutes: 90,
    activityCheckIntervalMinutes: 5,
    sessionExtensionMinutes: 30,
  };

  // Set up activity tracking
  const { activityState } = useUserActivity({
    inactivityTimeoutMinutes: sessionConfig.inactivityTimeoutMinutes,
    checkIntervalMs: sessionConfig.activityCheckIntervalMinutes * 60 * 1000,
    throttleMs: 30000, // 30 seconds between activity updates
    trackMouseMovement: true,
    mouseMoveThrottleMs: 10000, // 10 seconds for mouse movement
  });

  const extendSession = useCallback(async (): Promise<boolean> => {
    if (isExtending) {
      return true;
    }

    // Don't extend on auth pages
    const pathname =
      typeof window !== "undefined" ? window.location.pathname : "";
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
    const timeSinceLastExtension = now - lastExtensionRef.current;

    // Don't extend too frequently (minimum 5 minutes between extensions)
    if (timeSinceLastExtension < 5 * 60 * 1000) {
      return true;
    }

    setIsExtending(true);
    lastExtensionRef.current = now;

    try {
      const response = await fetch("/api/auth/extend-session", {
        method: "POST",
      });

      if (response.ok) {
        await response.json();
        lastExtensionRef.current = Date.now();
        return true;
      } else if (response.status === 401) {
        await logout();
        return false;
      }

      return true;
    } catch (error) {
      return true;
    } finally {
      setIsExtending(false);
    }
  }, []);

  const checkSession = useCallback(async (): Promise<boolean> => {
    if (isValidating) {
      return true;
    }

    // Don't validate on auth pages
    const pathname =
      typeof window !== "undefined" ? window.location.pathname : "";
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
      typeof window !== "undefined" &&
      window.lastSessionValidation &&
      now - window.lastSessionValidation < 500
    ) {
      return true;
    }

    // Check for inactivity before validating session
    const inactivityTimeoutMs =
      sessionConfig.inactivityTimeoutMinutes * 60 * 1000;
    if (isUserInactive(inactivityTimeoutMs)) {
      await logout();
      return false;
    }

    setIsValidating(true);
    if (typeof window !== "undefined") {
      window.lastSessionValidation = now;
    }

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
  }, [sessionConfig.inactivityTimeoutMinutes]);

  // Session validation on page load and periodic checks
  useEffect(() => {
    // Check session immediately on page load (but not on auth pages)
    const pathname =
      typeof window !== "undefined" ? window.location.pathname : "";
    if (
      pathname !== "/login" &&
      pathname !== "/forgot-password" &&
      pathname !== "/reset-password" &&
      pathname !== "/verify-email" &&
      pathname !== "/resend-verification"
    ) {
      void checkSession();
    }

    // Set up periodic validation using configurable interval
    const intervalMs = sessionConfig.activityCheckIntervalMinutes * 60 * 1000;
    const intervalId = setInterval(() => {
      void checkSession();
    }, intervalMs);

    return () => {
      clearInterval(intervalId);
    };
  }, [checkSession, sessionConfig.activityCheckIntervalMinutes]);

  // Extend session when user becomes active after a period of inactivity
  useEffect(() => {
    if (activityState.isActive && activityState.lastActivity) {
      const timeSinceLastExtension = Date.now() - lastExtensionRef.current;

      // If it's been more than 10 minutes since last extension and user is active, extend session
      if (timeSinceLastExtension > 10 * 60 * 1000) {
        void extendSession();
      }
    }
  }, [activityState.isActive, activityState.lastActivity, extendSession]);

  return { checkSession, extendSession };
}
