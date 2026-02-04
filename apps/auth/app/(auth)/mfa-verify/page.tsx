"use client";
import { CommonButton } from "@repo/ui/components";
import type { JSX, KeyboardEvent, ClipboardEvent, ChangeEvent } from "react";
import { Suspense, useState, useEffect, useCallback, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Image from "next/image";
import { signIn } from "next-auth/react";
import {
  verifyTotpCode,
  verifySmsCode,
  sendSmsCode,
} from "../../lib/mfaActions";
import { Copyright } from "../../components/Copyright";
import { OrangePanel } from "../../components/OrangePanel";
import "./page.scss";

type MfaMethod = "TOTP" | "SMS";

function MfaVerificationContent(): JSX.Element {
  const router = useRouter();
  const searchParams = useSearchParams();
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  const [code, setCode] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resendSuccess, setResendSuccess] = useState(false);

  const method = (searchParams.get("method") ?? "TOTP") as MfaMethod;
  const digits = code.padEnd(6, "").split("").slice(0, 6);

  // Auto-focus first input on mount
  useEffect(() => {
    if (inputRefs.current[0]) {
      inputRefs.current[0].focus();
    }
  }, []);

  // Check for stored credentials
  useEffect(() => {
    if (typeof window !== "undefined") {
      const storedEmail = sessionStorage.getItem("mfa_email");
      if (!storedEmail) {
        router.push("/login");
      }
    }
  }, [router]);

  const handleVerify = useCallback(async (): Promise<void> => {
    if (code.length !== 6) return;

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
      const verifyFn = method === "TOTP" ? verifyTotpCode : verifySmsCode;
      const result = await verifyFn(email, password, code);

      if (!result.success) {
        setError(result.error ?? "Invalid code. Please try again.");
        setCode("");
        setIsLoading(false);
        return;
      }

      sessionStorage.removeItem("mfa_email");
      sessionStorage.removeItem("mfa_password");

      const signInResult = await signIn("credentials", {
        email,
        password,
        redirect: false,
      });

      if (signInResult?.error) {
        window.location.href = process.env.NEXT_PUBLIC_ELEVAITE_HOMEPAGE ?? "/";
      } else {
        window.location.href = process.env.NEXT_PUBLIC_ELEVAITE_HOMEPAGE ?? "/";
      }
    } catch {
      setError("Verification failed. Please try again.");
      setIsLoading(false);
    }
  }, [code, method, router]);

  // Auto-submit when 6 digits entered
  useEffect(() => {
    if (code.length === 6 && !isLoading) {
      handleVerify().catch(() => {
        setError("Verification failed. Please try again.");
        setIsLoading(false);
      });
    }
  }, [code, isLoading, handleVerify]);

  const handleInputChange = (
    index: number,
    e: ChangeEvent<HTMLInputElement>,
  ): void => {
    const inputValue = e.target.value;

    if (inputValue.length > 1) return;
    if (inputValue && !/^\d$/.test(inputValue)) return;

    const newDigits = [...digits];
    newDigits[index] = inputValue;
    const newValue = newDigits.join("").replace(/\s/g, "");
    setCode(newValue);

    if (inputValue && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (
    index: number,
    e: KeyboardEvent<HTMLInputElement>,
  ): void => {
    if (e.key === "Backspace") {
      if (!digits[index] && index > 0) {
        inputRefs.current[index - 1]?.focus();
        const newDigits = [...digits];
        newDigits[index - 1] = "";
        setCode(newDigits.join("").replace(/\s/g, ""));
      }
    }

    if (e.key === "ArrowLeft" && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
    if (e.key === "ArrowRight" && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handlePaste = (e: ClipboardEvent<HTMLInputElement>): void => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData("text");
    const pastedDigits = pastedData.replace(/\D/g, "").slice(0, 6);

    if (pastedDigits) {
      setCode(pastedDigits);
      const focusIndex = Math.min(pastedDigits.length, 5);
      inputRefs.current[focusIndex]?.focus();
    }
  };

  const handleResend = async (): Promise<void> => {
    if (method !== "SMS") return;

    const email = sessionStorage.getItem("mfa_email");
    const password = sessionStorage.getItem("mfa_password");

    if (!email || !password) {
      setError("Session expired. Please log in again.");
      router.push("/login");
      return;
    }

    setIsResending(true);
    setError(null);
    setResendSuccess(false);

    try {
      const result = await sendSmsCode(email, password);

      if (!result.success) {
        setError(result.error ?? "Failed to resend code");
      } else {
        setResendSuccess(true);
        setTimeout(() => {
          setResendSuccess(false);
        }, 3000);
      }
    } catch {
      setError("Failed to resend code. Please try again.");
    } finally {
      setIsResending(false);
    }
  };

  const handleVerifyClick = (): void => {
    handleVerify().catch(() => {
      setError("Verification failed. Please try again.");
      setIsLoading(false);
    });
  };

  const handleResendClick = (): void => {
    handleResend().catch(() => {
      setError("Failed to resend code. Please try again.");
      setIsResending(false);
    });
  };

  const handleBackClick = (): void => {
    router.back();
  };

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
            <h1>Enter verification code</h1>
            <p>Enter the 6-digit code sent to you to log into your account.</p>
          </div>

          <div className="mfa-code-input">
            <div className="code-inputs">
              {[0, 1, 2, 3, 4, 5].map((index) => (
                <input
                  key={index}
                  ref={(el) => {
                    inputRefs.current[index] = el;
                  }}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digits[index] ?? ""}
                  onChange={(e) => {
                    handleInputChange(index, e);
                  }}
                  onKeyDown={(e) => {
                    handleKeyDown(index, e);
                  }}
                  onPaste={handlePaste}
                  onFocus={(e) => {
                    e.target.select();
                  }}
                  disabled={isLoading}
                  className={error ? "error" : ""}
                  aria-label={`Digit ${index + 1} of 6`}
                />
              ))}
            </div>
            {error ? <p className="error-message">{error}</p> : null}
          </div>

          {resendSuccess ? (
            <p className="mfa-success-message">Code sent successfully!</p>
          ) : null}

          <div className="mfa-verify-btn">
            <CommonButton
              overrideClass
              className={
                code.length === 6 && !isLoading ? "active" : "disabled"
              }
              onClick={handleVerifyClick}
              disabled={code.length !== 6 || isLoading}
            >
              {isLoading ? "Verifying..." : "Verify"}
            </CommonButton>
          </div>

          <div className="mfa-help-links">
            <p className="resend-text">
              <span className="bold">
                Didn&apos;t receive a sign-in request?
              </span>
              {method === "SMS" ? (
                <CommonButton
                  overrideClass
                  onClick={handleResendClick}
                  disabled={isResending}
                >
                  {isResending ? "Sending..." : "Resend request."}
                </CommonButton>
              ) : (
                <span className="gray">Check your authenticator app.</span>
              )}
            </p>
            <CommonButton
              overrideClass
              className="try-another"
              onClick={handleBackClick}
            >
              Try another method
            </CommonButton>
          </div>
        </div>

        <Copyright />
      </div>

      <OrangePanel />
    </div>
  );
}

function MfaVerification(): JSX.Element {
  return (
    <Suspense fallback={<div className="mfa-page-container" />}>
      <MfaVerificationContent />
    </Suspense>
  );
}

export default MfaVerification;
