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
    | "Admin access required."
    | "Something went wrong."
    | undefined
  >;
  authenticateGoogle: () => Promise<
    | "Invalid credentials."
    | "Email not verified."
    | "Admin access required."
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

  // Create wrapper functions to handle the admin access required error
  const handleAuthenticate = async (
    prevstate: string,
    formData: { email: string; password: string; rememberMe: boolean }
  ) => {
    // Convert formData to the expected format
    const credentials = {
      email: formData.email,
      password: formData.password,
    };

    const result = await authenticate(prevstate, credentials);

    // If the error is "Admin access required", display a custom error message
    if (result === "Admin access required.") {
      return "Something went wrong.";
    }

    return result;
  };

  const handleGoogleAuthenticate = async () => {
    const result = await authenticateGoogle();

    // If the error is "Admin access required", display a custom error message
    if (result === "Admin access required.") {
      return "Something went wrong.";
    }

    return result;
  };

  return (
    <LogInForm
      authenticate={handleAuthenticate}
      authenticateGoogle={handleGoogleAuthenticate}
    />
  );
}
