"use client";

import { useState } from "react";
import { QRCodeDisplay } from "./QRCodeDisplay";
import { MFACodeInput } from "./MFACodeInput";

interface TOTPSetupProps {
  secret: string;
  qrCodeUri: string;
  onVerify: (code: string) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
  error?: string;
}

export function TOTPSetup({
  secret,
  qrCodeUri,
  onVerify,
  onCancel,
  isLoading = false,
  error,
}: TOTPSetupProps): JSX.Element {
  const [step, setStep] = useState<"setup" | "verify">("setup");
  const [isVerifying, setIsVerifying] = useState(false);

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

  const copySecret = async () => {
    try {
      await navigator.clipboard.writeText(secret);
      // You could add a toast notification here
    } catch (error) {
      console.error("Failed to copy secret:", error);
    }
  };

  return (
    <div className="ui-max-w-md ui-mx-auto ui-p-6 ui-bg-[#1a1a1a] ui-rounded-lg ui-border ui-border-gray-700">
      <div className="ui-text-center ui-mb-6">
        <h2 className="ui-text-2xl ui-font-bold ui-text-white ui-mb-2">
          Set up TOTP Authentication
        </h2>
        <p className="ui-text-gray-400">
          Scan the QR code with your authenticator app or enter the secret
          manually
        </p>
      </div>

      {step === "setup" && (
        <div className="ui-space-y-6">
          {/* QR Code */}
          <div className="ui-text-center">
            <QRCodeDisplay value={qrCodeUri} size={200} />
          </div>

          {/* Manual Secret */}
          <div className="ui-space-y-2">
            <label className="ui-block ui-text-sm ui-font-medium ui-text-gray-300">
              Or enter this secret manually:
            </label>
            <div className="ui-flex ui-items-center ui-gap-2">
              <code className="ui-flex-1 ui-p-2 ui-bg-[#161616] ui-border ui-border-gray-600 ui-rounded ui-text-sm ui-text-white ui-font-mono ui-break-all">
                {secret}
              </code>
              <button
                onClick={copySecret}
                className="ui-px-3 ui-py-2 ui-bg-[#E75F33] ui-text-white ui-rounded ui-text-sm hover:ui-bg-[#d54d26] ui-transition-colors"
              >
                Copy
              </button>
            </div>
          </div>

          {/* Instructions */}
          <div className="ui-space-y-2">
            <h3 className="ui-text-sm ui-font-medium ui-text-gray-300">
              Instructions:
            </h3>
            <ol className="ui-text-sm ui-text-gray-400 ui-space-y-1 ui-list-decimal ui-list-inside">
              <li>
                Install an authenticator app (Google Authenticator, Authy, etc.)
              </li>
              <li>Scan the QR code or enter the secret manually</li>
              <li>Enter the 6-digit code from your app below</li>
            </ol>
          </div>

          {/* Continue Button */}
          <button
            onClick={() => setStep("verify")}
            className="ui-w-full ui-py-3 ui-px-4 ui-bg-[#E75F33] ui-text-white ui-rounded-lg ui-font-medium hover:ui-bg-[#d54d26] ui-transition-colors"
          >
            Continue to Verification
          </button>
        </div>
      )}

      {step === "verify" && (
        <div className="ui-space-y-6">
          <div className="ui-text-center">
            <h3 className="ui-text-lg ui-font-medium ui-text-white ui-mb-2">
              Enter Verification Code
            </h3>
            <p className="ui-text-gray-400 ui-text-sm">
              Enter the 6-digit code from your authenticator app.
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
              onClick={() => setStep("setup")}
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
        </div>
      )}
    </div>
  );
}
