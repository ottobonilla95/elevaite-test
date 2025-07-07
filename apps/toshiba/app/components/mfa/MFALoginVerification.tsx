"use client";

import { useState } from "react";
import { MFACodeInput } from "./MFACodeInput";

interface MFALoginVerificationProps {
  email: string;
  password: string;
  mfaType: "totp" | "sms";
  onVerify: (code: string) => Promise<void>;
  onCancel: () => void;
  onBackToMethodSelection?: () => void;
  onSendSMSCode?: () => Promise<void>;
  isLoading?: boolean;
  error?: string;
}

export function MFALoginVerification({
  email,
  password: _password,
  mfaType,
  onVerify,
  onCancel,
  onBackToMethodSelection,
  onSendSMSCode,
  isLoading = false,
  error,
}: MFALoginVerificationProps): JSX.Element {
  const [isVerifying, setIsVerifying] = useState(false);
  const [isSendingCode, setIsSendingCode] = useState(false);

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
    if (!onSendSMSCode) return;

    setIsSendingCode(true);
    try {
      await onSendSMSCode();
    } catch (error) {
      // Error handling is done by parent component
    } finally {
      setIsSendingCode(false);
    }
  };

  const getDescription = () => {
    return mfaType === "totp"
      ? "Enter the 6-digit code from your authenticator app."
      : "Enter the 6-digit code sent to your phone";
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
            Didn&apos;t receive a sign-in request?{" "}
            <button
              onClick={handleSendCode}
              disabled={isSendingCode || isVerifying || isLoading}
              className="ui-text-[var(--ev-colors-highlight)] hover:ui-text-[var(--ev-colors-highlight)]/80 ui-transition-colors disabled:ui-opacity-50 ui-underline"
            >
              {isSendingCode ? "Sending..." : "Resend request"}
            </button>
            .
          </div>
        </div>
      )}

      {/* Try another method button */}
      {onBackToMethodSelection && (
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
