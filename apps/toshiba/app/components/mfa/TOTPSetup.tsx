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
    <div
      className="ui-max-w-md ui-mx-auto ui-p-6 ui-bg-[#1a1a1a] ui-rounded-lg"
      style={{ border: "none", textAlign: "center" }}
    >
      <div className="ui-text-center ui-mb-6">
        <h2 className="ui-text-2xl ui-font-bold ui-text-white ui-mb-2">
          {step === "setup"
            ? "Set up TOTP Authentication"
            : "Enter Verification Code"}
        </h2>
        <p className="ui-text-gray-400">
          {step === "setup"
            ? "Scan the QR code with your authenticator app or enter the secret manually."
            : "Enter the 6-digit code from your authenticator app."}
        </p>
      </div>

      {step === "setup" && (
        <div className="ui-space-y-6">
          {/* QR Code */}
          <div className="ui-text-center" style={{ margin: "32px 0" }}>
            <QRCodeDisplay value={qrCodeUri} size={200} />
          </div>

          {/* Manual Secret */}
          <div style={{ textAlign: "center", marginBottom: "24px" }}>
            <div style={{ marginBottom: "16px" }}>
              <label className="ui-block ui-text-sm ui-font-medium ui-text-gray-300">
                Or enter this secret manually
              </label>
            </div>
            <div
              style={{
                position: "relative",
                maxWidth: "400px",
                margin: "0 auto",
                display: "inline-block",
              }}
            >
              <code
                className="ui-bg-[#161616] ui-rounded ui-text-sm ui-text-white ui-font-mono"
                style={{
                  border: "1px solid var(--ev-colors-highlight)",
                  padding: "16px 48px 16px 16px",
                  display: "block",
                  wordBreak: "break-all",
                  width: "100%",
                }}
              >
                {secret}
              </code>
              <button
                onClick={copySecret}
                title="Copy secret"
                className="ui-text-white ui-rounded ui-text-sm ui-transition-colors"
                style={{
                  position: "absolute",
                  right: "8px",
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "transparent",
                  border: "none",
                  cursor: "pointer",
                  padding: "6px",
                  width: "28px",
                  height: "28px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "var(--ev-colors-secondaryText)",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor =
                    "var(--ev-colors-secondary)";
                  e.currentTarget.style.color = "var(--ev-colors-text)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = "transparent";
                  e.currentTarget.style.color =
                    "var(--ev-colors-secondaryText)";
                }}
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                </svg>
              </button>
            </div>
          </div>

          {/* Instructions */}
          <div className="ui-space-y-2" style={{ textAlign: "center" }}>
            <div className="ui-text-sm ui-text-gray-400 ui-space-y-2">
              <div>
                1. Install an authenticator app (Google Authenticator, Authy,
                etc.)
              </div>
              <div>2. Scan the QR code or enter the secret manually</div>
              <div>3. Enter the 6-digit code from your app below</div>
            </div>
          </div>

          {/* Action Buttons */}
          <div
            style={{ marginTop: "32px", position: "relative", height: "48px" }}
          >
            <button
              onClick={onCancel}
              className="ui-py-3 ui-px-4 ui-bg-[#E75F33] ui-text-white ui-rounded-lg ui-font-medium hover:ui-bg-[#d54d26] ui-transition-colors"
              style={{ position: "absolute", left: "0" }}
            >
              Cancel
            </button>
            <button
              onClick={() => setStep("verify")}
              className="ui-py-3 ui-px-4 ui-bg-[#E75F33] ui-text-white ui-rounded-lg ui-font-medium hover:ui-bg-[#d54d26] ui-transition-colors"
              style={{ position: "absolute", right: "0" }}
            >
              Continue to Verification
            </button>
          </div>
        </div>
      )}

      {step === "verify" && (
        <div className="ui-space-y-6">
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
        </div>
      )}
    </div>
  );
}
