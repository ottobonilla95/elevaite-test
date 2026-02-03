"use client";
import { ElevaiteIcons } from "@repo/ui/components";
import type { JSX } from "react";
import { Suspense, useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { sendSmsCode } from "../../lib/mfaActions";
import "./page.scss";

type MfaMethod = "TOTP" | "SMS";

function QrCodeIcon(): JSX.Element {
  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="3" y="3" width="7" height="7" />
      <rect x="14" y="3" width="7" height="7" />
      <rect x="14" y="14" width="7" height="7" />
      <rect x="3" y="14" width="7" height="7" />
    </svg>
  );
}

function SmsIcon(): JSX.Element {
  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      <line x1="8" y1="9" x2="16" y2="9" />
      <line x1="8" y1="13" x2="14" y2="13" />
    </svg>
  );
}

function CheckIcon(): JSX.Element {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="3"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

function MfaMethodSelectionContent(): JSX.Element {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [selectedMethod, setSelectedMethod] = useState<MfaMethod | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Get available methods from URL params
  const methodsParam = searchParams.get("methods") ?? "";
  const maskedPhone = searchParams.get("phone") ?? "***-***-****";
  const availableMethods = methodsParam
    .split(",")
    .filter(Boolean) as MfaMethod[];

  // Check for stored credentials
  useEffect(() => {
    if (typeof window !== "undefined") {
      const storedEmail = sessionStorage.getItem("mfa_email");
      if (!storedEmail) {
        router.push("/login");
      }
    }
  }, [router]);

  const handleContinue = async (): Promise<void> => {
    if (!selectedMethod) return;

    const email = sessionStorage.getItem("mfa_email");
    const password = sessionStorage.getItem("mfa_password");

    if (!email || !password) {
      setError("Session expired. Please log in again.");
      router.push("/login");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      if (selectedMethod === "SMS") {
        const result = await sendSmsCode(email, password);
        if (!result.success) {
          setError(result.error ?? "Failed to send SMS code");
          setIsLoading(false);
          return;
        }
      }

      router.push(`/mfa-verify?method=${selectedMethod}`);
    } catch {
      setError("Something went wrong. Please try again.");
      setIsLoading(false);
    }
  };

  const handleContinueClick = (): void => {
    handleContinue().catch(() => {
      setError("Something went wrong. Please try again.");
      setIsLoading(false);
    });
  };

  const handleBackToLogin = (): void => {
    sessionStorage.removeItem("mfa_email");
    sessionStorage.removeItem("mfa_password");
    router.push("/login");
  };

  // If no methods available, show error state
  if (availableMethods.length === 0) {
    return (
      <div className="mfa-page-container">
        <div className="left-panel">
          <div className="logo-container">
            <ElevaiteIcons.SVGNavbarLogo />
          </div>

          <div className="form-content">
            <div className="mfa-heading">
              <h1>Invalid Request</h1>
              <p>No MFA methods available. Please try logging in again.</p>
            </div>

            <div className="mfa-continue-btn">
              <button
                type="button"
                className="active"
                onClick={() => {
                  router.push("/login");
                }}
              >
                Back to Login
              </button>
            </div>
          </div>

          <p className="copyright">
            <span className="gray">Copyright 2023 - </span>
            <a
              href="https://www.iopex.com/"
              target="_blank"
              rel="noopener noreferrer"
            >
              iOPEX Technologies
            </a>
          </p>
        </div>

        <div className="right-panel" />
      </div>
    );
  }

  return (
    <div className="mfa-page-container">
      <div className="left-panel">
        <div className="logo-container">
          <ElevaiteIcons.SVGNavbarLogo />
        </div>

        <div className="form-content">
          <div className="mfa-heading">
            <h1>Choose your Multi-Factor Authentication Method</h1>
            <p>
              Choose one of the following forms of multi-factor authentication.
            </p>
          </div>

          <div className="mfa-method-cards">
            {availableMethods.includes("TOTP") && (
              <button
                type="button"
                className={`mfa-method-card ${selectedMethod === "TOTP" ? "selected" : ""}`}
                onClick={() => {
                  setSelectedMethod("TOTP");
                }}
                disabled={isLoading}
              >
                <div className="icon-container">
                  <QrCodeIcon />
                </div>
                <div className="content">
                  <p className="title">Authenticator App</p>
                  <p className="description">
                    Get a code from your authenticator app (Google
                    Authenticator, Authy, etc.)
                  </p>
                </div>
                {selectedMethod === "TOTP" && (
                  <div className="checkmark">
                    <CheckIcon />
                  </div>
                )}
              </button>
            )}

            {availableMethods.includes("SMS") && (
              <button
                type="button"
                className={`mfa-method-card ${selectedMethod === "SMS" ? "selected" : ""}`}
                onClick={() => {
                  setSelectedMethod("SMS");
                }}
                disabled={isLoading}
              >
                <div className="icon-container">
                  <SmsIcon />
                </div>
                <div className="content">
                  <p className="title">Text Message (SMS)</p>
                  <p className="description">
                    We&apos;ll send a code to {maskedPhone}
                  </p>
                </div>
                {selectedMethod === "SMS" && (
                  <div className="checkmark">
                    <CheckIcon />
                  </div>
                )}
              </button>
            )}
          </div>

          {error ? <p className="mfa-error">{error}</p> : null}

          <div className="mfa-continue-btn">
            <button
              type="button"
              className={selectedMethod && !isLoading ? "active" : "disabled"}
              onClick={handleContinueClick}
              disabled={!selectedMethod || isLoading}
            >
              {isLoading ? "Please wait..." : "Continue"}
            </button>
          </div>

          <div className="mfa-back-link">
            <button type="button" onClick={handleBackToLogin}>
              Back to login
            </button>
          </div>
        </div>

        <p className="copyright">
          <span className="gray">Copyright 2023 - </span>
          <a
            href="https://www.iopex.com/"
            target="_blank"
            rel="noopener noreferrer"
          >
            iOPEX Technologies
          </a>
        </p>
      </div>

      <div className="right-panel" />
    </div>
  );
}

function MfaMethodSelection(): JSX.Element {
  return (
    <Suspense fallback={<div className="mfa-page-container" />}>
      <MfaMethodSelectionContent />
    </Suspense>
  );
}

export default MfaMethodSelection;
