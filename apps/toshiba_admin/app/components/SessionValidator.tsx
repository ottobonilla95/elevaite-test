"use client";

import { usePathname } from "next/navigation";
import { useEffect } from "react";
import { useSessionValidation } from "../hooks/useSessionValidation";

export function SessionValidator({ children }: { children: React.ReactNode }) {
  const { checkSession } = useSessionValidation();
  const pathname = usePathname();

  // Validate session on initial load and when pathname changes
  useEffect(() => {
    // Skip validation on auth pages
    if (
      pathname === "/login" ||
      pathname === "/reset-password" ||
      pathname.includes("/reset-password") ||
      pathname === "/forgot-password" ||
      pathname.includes("/forgot-password")
    ) {
      console.log("Skipping session validation on auth page:", pathname);
      return;
    }

    console.log("Validating session on page load/change:", pathname);
    checkSession();
  }, [pathname, checkSession]);

  return <>{children}</>;
}
