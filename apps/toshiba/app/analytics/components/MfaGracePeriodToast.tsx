"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useSession } from "next-auth/react";

interface MfaGracePeriodToastProps {
  className?: string;
}

export function MfaGracePeriodToast({
  className = "",
}: MfaGracePeriodToastProps): JSX.Element | null {
  const { data: session, status } = useSession();
  const router = useRouter();
  const pathname = usePathname();
  const [isVisible, setIsVisible] = useState(false);
  const [isDismissed, setIsDismissed] = useState(false);
  const previousStatusRef = useRef<typeof status>("loading");
  const hasShownOnLoginRef = useRef(false);

  const isToastFreePage =
    pathname === "/login" ||
    pathname === "/forgot-password" ||
    pathname === "/reset-password" ||
    pathname === "/verify-email" ||
    pathname === "/resend-verification" ||
    pathname === "/settings";

  const shouldShowToast = useCallback((userSession: any): boolean => {
    if (!userSession?.user?.grace_period?.in_grace_period) {
      return false;
    }

    const dismissedKey = `mfa-toast-dismissed-${userSession.user.email}`;
    return sessionStorage.getItem(dismissedKey) !== "true";
  }, []);

  useEffect(() => {
    const previousStatus = previousStatusRef.current;
    previousStatusRef.current = status;

    if (previousStatus === "authenticated" && status === "unauthenticated") {
      setIsVisible(false);
      setIsDismissed(false);
      hasShownOnLoginRef.current = false;
      return;
    }

    // Only proceed if we have an authenticated session
    if (status !== "authenticated" || !session?.user) {
      setIsVisible(false);
      return;
    }

    // Check if user is in grace period
    if (!shouldShowToast(session)) {
      setIsVisible(false);
      return;
    }

    // Detect new login (status changed from loading/unauthenticated to authenticated)
    const isNewLogin =
      (previousStatus === "loading" || previousStatus === "unauthenticated") &&
      status === "authenticated";

    if (isNewLogin) {
      // Clear any previous dismissal for this user on new login
      if (session.user.email) {
        const dismissedKey = `mfa-toast-dismissed-${session.user.email}`;
        sessionStorage.removeItem(dismissedKey);
      }
      hasShownOnLoginRef.current = false;
    }

    // Show toast if user should see it and we haven't shown it yet
    if (!hasShownOnLoginRef.current) {
      setIsVisible(true);
      setIsDismissed(false);
      hasShownOnLoginRef.current = true;
    }
  }, [session, status, shouldShowToast]);

  // Handle page visibility changes for page reloads
  useEffect(() => {
    const handleVisibilityChange = () => {
      // When page becomes visible after being hidden, re-evaluate toast
      if (
        !document.hidden &&
        status === "authenticated" &&
        session?.user &&
        shouldShowToast(session)
      ) {
        if (!hasShownOnLoginRef.current) {
          setIsVisible(true);
          setIsDismissed(false);
          hasShownOnLoginRef.current = true;
        }
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [session, status, shouldShowToast]);

  // Don't render on auth pages (after all hooks)
  if (isToastFreePage) {
    return null;
  }

  const handleDismiss = () => {
    setIsVisible(false);
    setIsDismissed(true);

    // Store dismissal in session storage
    if (session?.user?.email) {
      const dismissedKey = `mfa-toast-dismissed-${session.user.email}`;
      sessionStorage.setItem(dismissedKey, "true");
    }
  };

  const handleSetupMfa = () => {
    // Close the toast first
    handleDismiss();
    // Navigate to settings with MFA section pre-selected
    router.push("/settings#mfa");
  };

  // Don't render if not visible or dismissed
  if (!isVisible || isDismissed) {
    return null;
  }

  const gracePeriod = session?.user?.grace_period;
  if (!gracePeriod) {
    return null;
  }

  const daysRemaining = gracePeriod.days_remaining;
  const daysText = daysRemaining === 1 ? "day" : "days";

  return (
    <div
      className={`fixed mt-10 left-[4%] right-[4%] w-[92%] z-[1000] sm:top-5 sm:left-[5%] sm:right-[5%] sm:w-[90%] ${className}`}
    >
      <div
        className="flex items-center gap-3 p-4 rounded-2xl shadow-lg border border-white/10 transition-all duration-300 sm:p-3 sm:gap-2"
        style={{
          backgroundColor: "var(--ev-colors-highlight)",
          color: "var(--ev-colors-text)",
        }}
      >
        {/* Info icon */}
        <div className="flex-shrink-0 flex items-center justify-center mr-5">
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="white"
            stroke="none"
          >
            <circle cx="12" cy="12" r="12" fill="white" />
            <path
              d="M12 8v4m0 4h.01"
              stroke="var(--ev-colors-highlight)"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>

        {/* Message */}
        <div
          className="flex-1 leading-relaxed"
          style={{ color: "var(--ev-colors-text)" }}
        >
          <span className="text-lg">
            You have {daysRemaining} {daysText} to enable Multi-Factor
            Authentication. Protect your account and avoid interruptions by
            setting it up now.
          </span>
        </div>

        {/* Setup MFA button */}
        <button
          onClick={handleSetupMfa}
          className="flex-shrink-0 bg-transparent border-none cursor-pointer p-0 flex items-center gap-2 text-lg font-medium underline transition-opacity duration-200 hover:opacity-80"
          style={{ color: "var(--ev-colors-text)" }}
          type="button"
        >
          <span className="text-lg">Set up MFA</span>
          <div
            className="flex items-center justify-center w-6 h-6 bg-white rounded-full flex-shrink-0"
            style={{ color: "var(--ev-colors-highlight)" }}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M5 12h14" />
              <path d="m12 5 7 7-7 7" />
            </svg>
          </div>
        </button>

        {/* Close button */}
        <button
          onClick={handleDismiss}
          className="flex-shrink-0 bg-transparent border-none cursor-pointer p-1 rounded flex items-center justify-center transition-colors duration-200 hover:bg-white/10 ml-5"
          style={{ color: "var(--ev-colors-text)" }}
          type="button"
          aria-label="Dismiss notification"
        >
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>
    </div>
  );
}
