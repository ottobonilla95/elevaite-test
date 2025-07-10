"use client";

import { useState } from "react";
import { AppIcon, SMSIcon } from "../icons";

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
            icon={<AppIcon width={50} height={50} />}
            title="Authenticator App"
            hint="Get a code from your authenticator app."
          />
        )}

        {availableMethods.sms && (
          <MFAMethodButton
            onClick={() => handleMethodClick("sms")}
            disabled={isLoading}
            icon={<SMSIcon width={50} height={50} />}
            title="Text Message (SMS)"
            hint={`We'll send a code to your phone ${getMaskedPhoneNumber()} (you can view this at the settings page for change password)`}
          />
        )}
      </div>
    </div>
  );
}

interface MFAMethodButtonProps {
  onClick: () => void;
  disabled: boolean;
  icon: JSX.Element;
  title: string;
  hint: string;
}

function MFAMethodButton({
  onClick,
  disabled,
  icon,
  title,
  hint,
}: MFAMethodButtonProps): JSX.Element {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        border: "2px solid #6b7280",
        width: "75%",
        height: "90px",
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
          marginLeft: "16px",
        }}
      >
        {icon}
      </div>
      <div className="ui-flex-1" style={{ textAlign: "left" }}>
        <h3
          className="ui-text-white ui-font-semibold ui-text-lg ui-mb-1"
          style={{ textAlign: "left" }}
        >
          {title}
        </h3>
        <p
          className="ui-text-gray-400 ui-text-sm"
          style={{ textAlign: "left" }}
        >
          {hint}
        </p>
      </div>
    </button>
  );
}
