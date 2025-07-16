"use client";

import { useState } from "react";
import { AppIcon, SMSIcon, EmailIcon } from "../icons";
import { getMFAConfig } from "../../lib/mfaConfig";

interface MFAMethodSelectionProps {
  email: string;
  password: string;
  availableMethods: {
    totp: boolean;
    sms: boolean;
    email: boolean;
  };
  onMethodSelect: (method: "totp" | "sms" | "email") => void;
  onCancel: () => void;
  phoneNumber?: string;
  userEmail?: string;
  isLoading?: boolean;
}

export function MFAMethodSelection({
  email,
  password: _password,
  availableMethods,
  onMethodSelect,
  onCancel,
  phoneNumber,
  userEmail,
  isLoading = false,
}: MFAMethodSelectionProps): JSX.Element {
  const [selectedMethod, setSelectedMethod] = useState<
    "totp" | "sms" | "email" | null
  >(null);

  const mfaConfig = getMFAConfig();

  const filteredMethods = {
    totp: availableMethods.totp && mfaConfig.totp,
    sms: availableMethods.sms && mfaConfig.sms,
    email: availableMethods.email && mfaConfig.email,
  };

  const handleMethodClick = (method: "totp" | "sms" | "email") => {
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

  // Get email for Email display
  const getMaskedEmail = () => {
    const emailToMask = userEmail || email;
    if (!emailToMask) return "***@***.com";

    const [username, domain] = emailToMask.split("@");
    if (!username || !domain) return emailToMask;

    if (username.length <= 2) {
      return `${"*".repeat(username.length)}@${domain}`;
    }

    return `${username.slice(0, 2)}${"*".repeat(username.length - 2)}@${domain}`;
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
      <div className="ui-space-y-4">
        {filteredMethods.email && (
          <MFAMethodButton
            onClick={() => handleMethodClick("email")}
            disabled={isLoading}
            icon={<EmailIcon width={50} height={50} />}
            title="Email"
            hint={`We'll send a code to your email ${getMaskedEmail()}`}
          />
        )}

        {filteredMethods.totp && (
          <MFAMethodButton
            onClick={() => handleMethodClick("totp")}
            disabled={isLoading}
            icon={<AppIcon width={50} height={50} />}
            title="Authenticator App"
            hint="Get a code from your authenticator app."
          />
        )}

        {filteredMethods.sms && (
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
        marginTop: "25px",
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
