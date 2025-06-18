"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { signOut } from "next-auth/react";
import { useSessionValidation } from "../hooks/useSessionValidation";

export function SessionValidator({
  children,
}: {
  children: React.ReactNode;
}): JSX.Element {
  const { checkSession } = useSessionValidation();
  const pathname = usePathname();
  const router = useRouter();
  const [isValidating, setIsValidating] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

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
      setIsLoading(false);
      return;
    }

    // Prevent multiple simultaneous validations
    if (isValidating) return;

    async function validateSession(): Promise<void> {
      setIsValidating(true);

      try {
        const isValid = await checkSession();

        if (!isValid) {
          // Use signOut to clear the session and redirect to login
          await signOut({ callbackUrl: "/login" });
        }
      } catch (error) {
        // Fail silently
      } finally {
        setIsValidating(false);
        setIsLoading(false);
      }
    }

    void validateSession();
  }, [pathname]);

  // Show loading state while validating session on initial load
  if (
    isLoading &&
    pathname !== "/login" &&
    !pathname.includes("/reset-password") &&
    !pathname.includes("/forgot-password")
  ) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-gray-900" />
      </div>
    );
  }

  return <>{children}</>;
}
