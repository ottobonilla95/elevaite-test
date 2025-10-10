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

    // Enhanced CSS to fix UI styling - keep only eye icon
    if (typeof document !== "undefined") {
      const style = document.createElement("style");
      style.innerHTML = `
        /* Hide the register link section */
        .login-form-main-container > div:last-child {
          display: none !important;
        }
        
        /* Fix LogInForm container styling */
        .login-form-main-container {
          width: 100% !important;
          max-width: none !important;
          background: transparent !important;
          box-shadow: none !important;
          border: none !important;
          padding: 0 !important;
          margin: 0 !important;
        }
        
        /* HIDE ALL ICONS EXCEPT PASSWORD EYE */
        .login-form-main-container svg {
          display: none !important;
        }
        
        /* SHOW ONLY PASSWORD EYE ICON */
        .login-form-main-container button[type="button"] svg {
          display: block !important;
        }
        
        /* Style email field without icon space */
        .login-form-main-container input[type="email"] {
          background-color: var(--ev-colors-inputBackground, #2a2a2a) !important;
          border: 1px solid var(--ev-colors-inputBorder, #444) !important;
          color: var(--ev-colors-text, #ffffff) !important;
          border-radius: 8px !important;
          padding: 12px 16px !important;
          font-size: 14px !important;
          width: 100% !important;
          height: 48px !important;
        }
        
        /* Style password field with space for eye icon */
        .login-form-main-container input[type="password"] {
          background-color: var(--ev-colors-inputBackground, #2a2a2a) !important;
          border: 1px solid var(--ev-colors-inputBorder, #444) !important;
          color: var(--ev-colors-text, #ffffff) !important;
          border-radius: 8px !important;
          padding: 12px 40px 12px 16px !important;
          font-size: 14px !important;
          width: 100% !important;
          height: 48px !important;
        }
        
        /* Style labels */
        .login-form-main-container label {
          color: var(--ev-colors-text, #ffffff) !important;
          font-weight: 500 !important;
          margin-bottom: 8px !important;
          display: block !important;
        }
        
        /* Style the Sign In button */
        .login-form-main-container button[type="submit"] {
          background-color: var(--ev-colors-accent, #ef4444) !important;
          color: white !important;
          border: none !important;
          border-radius: 8px !important;
          padding: 12px 24px !important;
          font-size: 16px !important;
          font-weight: 600 !important;
          width: 100% !important;
          height: 48px !important;
          cursor: pointer !important;
          transition: all 0.2s ease !important;
        }
        
        .login-form-main-container button[type="submit"]:hover {
          background-color: var(--ev-colors-accentHover, #dc2626) !important;
        }
        
        /* Keep password toggle button visible and functional */
        .login-form-main-container button[type="button"] {
          background: transparent !important;
          border: none !important;
          color: #808080 !important;
          cursor: pointer !important;
          padding: 8px !important;
          position: absolute !important;
          right: 8px !important;
          top: 50% !important;
          transform: translateY(-50%) !important;
          z-index: 10 !important;
          width: 32px !important;
          height: 32px !important;
          display: flex !important;
          align-items: center !important;
          justify-content: center !important;
        }
        
        .login-form-main-container button[type="button"]:hover {
          color: #ffffff !important;
        }
        
        .login-form-main-container button[type="button"] svg {
          width: 16px !important;
          height: 16px !important;
        }
        
        /* Style forgot password link */
        .login-form-main-container a {
          color: var(--ev-colors-highlight, #3b82f6) !important;
          text-decoration: none !important;
        }
        
        /* Style checkbox container */
        .login-form-main-container .ui-flex {
          align-items: center !important;
          gap: 8px !important;
        }
        
        /* Style checkbox */
        .login-form-main-container input[type="checkbox"] {
          width: 16px !important;
          height: 16px !important;
          margin: 0 !important;
          accent-color: #e75f33 !important;
        }
        
        /* Style form spacing */
        .login-form-main-container > div {
          margin-bottom: 20px !important;
        }
        
        /* Responsive adjustments */
        @media (max-width: 768px) {
          .login-page-container {
            grid-template-columns: 1fr !important;
          }
          
          .auth-fluff-container {
            display: none !important;
          }
          
          .login-form-container {
            padding: 20px !important;
          }
        }
      `;
      document.head.appendChild(style);

      return () => {
        document.head.removeChild(style);
      };
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
        return undefined;
      }

      if (result === "MFA_REQUIRED_SMS") {
        setMfaState(
          createMfaState(
            { totp: false, sms: true, email: false },
            formData.email,
            formData.password
          )
        );
        return undefined;
      }

      if (result === "MFA_REQUIRED_EMAIL") {
        setMfaState(
          createMfaState(
            { totp: false, sms: false, email: true },
            formData.email,
            formData.password
          )
        );
        return undefined;
      }

      if (result === "MFA_REQUIRED_MULTIPLE") {
        return undefined;
      }

      if (result === "Admin access required.") {
        return "Something went wrong.";
      }

      return typeof result === "string" ? result : "Something went wrong.";
    } catch (error: any) {
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
    } catch (error: any) {
      setError(error.message ?? "Failed to resend SMS code");
    }
  };

  // Handle Email code resend
  const handleEmailResend = async () => {
    if (!mfaState) return;

    try {
      const result = await authenticate("", {
        email: mfaState.email,
        password: mfaState.password,
      });

      if (result === "MFA_REQUIRED_EMAIL") {
        return;
      }

      if (result) {
        if (typeof result === "string") {
          setError(result);
        } else {
          setError("Something went wrong.");
        }
      }
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