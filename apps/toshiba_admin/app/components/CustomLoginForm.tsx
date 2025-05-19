"use client";
import { LogInForm } from "@repo/ui/components";
import type { JSX } from "react";
import { useEffect, useState } from "react";

interface CustomLoginFormProps {
  authenticate: (
    prevstate: string,
    formData: Record<"email" | "password", string>
  ) => Promise<
    | "Invalid credentials."
    | "Email not verified."
    | "Something went wrong."
    | undefined
  >;
  authenticateGoogle: () => Promise<
    | "Invalid credentials."
    | "Email not verified."
    | "Something went wrong."
    | undefined
  >;
}

export function CustomLoginForm({
  authenticate,
  authenticateGoogle,
}: CustomLoginFormProps): JSX.Element {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);

    // Hide the register link when the component mounts
    if (typeof document !== "undefined") {
      const style = document.createElement("style");
      style.innerHTML = `
        /* Hide the register link section */
        .login-form-main-container > div:last-child {
          display: none !important;
        }
      `;
      document.head.appendChild(style);
    }
  }, []);

  // Only render the component on the client side to avoid hydration issues
  if (!mounted) {
    return <div className="ui-h-[400px]" />;
  }

  return (
    <LogInForm
      authenticate={authenticate}
      authenticateGoogle={authenticateGoogle}
    />
  );
}
