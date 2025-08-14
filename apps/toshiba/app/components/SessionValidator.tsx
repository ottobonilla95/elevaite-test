"use client";

import { useEffect } from "react";
import { useSessionValidation } from "../hooks/useSessionValidation";

export function SessionValidator({
  children,
}: {
  children: React.ReactNode;
}): JSX.Element {
  useSessionValidation();

  useEffect(() => {
    const loadSessionConfig = async () => {
      try {
        const response = await fetch("/api/auth/session-config");
        if (response.ok) {
          const config = await response.json();
          if (typeof window !== "undefined") {
            window.sessionConfig = config;
          }
        }
      } catch (error) {
        // Failed to load session configuration, use default configuration
        if (typeof window !== "undefined") {
          window.sessionConfig = {
            inactivityTimeoutMinutes: 90,
            activityCheckIntervalMinutes: 5,
            sessionExtensionMinutes: 30,
          };
        }
      }
    };

    void loadSessionConfig();
  }, []);

  return <>{children}</>;
}
