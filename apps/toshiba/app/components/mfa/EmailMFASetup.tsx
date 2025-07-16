"use client";

import { useState } from "react";
import { MFACodeInput } from "./MFACodeInput";

interface EmailMFASetupProps {
  onSetup: () => Promise<void>;
  onVerify: (code: string) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
  error?: string;
  userEmail?: string;
}

export function EmailMFASetup({
  onSetup,
  onVerify,
  onCancel,
  isLoading = false,
  error,
  userEmail = "",
}: EmailMFASetupProps): JSX.Element {
  const [step, setStep] = useState<"setup" | "verify">("setup");
  const [isSettingUp, setIsSettingUp] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);

  const handleSetupSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    setIsSettingUp(true);
    try {
      await onSetup();
      setStep("verify");
    } catch (error) {
      // Error handling is done by parent component
    } finally {
      setIsSettingUp(false);
    }
  };

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

  const handleResendCode = async () => {
    setIsSettingUp(true);
    try {
      await onSetup();
    } catch (error) {
      // Error handling is done by parent component
    } finally {
      setIsSettingUp(false);
    }
  };

  const getMaskedEmail = (email: string) => {
    if (!email) return "";
    const [username, domain] = email.split("@");
    if (!username || !domain) return email;
    
    if (username.length <= 2) {
      return `${"*".repeat(username.length)}@${domain}`;
    }
    
    return `${username.slice(0, 2)}${"*".repeat(username.length - 2)}@${domain}`;
  };

  return (
    <div
      className="ui-max-w-md ui-mx-auto ui-p-6 ui-bg-[#1a1a1a] ui-rounded-lg"
      style={{ border: "none", textAlign: "center" }}
    >
      <div className="ui-text-center ui-mb-6">
        <h2 className="ui-text-2xl ui-font-bold ui-text-white ui-mb-2">
          {step === "setup"
            ? "Set up Email Authentication"
            : "Enter Verification Code"}
        </h2>
        <p className="ui-text-gray-400">
          {step === "setup"
            ? "Enable email-based two-factor authentication for your account."
            : "Enter the 6-digit code sent to your email."}
        </p>
      </div>

      {step === "setup" && (
        <form onSubmit={handleSetupSubmit} className="ui-space-y-6">
          <div className="ui-text-center ui-space-y-4">
            <div className="ui-text-white ui-font-medium">
              Verification codes will be sent to:
            </div>
            <div className="ui-text-[#E75F33] ui-font-medium ui-text-lg">
              {userEmail}
            </div>
          </div>

          <div
            className="ui-space-y-2"
            style={{ textAlign: "center", marginTop: "32px" }}
          >
            <div className="ui-text-sm ui-text-gray-400 ui-space-y-2">
              <div>1. We'll send a 6-digit code to your email</div>
              <div>2. Enter the code to verify your email</div>
              <div>3. You'll receive codes for future logins</div>
            </div>
          </div>

          <div
            style={{ marginTop: "32px", position: "relative", height: "48px" }}
          >
            <button
              type="button"
              onClick={onCancel}
              disabled={isSettingUp || isLoading}
              className="ui-py-3 ui-px-4 ui-bg-[#E75F33] ui-text-white ui-rounded-lg ui-font-medium hover:ui-bg-[#d54d26] ui-transition-colors disabled:ui-opacity-50"
              style={{ position: "absolute", left: "0" }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSettingUp || isLoading}
              className="ui-py-3 ui-px-4 ui-bg-[#E75F33] ui-text-white ui-rounded-lg ui-font-medium hover:ui-bg-[#d54d26] ui-transition-colors disabled:ui-opacity-50"
              style={{ position: "absolute", right: "0" }}
            >
              {isSettingUp ? "Setting up..." : "Send Code"}
            </button>
          </div>
        </form>
      )}

      {step === "verify" && (
        <div className="ui-space-y-6">
          <div className="ui-text-center">
            <p className="ui-text-gray-400 ui-text-sm ui-mb-4">
              We sent a verification code to:
            </p>
            <p className="ui-text-white ui-font-medium ui-mb-4">
              {getMaskedEmail(userEmail)}
            </p>
          </div>

          <div style={{ marginTop: "32px" }}>
            <MFACodeInput
              onComplete={handleCodeComplete}
              error={error}
              disabled={isVerifying || isLoading}
            />
          </div>

          {isVerifying && (
            <div className="ui-text-center ui-text-sm ui-text-gray-400">
              Verifying code...
            </div>
          )}

          <div
            className="ui-flex ui-justify-center"
            style={{ marginTop: "32px" }}
          >
            <button
              onClick={onCancel}
              disabled={isVerifying || isLoading}
              className="ui-py-3 ui-px-4 ui-bg-[#E75F33] ui-text-white ui-rounded-lg ui-font-medium hover:ui-bg-[#d54d26] ui-transition-colors disabled:ui-opacity-50"
            >
              Cancel
            </button>
          </div>

          <div className="ui-text-center">
            <button
              onClick={handleResendCode}
              disabled={isVerifying || isLoading || isSettingUp}
              className="ui-text-sm ui-text-[#E75F33] hover:ui-text-[#d54d26] ui-transition-colors disabled:ui-opacity-50"
            >
              {isSettingUp ? "Sending..." : "Didn't receive the code? Resend"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
