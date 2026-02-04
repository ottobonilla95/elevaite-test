"use client";

import type { JSX } from "react";
import { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Image from "next/image";
import { resetPassword } from "../../lib/actions";
import { LockIcon, EyeOffIcon } from "../../components/icons";
import { Copyright } from "../../components/Copyright";
import { OrangePanel } from "../../components/OrangePanel";
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

            <Copyright />
          </div>

          <OrangePanel />
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

            <Copyright />
          </div>

          <OrangePanel />
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
