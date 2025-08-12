"use client";
import { LogInForm } from "@repo/ui/components";
import type { JSX } from "react";
import { useEffect, useState } from "react";
import { MFALoginVerification, MFAMethodSelection } from "./mfa";
import { getMFAConfig } from "../lib/mfaConfig";

interface CustomLoginFormProps {
  authenticate: (
    prevstate: string,
    formData: Record<"email" | "password", string> & { totp_code?: string }
  ) => Promise<
    | "Invalid credentials."
    | "Email not verified."
    | "Account locked. Please try again later or reset your password."
    | "Too many attempts. Please try again later."
    | "Admin access required."
    | "Something went wrong."
    | "MFA_REQUIRED_TOTP"
    | "MFA_REQUIRED_SMS"
    | "MFA_REQUIRED_EMAIL"
    | "MFA_REQUIRED_MULTIPLE"
    | { type: "MFA_ERROR"; error: any }
    | undefined
  >;
}

export function CustomLoginForm({
  authenticate,
}: CustomLoginFormProps): JSX.Element {
  const [mounted, setMounted] = useState(false);
  const [mfaState, setMfaState] = useState<{
    stage: "method_selection" | "verification";
    availableMethods: { totp: boolean; sms: boolean; email: boolean };
    selectedMethod?: "totp" | "sms" | "email";
    email: string;
    password: string;
    maskedPhone?: string;
    maskedEmail?: string;
  } | null>(null);
  const [error, setError] = useState<string>("");

  const mfaConfig = getMFAConfig();

  const filterAvailableMethods = (methods: {
    totp: boolean;
    sms: boolean;
    email: boolean;
  }) => ({
    totp: methods.totp && mfaConfig.totp,
    sms: methods.sms && mfaConfig.sms,
    email: methods.email && mfaConfig.email,
  });

  // Helper function to determine if auto-selection should occur
  const shouldAutoSelectMethod = (availableMethods: {
    totp: boolean;
    sms: boolean;
    email: boolean;
  }) => {
    const enabledCount = Object.values(availableMethods).filter(Boolean).length;
    return enabledCount === 1;
  };

  // Helper function to get the single enabled method
  const getSingleEnabledMethod = (availableMethods: {
    totp: boolean;
    sms: boolean;
    email: boolean;
  }): "totp" | "sms" | "email" | null => {
    if (availableMethods.totp) return "totp";
    if (availableMethods.sms) return "sms";
    if (availableMethods.email) return "email";
    return null;
  };

  // Helper function to create MFA state with auto-selection logic
  const createMfaState = (
    availableMethods: { totp: boolean; sms: boolean; email: boolean },
    email: string,
    password: string,
    maskedPhone?: string,
    maskedEmail?: string
  ) => {
    const filteredMethods = filterAvailableMethods(availableMethods);

    if (shouldAutoSelectMethod(filteredMethods)) {
      const singleMethod = getSingleEnabledMethod(filteredMethods);
      if (singleMethod) {
        return {
          stage: "verification" as const,
          availableMethods: filteredMethods,
          selectedMethod: singleMethod,
          email,
          password,
          maskedPhone,
          maskedEmail,
        };
      }
    }
    return {
      stage: "method_selection" as const,
      availableMethods: filteredMethods,
      email,
      password,
      maskedPhone,
      maskedEmail,
    };
  };

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
    | "Account locked. Please try again later or reset your password."
    | "Too many attempts. Please try again later."
    | "Something went wrong."
    | undefined
  > => {
    setError("");

    try {
      const result = await authenticate(prevstate, {
        email: formData.email,
        password: formData.password,
      });

      if (result && typeof result === "object" && result.type === "MFA_ERROR") {
        const error = result.error;

        if (error.message === "MFA_REQUIRED_MULTIPLE") {
          const availableMethods = error.availableMethods || [];
          const methodsObj = {
            totp: availableMethods.includes("TOTP"),
            sms: availableMethods.includes("SMS"),
            email: availableMethods.includes("Email"),
          };

          setMfaState(
            createMfaState(
              methodsObj,
              formData.email,
              formData.password,
              error.maskedPhone,
              error.maskedEmail
            )
          );
          return undefined;
        }

        if (error.message === "MFA_REQUIRED_TOTP") {
          setMfaState(
            createMfaState(
              { totp: true, sms: false, email: false },
              formData.email,
              formData.password
            )
          );
          return undefined;
        }

        if (error.message === "MFA_REQUIRED_SMS") {
          setMfaState(
            createMfaState(
              { totp: false, sms: true, email: false },
              formData.email,
              formData.password,
              error.maskedPhone
            )
          );
          return undefined;
        }

        if (error.message === "MFA_REQUIRED_EMAIL") {
          setMfaState(
            createMfaState(
              { totp: false, sms: false, email: true },
              formData.email,
              formData.password,
              undefined,
              error.maskedEmail
            )
          );
          return undefined;
        }
      }

      if (result === "MFA_REQUIRED_TOTP") {
        setMfaState(
          createMfaState(
            { totp: true, sms: false, email: false },
            formData.email,
            formData.password
          )
        );
        return undefined; // Don't show error, show MFA form instead
      }

      if (result === "MFA_REQUIRED_SMS") {
        setMfaState(
          createMfaState(
            { totp: false, sms: true, email: false },
            formData.email,
            formData.password
          )
        );
        return undefined; // Don't show error, show MFA form instead
      }

      if (result === "MFA_REQUIRED_EMAIL") {
        setMfaState(
          createMfaState(
            { totp: false, sms: false, email: true },
            formData.email,
            formData.password
          )
        );
        return undefined; // Don't show error, show MFA form instead
      }

      if (result === "MFA_REQUIRED_MULTIPLE") {
        return undefined;
      }

      // Filter out "Admin access required." since LogInForm doesn't support it
      if (result === "Admin access required.") {
        return "Something went wrong.";
      }

      return typeof result === "string" ? result : "Something went wrong.";
    } catch (error: any) {
      // Handle MFA errors with masked phone number and email
      if (error.message === "MFA_REQUIRED_MULTIPLE") {
        // Parse available methods from error
        const availableMethods = error.availableMethods || [];

        const methodsObj = {
          totp: availableMethods.includes("TOTP"),
          sms: availableMethods.includes("SMS"),
          email: availableMethods.includes("Email"),
        };

        setMfaState(
          createMfaState(
            methodsObj,
            formData.email,
            formData.password,
            error.maskedPhone,
            error.maskedEmail
          )
        );
        return undefined;
      }

      if (error.message === "MFA_REQUIRED_SMS") {
        setMfaState(
          createMfaState(
            { totp: false, sms: true, email: false },
            formData.email,
            formData.password,
            error.maskedPhone
          )
        );
        return undefined;
      }

      if (error.message === "MFA_REQUIRED_EMAIL") {
        setMfaState(
          createMfaState(
            { totp: false, sms: false, email: true },
            formData.email,
            formData.password,
            undefined,
            error.maskedEmail
          )
        );
        return undefined;
      }

      if (error.message === "MFA_REQUIRED_TOTP") {
        setMfaState(
          createMfaState(
            { totp: true, sms: false, email: false },
            formData.email,
            formData.password
          )
        );
        return undefined;
      }

      // Re-throw other errors
      throw error;
    }
  };

  // Handle MFA method selection
  const handleMethodSelect = async (method: "totp" | "sms" | "email") => {
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
      if (typeof result === "string") {
        setError(result);
      } else {
        setError("Something went wrong.");
      }
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

      // Success - code was resent
    } catch (error: any) {
      setError(error.message ?? "Failed to resend SMS code");
    }
  };

  // Handle Email code resend
  const handleEmailResend = async () => {
    if (!mfaState) return;

    try {
      // For email MFA during login, we need to trigger the login again
      // which will automatically send the email code
      const result = await authenticate("", {
        email: mfaState.email,
        password: mfaState.password,
      });

      // If we get MFA_REQUIRED_EMAIL again, that means the code was sent
      if (result === "MFA_REQUIRED_EMAIL") {
        // Code was resent successfully, no need to update state
        return;
      }

      // If we get a different result, handle it appropriately
      if (result) {
        if (typeof result === "string") {
          setError(result);
        } else {
          setError("Something went wrong.");
        }
      }

      // Success - no need to show a message, the user will receive the email
    } catch (error: any) {
      console.error("Failed to resend email code:", error);
      setError(
        error.message ?? "Failed to resend email code. Please try again."
      );
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
          userEmail={mfaState.maskedEmail || mfaState.email}
        />
      );
    } else if (mfaState.stage === "verification" && mfaState.selectedMethod) {
      return (
        <MFALoginVerification
          email={mfaState.email}
          password={mfaState.password}
          mfaType={mfaState.selectedMethod}
          availableMethods={mfaState.availableMethods}
          onVerify={handleMfaVerify}
          onCancel={handleMfaCancel}
          onBackToMethodSelection={handleBackToMethodSelection}
          onSendSMSCode={
            mfaState.selectedMethod === "sms" ? handleSMSResend : undefined
          }
          onSendEmailCode={
            mfaState.selectedMethod === "email" ? handleEmailResend : undefined
          }
          error={error}
        />
      );
    }
  }

  return <LogInForm authenticate={adaptedAuthenticate} />;
}
