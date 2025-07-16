"use client";

import { useState, useEffect, useRef } from "react";
import { MFACodeInput } from "./MFACodeInput";

interface MFALoginVerificationProps {
  email: string;
  password: string;
  mfaType: "totp" | "sms" | "email";
  availableMethods?: { totp: boolean; sms: boolean; email: boolean };
  onVerify: (code: string) => Promise<void>;
  onCancel: () => void;
  onBackToMethodSelection?: () => void;
  onSendSMSCode?: () => Promise<void>;
  onSendEmailCode?: () => Promise<void>;
  isLoading?: boolean;
  error?: string;
}

export function MFALoginVerification({
  email,
  password,
  mfaType,
  availableMethods,
  onVerify,
  onCancel,
  onBackToMethodSelection,
  onSendSMSCode,
  onSendEmailCode,
  isLoading = false,
  error,
}: MFALoginVerificationProps): JSX.Element {
  const [isVerifying, setIsVerifying] = useState(false);
  const [isSendingCode, setIsSendingCode] = useState(false);
  const [emailResendCooldown, setEmailResendCooldown] = useState(0);
  const emailCodeSentRef = useRef(false);

  // Check if there are multiple methods available
  const hasMultipleMethods = () => {
    if (!availableMethods) return false;
    const methodCount = Object.values(availableMethods).filter(Boolean).length;
    return methodCount > 1;
  };

  // Handle email resend cooldown timer
  useEffect(() => {
    if (emailResendCooldown > 0) {
      const timer = setTimeout(() => {
        setEmailResendCooldown(emailResendCooldown - 1);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [emailResendCooldown]);

  // Automatically send email code when component mounts for email MFA
  useEffect(() => {
    if (mfaType === "email" && !emailCodeSentRef.current) {
      const sendEmailCode = async () => {
        setIsSendingCode(true);
        emailCodeSentRef.current = true; // Set immediately to prevent double calls
        try {
          const response = await fetch("/api/email-mfa/send-login-code", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              email,
              password,
            }),
          });

          if (!response.ok) {
            const errorData = await response.json();
            console.error("Failed to send email code:", errorData.detail);
            emailCodeSentRef.current = false;
          } else {
            // Start the 10-second cooldown after initial send
            setEmailResendCooldown(10);
          }
        } catch (error: any) {
          console.error("Failed to send email code:", error.message);
          emailCodeSentRef.current = false;
        } finally {
          setIsSendingCode(false);
        }
      };

      sendEmailCode();
    }
  }, [mfaType, email, password]);

  const handleCodeComplete = async (code: string) => {
    setIsVerifying(true);
    try {
      await onVerify(code);
    } catch (error) {
      // Error handling is done by parent component
    } finally {
      setIsVerifying(false);
    }
  };

  const handleSendCode = async () => {
    if (mfaType === "sms" && onSendSMSCode) {
      setIsSendingCode(true);
      try {
        await onSendSMSCode();
      } catch (error) {
        // Error handling is done by parent component
      } finally {
        setIsSendingCode(false);
      }
    } else if (mfaType === "email") {
      setIsSendingCode(true);
      try {
        const response = await fetch("/api/email-mfa/send-login-code", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email,
            password,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          console.error("Failed to send email code:", errorData.detail);
        } else {
          // Start the 10-second cooldown
          setEmailResendCooldown(10);
        }
      } catch (error: any) {
        console.error("Failed to send email code:", error.message);
      } finally {
        setIsSendingCode(false);
      }
    }
  };

  const getDescription = () => {
    if (mfaType === "totp") {
      return "Enter the 6-digit code from your authenticator app.";
    } else if (mfaType === "sms") {
      return "Enter the 6-digit code sent to your phone.";
    } else if (mfaType === "email") {
      return "Enter the 6-digit code sent to your email.";
    }
    return "Enter the 6-digit verification code.";
  };

  return (
    <div className="ui-w-full ui-max-w-md ui-mx-auto">
      {/* Header */}
      <div className="ui-text-left ui-mb-8">
        <h1 className="ui-text-3xl ui-font-bold ui-text-white ui-mb-2">
          Enter verification code
        </h1>
        <p className="ui-text-gray-400">{getDescription()}</p>
      </div>

      {/* Code Input with top gap */}
      <div style={{ marginTop: "25px", width: "75%" }}>
        <MFACodeInput
          onComplete={handleCodeComplete}
          error={error}
          disabled={isVerifying || isLoading}
          autoFocus={true}
        />
      </div>

      {isVerifying && (
        <div
          className="ui-text-left ui-text-sm ui-text-gray-400 ui-mt-4"
          style={{ width: "75%" }}
        >
          Verifying code...
        </div>
      )}

      {/* SMS Resend section */}
      {mfaType === "sms" && onSendSMSCode && (
        <div style={{ marginTop: "25px", width: "75%" }}>
          <div className="ui-text-left ui-text-sm ui-text-gray-400">
            Didn&apos;t receive the code?{" "}
            <button
              onClick={handleSendCode}
              disabled={isSendingCode || isVerifying || isLoading}
              className="ui-text-[var(--ev-colors-highlight)] hover:ui-text-[var(--ev-colors-highlight)]/80 ui-transition-colors disabled:ui-opacity-50 ui-underline"
            >
              {isSendingCode ? "Sending..." : "Resend code"}
            </button>
            .
          </div>
        </div>
      )}

      {/* Email Resend section */}
      {mfaType === "email" && (
        <div style={{ marginTop: "25px", width: "75%" }}>
          <div className="ui-text-left ui-text-sm">
            <span className="ui-text-gray-400">
              Didn&apos;t receive the code?{" "}
            </span>
            <button
              onClick={handleSendCode}
              disabled={
                isSendingCode ||
                isVerifying ||
                isLoading ||
                emailResendCooldown > 0
              }
              style={{ color: "var(--ev-colors-highlight)" }}
              className="hover:ui-opacity-80 ui-transition-colors disabled:ui-opacity-50 ui-underline"
            >
              {isSendingCode
                ? "Sending..."
                : emailResendCooldown > 0
                  ? `Resend code (${emailResendCooldown}s)`
                  : "Resend code"}
            </button>
          </div>
        </div>
      )}

      {/* Try another method button - only show if there are multiple methods */}
      {onBackToMethodSelection && hasMultipleMethods() && (
        <div style={{ marginTop: "25px", width: "75%" }}>
          <button
            onClick={onBackToMethodSelection}
            disabled={isVerifying || isLoading}
            style={{ color: "var(--ev-colors-highlight)" }}
            className="hover:ui-opacity-80 ui-transition-colors disabled:ui-opacity-50 ui-underline ui-text-sm"
          >
            Try another method
          </button>
        </div>
      )}
    </div>
  );
}
