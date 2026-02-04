"use client";
import type { JSX } from "react";
import { Suspense, useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Image from "next/image";
import { sendSmsCode } from "../../lib/mfaActions";
import { QrCodeIcon, SmsIcon, CheckIcon } from "../../components/icons";
import { Copyright } from "../../components/Copyright";
import { OrangePanel } from "../../components/OrangePanel";
import "./page.scss";

type MfaMethod = "TOTP" | "SMS";

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
            <Image
              src="/images/logos/logo.png"
              alt="ElevAIte"
              width={85}
              height={27}
              priority
            />
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

          <Copyright />
        </div>

        <OrangePanel />
      </div>
    );
  }

  return (
    <div className="mfa-page-container">
      <div className="left-panel">
        <div className="logo-container">
          <Image
            src="/images/logos/logo.png"
            alt="ElevAIte"
            width={85}
            height={27}
            priority
          />
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

        <Copyright />
      </div>

      <OrangePanel />
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
