"use client";

import { useState } from "react";
import { PhoneNumberInput } from "./PhoneNumberInput";
import { MFACodeInput } from "./MFACodeInput";

interface SMSMFASetupProps {
  onSetup: (phoneNumber: string) => Promise<void>;
  onVerify: (code: string) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
  error?: string;
  initialPhoneNumber?: string;
}

export function SMSMFASetup({
  onSetup,
  onVerify,
  onCancel,
  isLoading = false,
  error,
  initialPhoneNumber = "",
}: SMSMFASetupProps): JSX.Element {
  const [phoneNumber, setPhoneNumber] = useState(initialPhoneNumber);
  const [step, setStep] = useState<"phone" | "verify">("phone");
  const [isSettingUp, setIsSettingUp] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);

  const handlePhoneSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!phoneNumber.trim()) return;

    setIsSettingUp(true);
    try {
      await onSetup(phoneNumber);
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

  const isPhoneValid = () => {
    const digits = phoneNumber.replace(/\D/g, "");
    return digits.length >= 10 && digits.length <= 15;
  };

  return (
    <div className="ui-max-w-md ui-mx-auto ui-p-6 ui-bg-[#1a1a1a] ui-rounded-lg ui-border ui-border-gray-700">
      <div className="ui-text-center ui-mb-6">
        <h2 className="ui-text-2xl ui-font-bold ui-text-white ui-mb-2">
          Set up SMS Authentication
        </h2>
        <p className="ui-text-gray-400">
          {step === "phone"
            ? "Enter your phone number to receive verification codes"
            : "Enter the verification code sent to your phone"}
        </p>
      </div>

      {step === "phone" && (
        <form onSubmit={handlePhoneSubmit} className="ui-space-y-6">
          <PhoneNumberInput
            value={phoneNumber}
            onChange={setPhoneNumber}
            error={error}
            disabled={isSettingUp || isLoading}
            placeholder="Enter your phone number"
          />

          <div className="ui-space-y-2">
            <h3 className="ui-text-sm ui-font-medium ui-text-gray-300">
              How it works:
            </h3>
            <ul className="ui-text-sm ui-text-gray-400 ui-space-y-1 ui-list-disc ui-list-inside">
              <li>We'll send a 6-digit code to your phone</li>
              <li>Enter the code to verify your phone number</li>
              <li>You'll receive codes for future logins</li>
            </ul>
          </div>

          <div className="ui-flex ui-gap-3">
            <button
              type="button"
              onClick={onCancel}
              disabled={isSettingUp || isLoading}
              className="ui-flex-1 ui-py-3 ui-px-4 ui-border ui-border-gray-600 ui-text-gray-300 ui-rounded-lg ui-font-medium hover:ui-bg-gray-700 ui-transition-colors disabled:ui-opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!isPhoneValid() || isSettingUp || isLoading}
              className="ui-flex-1 ui-py-3 ui-px-4 ui-bg-[#E75F33] ui-text-white ui-rounded-lg ui-font-medium hover:ui-bg-[#d54d26] ui-transition-colors disabled:ui-opacity-50 disabled:ui-bg-gray-600"
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
              {phoneNumber}
            </p>
          </div>

          <MFACodeInput
            onComplete={handleCodeComplete}
            error={error}
            disabled={isVerifying || isLoading}
          />

          {isVerifying && (
            <div className="ui-text-center ui-text-sm ui-text-gray-400">
              Verifying code...
            </div>
          )}

          <div className="ui-flex ui-gap-3">
            <button
              onClick={() => setStep("phone")}
              disabled={isVerifying || isLoading}
              className="ui-flex-1 ui-py-3 ui-px-4 ui-border ui-border-gray-600 ui-text-gray-300 ui-rounded-lg ui-font-medium hover:ui-bg-gray-700 ui-transition-colors disabled:ui-opacity-50"
            >
              Back
            </button>
            <button
              onClick={onCancel}
              disabled={isVerifying || isLoading}
              className="ui-flex-1 ui-py-3 ui-px-4 ui-border ui-border-gray-600 ui-text-gray-300 ui-rounded-lg ui-font-medium hover:ui-bg-gray-700 ui-transition-colors disabled:ui-opacity-50"
            >
              Cancel
            </button>
          </div>

          <div className="ui-text-center">
            <button
              onClick={() =>
                handlePhoneSubmit({
                  preventDefault: () => {},
                } as React.FormEvent)
              }
              disabled={isVerifying || isLoading}
              className="ui-text-sm ui-text-[#E75F33] hover:ui-text-[#d54d26] ui-transition-colors disabled:ui-opacity-50"
            >
              Didn't receive the code? Resend
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
