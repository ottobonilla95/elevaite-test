"use client";
import { LogInForm } from "@repo/ui/components";
import type { JSX } from "react";
import { useEffect, useState } from "react";
import { MFALoginVerification } from "./mfa/MFALoginVerification";

interface CustomLoginFormProps {
  authenticate: (
    prevstate: string,
    formData: Record<"email" | "password", string> & { totp_code?: string }
  ) => Promise<
    | "Invalid credentials."
    | "Email not verified."
    | "Admin access required."
    | "Something went wrong."
    | "MFA_REQUIRED_TOTP"
    | "MFA_REQUIRED_SMS"
    | undefined
  >;
}

export function CustomLoginForm({
  authenticate,
}: CustomLoginFormProps): JSX.Element {
  const [mounted, setMounted] = useState(false);
  const [mfaChallenge, setMfaChallenge] = useState<{
    type: "totp" | "sms";
    email: string;
    password: string;
  } | null>(null);
  const [error, setError] = useState<string>("");

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
    setError("");
    const result = await authenticate(prevstate, {
      email: formData.email,
      password: formData.password,
    });

    if (result === "MFA_REQUIRED_TOTP") {
      setMfaChallenge({
        type: "totp",
        email: formData.email,
        password: formData.password,
      });
      return undefined; // Don't show error, show MFA form instead
    }

    if (result === "MFA_REQUIRED_SMS") {
      setMfaChallenge({
        type: "sms",
        email: formData.email,
        password: formData.password,
      });
      return undefined; // Don't show error, show MFA form instead
    }

    // Filter out "Admin access required." since LogInForm doesn't support it
    if (result === "Admin access required.") {
      return "Something went wrong.";
    }

    return result;
  };

  // Handle MFA verification
  const handleMfaVerify = async (code: string) => {
    if (!mfaChallenge) return;

    setError("");
    const result = await authenticate("", {
      email: mfaChallenge.email,
      password: mfaChallenge.password,
      totp_code: code,
    });

    if (result) {
      setError(result);
    } else {
      // Success - clear MFA challenge
      setMfaChallenge(null);
    }
  };

  // Handle MFA cancellation
  const handleMfaCancel = () => {
    setMfaChallenge(null);
    setError("");
  };

  // Only render the component on the client side to avoid hydration issues
  if (!mounted) {
    return <div className="ui-h-[400px]" />;
  }

  // Show MFA verification if challenge is active
  if (mfaChallenge) {
    return (
      <MFALoginVerification
        email={mfaChallenge.email}
        password={mfaChallenge.password}
        mfaType={mfaChallenge.type}
        onVerify={handleMfaVerify}
        onCancel={handleMfaCancel}
        error={error}
      />
    );
  }

  return <LogInForm authenticate={adaptedAuthenticate} />;
}
