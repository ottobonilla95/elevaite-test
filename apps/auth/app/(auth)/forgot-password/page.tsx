"use client";
import type { JSX, FormEvent } from "react";
import { useState, useCallback } from "react";
import Link from "next/link";
import Image from "next/image";
import "./page.scss";

// Mail icon
function MailIcon(): JSX.Element {
  return (
    <svg
      width="17"
      height="14"
      viewBox="0 0 20 17"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        fill="currentColor"
        d="M18 .5H2C.9.5.01 1.4.01 2.5L0 14.5c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2v-12c0-1.1-.9-2-2-2Zm0 4-8 5-8-5v-2l8 5 8-5v2Z"
      />
    </svg>
  );
}

function ForgotPassword(): JSX.Element {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);
  const [debugResetUrl, setDebugResetUrl] = useState<string | null>(null);

  const callForgotPasswordApi = useCallback(
    async (emailAddress: string): Promise<void> => {
      const AUTH_API_URL = process.env.NEXT_PUBLIC_AUTH_API_URL;
      if (!AUTH_API_URL) {
        throw new Error("Server configuration error");
      }

      const response = await fetch(`${AUTH_API_URL}/api/auth/forgot-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email: emailAddress }),
      });

      if (!response.ok) {
        throw new Error("Failed to send reset link");
      }

      const data = (await response.json()) as { reset_url?: string };

      // If debug mode returned a reset URL, show it
      if (data.reset_url) {
        setDebugResetUrl(data.reset_url);
        // Also log to console for easy copying
        console.log("=".repeat(60));
        console.log("🔑 DEBUG: Password Reset URL");
        console.log(data.reset_url);
        console.log("=".repeat(60));
      }
    },
    [],
  );

  const handleSubmit = useCallback(
    async (e: FormEvent<HTMLFormElement>): Promise<void> => {
      e.preventDefault();
      setIsLoading(true);
      setError(null);
      setDebugResetUrl(null);

      try {
        await callForgotPasswordApi(email);
        setIsSubmitted(true);
      } catch {
        setError("Failed to send reset link. Please try again.");
      } finally {
        setIsLoading(false);
      }
    },
    [email, callForgotPasswordApi],
  );

  const handleResend = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    setError(null);
    setResendSuccess(false);
    setDebugResetUrl(null);

    try {
      await callForgotPasswordApi(email);
      setResendSuccess(true);
      setTimeout(() => {
        setResendSuccess(false);
      }, 3000);
    } catch {
      setError("Failed to resend link. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }, [email, callForgotPasswordApi]);

  const handleFormSubmit = (e: FormEvent<HTMLFormElement>): void => {
    handleSubmit(e).catch(() => {
      setError("Something went wrong. Please try again.");
      setIsLoading(false);
    });
  };

  const handleResendClick = (): void => {
    handleResend().catch(() => {
      setError("Failed to resend link. Please try again.");
      setIsLoading(false);
    });
  };

  return (
    <div className="forgot-password-container">
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
          {isSubmitted ? (
            // Success state - Check your email
            <>
              <div className="forgot-heading">
                <h1>Check your email</h1>
                <p>
                  We have sent a password recover instructions to your email.
                </p>
              </div>

              {/* Debug URL display - only shown when backend returns it */}
              {debugResetUrl ? (
                <div className="debug-url-box">
                  <p>
                    <strong>🔧 Debug Mode - Reset URL:</strong>
                  </p>
                  <a
                    href={debugResetUrl}
                    style={{ wordBreak: "break-all", color: "#ff681f" }}
                  >
                    {debugResetUrl}
                  </a>
                </div>
              ) : null}

              <div className="forgot-form">
                {resendSuccess ? (
                  <p className="resend-success">Link sent successfully!</p>
                ) : null}

                {error ? <p className="form-error">{error}</p> : null}

                <button
                  type="button"
                  className="submit-btn"
                  onClick={handleResendClick}
                  disabled={isLoading}
                >
                  {isLoading ? "Sending..." : "Resend link"}
                </button>
              </div>
            </>
          ) : (
            // Form state
            <>
              <div className="forgot-heading">
                <h1>Forgot Password</h1>
                <p>
                  Enter the email associated with your account and we will send
                  an email with instructions to reset your password.
                </p>
              </div>

              <form className="forgot-form" onSubmit={handleFormSubmit}>
                <div className="input-group">
                  <label htmlFor="email">Email Address*</label>
                  <div className="input-wrapper">
                    <span className="input-icon">
                      <MailIcon />
                    </span>
                    <div className="divider" />
                    <input
                      id="email"
                      type="email"
                      placeholder="john.smith@gmail.com"
                      value={email}
                      onChange={(e) => {
                        setEmail(e.target.value);
                      }}
                      required
                      disabled={isLoading}
                    />
                  </div>
                </div>

                {error ? <p className="form-error">{error}</p> : null}

                <button
                  type="submit"
                  className="submit-btn"
                  disabled={isLoading || !email}
                >
                  {isLoading ? "Sending..." : "Send Link"}
                </button>
              </form>

              <div className="back-to-signin">
                <p>Remember your password?</p>
                <Link href="/login">Sign In</Link>
              </div>
            </>
          )}
        </div>

        <p className="copyright">
          Copyright 2023 -{" "}
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

export default ForgotPassword;
