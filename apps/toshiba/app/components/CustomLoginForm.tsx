"use client";
import { LogInForm } from "@repo/ui/components";
import type { JSX } from "react";
import { useEffect, useState } from "react";
import { MFALoginVerification, MFAMethodSelection } from "./mfa";

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
    | "MFA_REQUIRED_BOTH"
    | undefined
  >;
}

export function CustomLoginForm({
  authenticate,
}: CustomLoginFormProps): JSX.Element {
  const [mounted, setMounted] = useState(false);
  const [mfaState, setMfaState] = useState<{
    stage: "method_selection" | "verification";
    availableMethods: { totp: boolean; sms: boolean };
    selectedMethod?: "totp" | "sms";
    email: string;
    password: string;
    maskedPhone?: string;
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

  // Effect to hide/show the page title based on MFA state
  useEffect(() => {
    if (typeof document !== "undefined") {
      const titleElement = document.querySelector(".title");
      if (titleElement) {
        if (mfaState) {
          (titleElement as HTMLElement).style.display = "none";
        } else {
          (titleElement as HTMLElement).style.display = "block";
        }
      }
    }
  }, [mfaState]);

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

    try {
      const result = await authenticate(prevstate, {
        email: formData.email,
        password: formData.password,
      });

      if (result === "MFA_REQUIRED_TOTP") {
        setMfaState({
          stage: "method_selection",
          availableMethods: { totp: true, sms: false },
          email: formData.email,
          password: formData.password,
        });
        return undefined; // Don't show error, show MFA form instead
      }

      if (result === "MFA_REQUIRED_SMS") {
        setMfaState({
          stage: "method_selection",
          availableMethods: { totp: false, sms: true },
          email: formData.email,
          password: formData.password,
        });
        return undefined; // Don't show error, show MFA form instead
      }

      // Handle case where both MFA methods are available
      if (result === "MFA_REQUIRED_BOTH") {
        setMfaState({
          stage: "method_selection",
          availableMethods: { totp: true, sms: true },
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
    } catch (error: any) {
      // Handle MFA errors with masked phone number
      if (error.message === "MFA_REQUIRED_BOTH") {
        setMfaState({
          stage: "method_selection",
          availableMethods: { totp: true, sms: true },
          email: formData.email,
          password: formData.password,
          maskedPhone: error.maskedPhone,
        });
        return undefined;
      }

      if (error.message === "MFA_REQUIRED_SMS") {
        setMfaState({
          stage: "method_selection",
          availableMethods: { totp: false, sms: true },
          email: formData.email,
          password: formData.password,
          maskedPhone: error.maskedPhone,
        });
        return undefined;
      }

      if (error.message === "MFA_REQUIRED_TOTP") {
        setMfaState({
          stage: "method_selection",
          availableMethods: { totp: true, sms: false },
          email: formData.email,
          password: formData.password,
        });
        return undefined;
      }

      // Re-throw other errors
      throw error;
    }
  };

  // Handle MFA method selection
  const handleMethodSelect = (method: "totp" | "sms") => {
    if (!mfaState) return;

    setMfaState({
      ...mfaState,
      stage: "verification",
      selectedMethod: method,
    });
  };

  // Handle MFA verification
  const handleMfaVerify = async (code: string) => {
    if (!mfaState || !mfaState.selectedMethod) return;

    setError("");
    const result = await authenticate("", {
      email: mfaState.email,
      password: mfaState.password,
      totp_code: code,
    });

    if (result) {
      setError(result);
    } else {
      // Success - clear MFA state
      setMfaState(null);
    }
  };

  // Handle back to method selection
  const handleBackToMethodSelection = () => {
    if (!mfaState) return;

    setMfaState({
      ...mfaState,
      stage: "method_selection",
      selectedMethod: undefined,
    });
    setError("");
  };

  // Handle SMS code resend
  const handleSMSResend = async () => {
    if (!mfaState) return;

    try {
      const authApiUrl =
        process.env.NEXT_PUBLIC_AUTH_API_URL ?? "http://127.0.0.1:8004";
      const apiUrl = authApiUrl.replace("localhost", "127.0.0.1");

      const response = await fetch(`${apiUrl}/api/auth/resend-sms-code`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Tenant-ID": process.env.NEXT_PUBLIC_AUTH_TENANT_ID ?? "default",
        },
        body: JSON.stringify({
          email: mfaState.email,
          password: mfaState.password,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail ?? "Failed to resend SMS code");
      }

      // Success - no need to show a message, the user will receive the SMS
    } catch (error) {
      console.error("Failed to resend SMS code:", error);
      setError("Failed to resend SMS code. Please try again.");
    }
  };

  // Handle MFA cancellation
  const handleMfaCancel = () => {
    setMfaState(null);
    setError("");
  };

  // Only render the component on the client side to avoid hydration issues
  if (!mounted) {
    return <div className="ui-h-[400px]" />;
  }

  // Show MFA flow if active - this completely replaces the login form
  if (mfaState) {
    if (mfaState.stage === "method_selection") {
      return (
        <MFAMethodSelection
          email={mfaState.email}
          password={mfaState.password}
          availableMethods={mfaState.availableMethods}
          onMethodSelect={handleMethodSelect}
          onCancel={handleMfaCancel}
          phoneNumber={mfaState.maskedPhone}
        />
      );
    } else if (mfaState.stage === "verification" && mfaState.selectedMethod) {
      return (
        <MFALoginVerification
          email={mfaState.email}
          password={mfaState.password}
          mfaType={mfaState.selectedMethod}
          onVerify={handleMfaVerify}
          onCancel={handleMfaCancel}
          onBackToMethodSelection={
            // Only show back to method selection if multiple methods are available
            mfaState.availableMethods.totp && mfaState.availableMethods.sms
              ? handleBackToMethodSelection
              : undefined
          }
          onSendSMSCode={
            mfaState.selectedMethod === "sms" ? handleSMSResend : undefined
          }
          error={error}
        />
      );
    }
  }

  return <LogInForm authenticate={adaptedAuthenticate} />;
}
