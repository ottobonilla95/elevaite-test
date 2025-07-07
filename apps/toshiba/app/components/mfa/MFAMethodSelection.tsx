"use client";

import { useState } from "react";

interface MFAMethodSelectionProps {
  email: string;
  password: string;
  availableMethods: {
    totp: boolean;
    sms: boolean;
  };
  onMethodSelect: (method: "totp" | "sms") => void;
  onCancel: () => void;
  phoneNumber?: string;
  isLoading?: boolean;
}

export function MFAMethodSelection({
  email,
  password: _password,
  availableMethods,
  onMethodSelect,
  onCancel,
  phoneNumber,
  isLoading = false,
}: MFAMethodSelectionProps): JSX.Element {
  const [selectedMethod, setSelectedMethod] = useState<"totp" | "sms" | null>(
    null
  );

  const handleMethodClick = (method: "totp" | "sms") => {
    if (isLoading) return;
    setSelectedMethod(method);
    onMethodSelect(method);
  };

  // Get phone number for SMS display (mask it)
  const getMaskedPhoneNumber = () => {
    if (!phoneNumber) return "***-***-5499";

    // Mask the phone number, showing only last 4 digits
    const cleaned = phoneNumber.replace(/\D/g, "");
    if (cleaned.length >= 4) {
      const lastFour = cleaned.slice(-4);
      return `***-***-${lastFour}`;
    }
    return "***-***-5499";
  };

  return (
    <div className="ui-w-full ui-max-w-md ui-mx-auto">
      {/* Header */}
      <div className="ui-text-left ui-mb-8">
        <h1 className="ui-text-3xl ui-font-bold ui-text-white ui-mb-2">
          Verify your identity
        </h1>
        <p className="ui-text-gray-400">
          Choose one of the following forms of multi-factor authentication.
        </p>
      </div>

      {/* MFA Method Options with reduced top gap and left alignment */}
      <div style={{ marginTop: "25px" }} className="ui-space-y-4">
        {availableMethods.totp && (
          <MFAMethodButton
            onClick={() => handleMethodClick("totp")}
            disabled={isLoading}
            icon={<AuthenticatorIcon />}
            text="Use a verification code"
          />
        )}

        {availableMethods.sms && (
          <MFAMethodButton
            onClick={() => handleMethodClick("sms")}
            disabled={isLoading}
            icon={<SMSIcon />}
            text={`Text ${getMaskedPhoneNumber()}`}
          />
        )}
      </div>
    </div>
  );
}

function AuthenticatorIcon(): JSX.Element {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={28}
      height={28}
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
      width={28}
      height={28}
      fill="white"
      viewBox="0 0 24 24"
    >
      <path d="M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM9 11H7V9h2v2zm4 0h-2V9h2v2zm4 0h-2V9h2v2z" />
    </svg>
  );
}

interface MFAMethodButtonProps {
  onClick: () => void;
  disabled: boolean;
  icon: JSX.Element;
  text: string;
}

function MFAMethodButton({
  onClick,
  disabled,
  icon,
  text,
}: MFAMethodButtonProps): JSX.Element {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        border: "2px solid #6b7280",
        width: "75%",
        height: "75px",
      }}
      className={`
        ui-py-12 ui-px-6 ui-flex ui-items-center ui-gap-6 ui-text-left ui-transition-all
        ui-rounded-lg ui-bg-transparent
        hover:ui-border-[var(--ev-colors-highlight)]
        ${disabled ? "ui-opacity-50 ui-cursor-not-allowed" : "ui-cursor-pointer"}
      `}
    >
      <div
        className="ui-p-3 ui-rounded-lg ui-flex-shrink-0"
        style={{
          backgroundColor: "var(--ev-colors-highlight)",
          marginLeft: "16px",
        }}
      >
        {icon}
      </div>
      <div className="ui-flex-1">
        <h3 className="ui-text-white ui-font-semibold ui-text-lg">{text}</h3>
      </div>
    </button>
  );
}
