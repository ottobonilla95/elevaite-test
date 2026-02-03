"use client";

import type { JSX } from "react";
import { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Image from "next/image";
import { resetPassword } from "../../lib/actions";
import "./page.scss";

// Loading component for Suspense fallback
function ResetPasswordLoading(): JSX.Element {
  return (
    <div className="reset-password-container">
      <div className="reset-password-inner">
        <div className="form-panel">
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
            <div className="form-wrapper">
              <div className="headings">
                <h1>Loading...</h1>
              </div>
            </div>
          </div>
        </div>
        <div className="orange-panel" />
      </div>
    </div>
  );
}

// Main component wrapped in Suspense boundary
export default function ResetPassword(): JSX.Element {
  return (
    <Suspense fallback={<ResetPasswordLoading />}>
      <ResetPasswordContent />
    </Suspense>
  );
}

function ResetPasswordContent(): JSX.Element {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [isSuccess, setIsSuccess] = useState(false);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleResetPassword = async (): Promise<void> => {
    if (!token) {
      setError("Invalid or missing reset token");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("Both passwords must match.");
      return;
    }

    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      const result = await resetPassword(token, newPassword);
      if (result.success) {
        setIsSuccess(true);
      } else {
        setError(result.error || "Failed to reset password. Please try again.");
      }
    } catch {
      setError("Failed to reset password. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSignIn = (): void => {
    window.location.href = "/login";
  };

  // No token provided - show error state
  if (!token) {
    return (
      <div className="reset-password-container">
        <div className="reset-password-inner">
          <div className="form-panel">
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
              <div className="form-wrapper">
                <div className="headings">
                  <h1>Invalid Reset Link</h1>
                  <p>
                    This password reset link is invalid or has expired. Please
                    request a new password reset.
                  </p>
                </div>
                <div className="form-fields">
                  <button
                    className="submit-button"
                    onClick={() => {
                      window.location.href = "/forgot-password";
                    }}
                    type="button"
                  >
                    Request New Reset Link
                  </button>
                </div>
              </div>
            </div>

            <div className="copyright">
              <span>Copyright 2023 - </span>
              <a
                href="https://www.iopex.com/"
                target="_blank"
                rel="noopener noreferrer"
              >
                iOPEX Technologies
              </a>
            </div>
          </div>

          <div className="orange-panel" />
        </div>
      </div>
    );
  }

  // Success state
  if (isSuccess) {
    return (
      <div className="reset-password-container">
        <div className="reset-password-inner">
          <div className="form-panel">
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
              <div className="form-wrapper">
                <div className="headings">
                  <h1>Password Reset</h1>
                  <p>Log into your account with your new password.</p>
                </div>
                <div className="form-fields">
                  <button
                    className="submit-button"
                    onClick={handleSignIn}
                    type="button"
                  >
                    Sign in
                  </button>
                </div>
              </div>
            </div>

            <div className="copyright">
              <span>Copyright 2023 - </span>
              <a
                href="https://www.iopex.com/"
                target="_blank"
                rel="noopener noreferrer"
              >
                iOPEX Technologies
              </a>
            </div>
          </div>

          <div className="orange-panel" />
        </div>
      </div>
    );
  }

  return (
    <div className="reset-password-container">
      <div className="reset-password-inner">
        {/* Left Panel - Form */}
        <div className="form-panel">
          {/* Logo */}
          <div className="logo-container">
            <Image
              src="/images/logos/logo.png"
              alt="ElevAIte"
              width={85}
              height={27}
              priority
            />
          </div>

          {/* Form Content */}
          <div className="form-content">
            <div className="form-wrapper">
              <div className="headings">
                <h1>Reset Password</h1>
                <p>
                  Your new password must be different from previously used
                  passwords.
                </p>
              </div>

              <div className="form-fields">
                {/* Password Field */}
                <div className="input-group">
                  <label htmlFor="password">Password*</label>
                  <div className="input-wrapper">
                    <span className="input-icon">
                      <LockIcon />
                    </span>
                    <div className="divider" />
                    <input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      value={newPassword}
                      onChange={(e) => {
                        setNewPassword(e.target.value);
                      }}
                      placeholder=""
                      required
                    />
                    <button
                      type="button"
                      className="eye-button"
                      onClick={() => {
                        setShowPassword(!showPassword);
                      }}
                      aria-label={
                        showPassword ? "Hide password" : "Show password"
                      }
                    >
                      <EyeOffIcon />
                    </button>
                  </div>
                  <span className="hint">Must be at least 8 characters.</span>
                </div>

                {/* Confirm Password Field */}
                <div className="input-group">
                  <label htmlFor="confirmPassword">Confirm Password*</label>
                  <div className="input-wrapper">
                    <span className="input-icon">
                      <LockIcon />
                    </span>
                    <div className="divider" />
                    <input
                      id="confirmPassword"
                      type={showConfirmPassword ? "text" : "password"}
                      value={confirmPassword}
                      onChange={(e) => {
                        setConfirmPassword(e.target.value);
                      }}
                      placeholder=""
                      required
                    />
                    <button
                      type="button"
                      className="eye-button"
                      onClick={() => {
                        setShowConfirmPassword(!showConfirmPassword);
                      }}
                      aria-label={
                        showConfirmPassword ? "Hide password" : "Show password"
                      }
                    >
                      <EyeOffIcon />
                    </button>
                  </div>
                  {error ? <span className="error-text">{error}</span> : null}
                </div>

                <button
                  className="submit-button"
                  onClick={handleResetPassword}
                  disabled={isSubmitting}
                  type="button"
                >
                  {isSubmitting ? "Resetting..." : "Confirm Password Change"}
                </button>
              </div>
            </div>
          </div>

          {/* Copyright */}
          <div className="copyright">
            <span>Copyright 2023 - </span>
            <a
              href="https://www.iopex.com/"
              target="_blank"
              rel="noopener noreferrer"
            >
              iOPEX Technologies
            </a>
          </div>
        </div>

        {/* Right Panel - Orange */}
        <div className="orange-panel" />
      </div>
    </div>
  );
}

function LockIcon(): JSX.Element {
  return (
    <svg
      width="17"
      height="17"
      viewBox="0 0 17 17"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M12.75 7.08333H4.25C3.46759 7.08333 2.83333 7.71759 2.83333 8.5V12.75C2.83333 13.5324 3.46759 14.1667 4.25 14.1667H12.75C13.5324 14.1667 14.1667 13.5324 14.1667 12.75V8.5C14.1667 7.71759 13.5324 7.08333 12.75 7.08333Z"
        stroke="#939393"
        strokeWidth="1.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M5.66667 7.08333V4.95833C5.66667 4.20743 5.96503 3.48716 6.49576 2.95643C7.02649 2.4257 7.74676 2.12733 8.49767 2.12733C9.24857 2.12733 9.96884 2.4257 10.4996 2.95643C11.0303 3.48716 11.3287 4.20743 11.3287 4.95833V7.08333"
        stroke="#939393"
        strokeWidth="1.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function EyeOffIcon(): JSX.Element {
  return (
    <svg
      width="17"
      height="17"
      viewBox="0 0 17 17"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M10.0483 10.0483C9.84604 10.2658 9.60169 10.4403 9.33001 10.5612C9.05833 10.6821 8.76479 10.7469 8.46747 10.7517C8.17014 10.7565 7.87469 10.7013 7.59929 10.5893C7.32389 10.4774 7.07413 10.3109 6.86494 10.1001C6.65575 9.88915 6.49125 9.63803 6.38145 9.36168C6.27165 9.08533 6.21875 8.78936 6.22583 8.49197C6.2329 8.19459 6.29996 7.90143 6.42293 7.63055C6.54591 7.35967 6.72224 7.11652 6.94133 6.91583"
        stroke="#939393"
        strokeWidth="1.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M7.48584 3.62917C7.81769 3.55374 8.15735 3.5157 8.49809 3.51583C13.4579 3.51583 15.5815 8.47571 15.5815 8.47571C15.2756 9.14832 14.8909 9.78016 14.4362 10.3581"
        stroke="#939393"
        strokeWidth="1.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M4.79283 4.79333C3.39816 5.75044 2.28963 7.04997 1.58081 8.57C1.58081 8.57 3.70435 13.5299 8.66423 13.5299C9.92251 13.5343 11.1567 13.1879 12.2288 12.5293"
        stroke="#939393"
        strokeWidth="1.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M1.58081 1.58083L15.5815 15.5815"
        stroke="#939393"
        strokeWidth="1.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
