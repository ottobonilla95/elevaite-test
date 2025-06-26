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
}

export function CustomLoginForm({
  authenticate,
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

  // Adapter function to match LogInForm's expected interface
  const adaptedAuthenticate = async (
    prevstate: string,
    formData: { email: string; password: string; rememberMe: boolean }
  ): Promise<
    | "Invalid credentials."
    | "Email not verified."
    | "Something went wrong."
    | undefined
  > => {
    const result = await authenticate(prevstate, {
      email: formData.email,
      password: formData.password,
    });

    // Filter out "Admin access required." since LogInForm doesn't support it
    if (result === "Admin access required.") {
      return "Something went wrong.";
    }

    return result;
  };

  // Only render the component on the client side to avoid hydration issues
  if (!mounted) {
    return <div className="ui-h-[400px]" />;
  }

  return <LogInForm authenticate={adaptedAuthenticate} />;
}
