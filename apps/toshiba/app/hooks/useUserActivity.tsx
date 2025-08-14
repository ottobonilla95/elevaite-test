"use client";

import { useEffect, useCallback, useRef, useState } from "react";

declare global {
  interface Window {
    lastUserActivity?: number;
  }
}

interface ActivityConfig {
  inactivityTimeoutMinutes?: number;
  checkIntervalMs?: number;
  throttleMs?: number;
  trackMouseMovement?: boolean;
  mouseMoveThrottleMs?: number;
}

interface ActivityState {
  isActive: boolean;
  lastActivity: number;
  timeUntilInactive: number;
}

/**
 * Hook for tracking user activity and detecting inactivity
 */
export function useUserActivity(config: ActivityConfig = {}): {
  activityState: ActivityState;
  updateActivity: () => void;
  resetActivity: () => void;
} {
  const {
    inactivityTimeoutMinutes = 30,
    checkIntervalMs = 60000, // 1 minute
    throttleMs = 30000, // 30 seconds
    trackMouseMovement = true,
    mouseMoveThrottleMs = 5000, // 5 seconds
  } = config;

  const [activityState, setActivityState] = useState<ActivityState>({
    isActive: true,
    lastActivity: Date.now(),
    timeUntilInactive: inactivityTimeoutMinutes * 60 * 1000,
  });

  const lastActivityRef = useRef<number>(Date.now());
  const lastUpdateRef = useRef<number>(0);
  const lastMouseMoveRef = useRef<number>(0);
  const checkIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const updateActivity = useCallback(() => {
    const now = Date.now();
    const timeSinceLastUpdate = now - lastUpdateRef.current;

    // Throttle activity updates to avoid excessive calls
    if (timeSinceLastUpdate < throttleMs) {
      return;
    }

    lastActivityRef.current = now;
    lastUpdateRef.current = now;
    if (typeof window !== "undefined") {
      window.lastUserActivity = now;
    }

    setActivityState((prev) => ({
      ...prev,
      isActive: true,
      lastActivity: now,
      timeUntilInactive: inactivityTimeoutMinutes * 60 * 1000,
    }));
  }, [throttleMs, inactivityTimeoutMinutes]);

  const resetActivity = useCallback(() => {
    const now = Date.now();
    lastActivityRef.current = now;
    lastUpdateRef.current = 0; // Reset to allow immediate update
    if (typeof window !== "undefined") {
      window.lastUserActivity = now;
    }

    setActivityState({
      isActive: true,
      lastActivity: now,
      timeUntilInactive: inactivityTimeoutMinutes * 60 * 1000,
    });
  }, [inactivityTimeoutMinutes]);

  const handleMouseMove = useCallback(() => {
    if (!trackMouseMovement) return;

    const now = Date.now();
    const timeSinceLastMouseMove = now - lastMouseMoveRef.current;

    // Throttle mouse movement updates more aggressively
    if (timeSinceLastMouseMove < mouseMoveThrottleMs) {
      return;
    }

    lastMouseMoveRef.current = now;
    updateActivity();
  }, [trackMouseMovement, mouseMoveThrottleMs, updateActivity]);

  const handleUserInteraction = useCallback(() => {
    updateActivity();
  }, [updateActivity]);

  // Check for inactivity periodically
  const checkInactivity = useCallback(() => {
    const now = Date.now();
    const timeSinceLastActivity = now - lastActivityRef.current;
    const inactivityTimeoutMs = inactivityTimeoutMinutes * 60 * 1000;
    const timeUntilInactive = Math.max(
      0,
      inactivityTimeoutMs - timeSinceLastActivity
    );
    const isActive = timeSinceLastActivity < inactivityTimeoutMs;

    setActivityState((prev) => ({
      ...prev,
      isActive,
      timeUntilInactive,
    }));
  }, [inactivityTimeoutMinutes]);

  useEffect(() => {
    // Initialize activity timestamp
    const now = Date.now();
    lastActivityRef.current = now;
    if (typeof window !== "undefined") {
      window.lastUserActivity = now;
    }

    // Set up event listeners for user interactions
    const events = [
      "mousedown",
      "mouseup",
      "click",
      "keydown",
      "keyup",
      "scroll",
      "touchstart",
      "touchend",
      "touchmove",
      "focus",
      "blur",
    ];

    // Add mouse move listener separately due to throttling
    if (trackMouseMovement) {
      document.addEventListener("mousemove", handleMouseMove, {
        passive: true,
      });
    }

    // Add other event listeners
    events.forEach((event) => {
      document.addEventListener(event, handleUserInteraction, {
        passive: true,
      });
    });

    // Set up periodic inactivity check
    checkIntervalRef.current = setInterval(checkInactivity, checkIntervalMs);

    // Cleanup function
    return () => {
      if (trackMouseMovement) {
        document.removeEventListener("mousemove", handleMouseMove);
      }

      events.forEach((event) => {
        document.removeEventListener(event, handleUserInteraction);
      });

      if (checkIntervalRef.current) {
        clearInterval(checkIntervalRef.current);
      }
    };
  }, [
    handleMouseMove,
    handleUserInteraction,
    checkInactivity,
    checkIntervalMs,
    trackMouseMovement,
  ]);

  return {
    activityState,
    updateActivity,
    resetActivity,
  };
}

/**
 * Utility function to get the last activity timestamp
 */
export function getLastActivity(): number {
  return (
    (typeof window !== "undefined" ? window.lastUserActivity : null) ||
    Date.now()
  );
}

/**
 * Utility function to check if user has been inactive for a given duration
 */
export function isUserInactive(inactivityTimeoutMs: number): boolean {
  const lastActivity = getLastActivity();
  const timeSinceLastActivity = Date.now() - lastActivity;
  return timeSinceLastActivity >= inactivityTimeoutMs;
}
