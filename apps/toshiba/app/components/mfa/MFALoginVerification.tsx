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

  const getTitle = () => {
    return "Enter verification code";
  };

  const getDescription = () => {
    return mfaType === "totp"
      ? "Enter the 6-digit code from your authenticator app"
      : "Enter the 6-digit code sent to your phone";
  };

  const getIcon = () => {
    return mfaType === "totp" ? <AuthenticatorIcon /> : <SMSIcon />;
  };

  return (
    <div className="ui-max-w-md ui-mx-auto ui-p-6 ui-bg-[#1a1a1a] ui-rounded-lg ui-border ui-border-gray-700">
      <div className="ui-text-center ui-mb-6">
        <div className="ui-flex ui-justify-center ui-mb-4">
          <div className="ui-p-3 ui-bg-[var(--ev-colors-highlight)] ui-rounded-full">
            {getIcon()}
          </div>
        </div>
        <h2 className="ui-text-2xl ui-font-bold ui-text-white ui-mb-2">
          {getTitle()}
        </h2>
        <p className="ui-text-gray-400 ui-mb-2">{getDescription()}</p>
        <p className="ui-text-sm ui-text-gray-500">
          Signing in as: <span className="ui-text-gray-300">{email}</span>
        </p>
      </div>

      <div className="ui-space-y-6">
        <MFACodeInput
          onComplete={handleCodeComplete}
          error={error}
          disabled={isVerifying || isLoading}
          autoFocus={true}
        />

        {isVerifying && (
          <div className="ui-text-center ui-text-sm ui-text-gray-400">
            Verifying code...
          </div>
        )}

        <div className="ui-space-y-3">
          {mfaType === "sms" && onSendSMSCode && (
            <div className="ui-text-center ui-text-sm ui-text-gray-400">
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
          )}

          {onBackToMethodSelection && (
            <div className="ui-text-center ui-text-sm ui-text-gray-400">
              <button
                onClick={onBackToMethodSelection}
                disabled={isVerifying || isLoading}
                className="ui-text-[var(--ev-colors-highlight)] hover:ui-text-[var(--ev-colors-highlight)]/80 ui-transition-colors disabled:ui-opacity-50 ui-underline"
              >
                I can&apos;t use my phone right now.
              </button>
            </div>
          )}
        </div>

        <div className="ui-flex ui-gap-3">
          <button
            onClick={onCancel}
            disabled={isVerifying || isLoading}
            className="ui-flex-1 ui-py-3 ui-px-4 ui-border ui-border-gray-600 ui-text-gray-300 ui-rounded-lg ui-font-medium hover:ui-bg-gray-700 ui-transition-colors disabled:ui-opacity-50"
          >
            Back to Login
          </button>
        </div>
      </div>
    </div>
  );
}

function AuthenticatorIcon(): JSX.Element {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={24}
      height={24}
      fill="white"
      viewBox="0 0 24 24"
    >
      <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zM12 7c1.4 0 2.8 1.1 2.8 2.5V11c.6 0 1.2.6 1.2 1.2v3.5c0 .7-.6 1.3-1.2 1.3H9.2c-.6 0-1.2-.6-1.2-1.3v-3.5c0-.6.6-1.2 1.2-1.2V9.5C9.2 8.1 10.6 7 12 7zm0 1.2c-.8 0-1.5.7-1.5 1.5V11h3V9.7c0-.8-.7-1.5-1.5-1.5z" />
    </svg>
  );
}

function SMSIcon(): JSX.Element {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={24}
      height={24}
      fill="white"
      viewBox="0 0 24 24"
    >
      <path d="M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM9 11H7V9h2v2zm4 0h-2V9h2v2zm4 0h-2V9h2v2z" />
    </svg>
  );
}
