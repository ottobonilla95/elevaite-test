"use client";

import { AuthFluff, ElevaiteIcons } from "@repo/ui/components";
import { useState, useEffect } from "react";
import type { JSX } from "react";
import { useSession } from "next-auth/react";
import { resetPassword, logout } from "../lib/actions";
import "./page.scss";

// Eye icons for password visibility toggle
const EyeIcon = ({ size = 16 }: { size?: number }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
  >
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
    <circle cx="12" cy="12" r="3" />
  </svg>
);

const EyeOffIcon = ({ size = 16 }: { size?: number }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
  >
    <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24" />
    <path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 11 8 11 8a13.16 13.16 0 0 1-1.67 2.68" />
    <path d="M6.61 6.61A13.526 13.526 0 0 0 1 12s4 8 11 8a9.74 9.74 0 0 0 5.39-1.61" />
    <line x1="2" y1="2" x2="22" y2="22" />
  </svg>
);

export default function ResetPassword(): JSX.Element {
  const [email, setEmail] = useState<string | null>(null);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRedirecting, setIsRedirecting] = useState(false);
  const { data: session, status } = useSession();

  useEffect(() => {
    if (isRedirecting) {
      console.log(
        "Reset Password Page - Already redirecting, skipping redirect logic"
      );
      return;
    }

    if (status === "loading") {
      return;
    }

    if (status === "unauthenticated") {
      console.log(
        "Reset Password Page - User is not authenticated, redirecting to login"
      );
      setIsRedirecting(true);
      window.location.href = "/login";
      return;
    }

    if (session && session.user) {
      console.log("Reset Password Page - User:", session.user);

      if (session.user.email) {
        console.log("Reset Password Page - Setting email:", session.user.email);
        setEmail(session.user.email);
      }

      console.log("Reset Password Page - User needs to reset password");
    }
  }, [status, session, isRedirecting]);
  const handleResetPassword = async (): Promise<void> => {
    if (newPassword !== confirmPassword) {
      setError("Passwords don't match");
      return;
    }

    if (newPassword.length < 9) {
      setError("Password must be at least 9 characters");
      return;
    }

    const hasUppercase = /[A-Z]/.test(newPassword);
    const hasLowercase = /[a-z]/.test(newPassword);
    const hasNumber = /[0-9]/.test(newPassword);
    const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(newPassword);

    if (!hasUppercase || !hasLowercase || !hasNumber || !hasSpecial) {
      setError(
        "Password must include uppercase, lowercase, numbers, and special characters"
      );
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      const result = await resetPassword(newPassword);

      if (result.success) {
        await logout();
      } else {
        const errorMessage =
          result.message || "Failed to reset password. Please try again.";
        console.log(
          "Setting error message:",
          errorMessage,
          typeof errorMessage
        );
        setError(errorMessage);
      }
    } catch (err) {
      console.log("Reset password caught error:", err);
      const errorMessage =
        err instanceof Error
          ? err.message
          : "An unexpected error occurred. Please try again.";
      console.log(
        "Setting catch error message:",
        errorMessage,
        typeof errorMessage
      );
      setError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="reset-password-page-container">
      <div className="auth-fluff-container">
        <div />
        <div className="center-block">
          <div className="center-header">
            <ElevaiteIcons.SVGNavbarLogo />
            <span>Toshiba - Powered by AI.</span>
          </div>
          <div className="auth-fluff-content">
            <AuthFluff mode={1} />
          </div>
        </div>
        <div className="version">
          <span>Version 2.0</span>
        </div>
      </div>

      <div className="reset-password-form-container">
        <div />

        <div className="center-block">
          <div className="title">
            <span className="main">Reset Your Password</span>
            <span>Please set a new secure password for your account.</span>
          </div>

          <div className="reset-password-form">
            <div className="reset-password-explanation">
              <p>
                For security reasons, you need to set a new password for your
                account.
                {email ? (
                  <span>
                    {" "}
                    This will be used for your account: <strong>{email}</strong>
                    .
                  </span>
                ) : null}
              </p>
              <p>
                Please choose a strong password that you haven&apos;t used
                before. Your password must be at least 9 characters long and
                include uppercase letters, lowercase letters, numbers, and
                special characters.
              </p>
            </div>

            <form
              className="form-fields"
              onSubmit={(e) => {
                e.preventDefault();
                void handleResetPassword();
              }}
            >
              <div className="form-field">
                <label htmlFor="newPassword">New Password</label>
                <div className="password-input-container">
                  <input
                    id="newPassword"
                    type={showNewPassword ? "text" : "password"}
                    value={newPassword}
                    onChange={(e) => {
                      setNewPassword(e.target.value);
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        // Move focus to confirm password field
                        document.getElementById("confirmPassword")?.focus();
                        e.preventDefault();
                      }
                    }}
                    required
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowNewPassword(!showNewPassword)}
                  >
                    {showNewPassword ? <EyeIcon /> : <EyeOffIcon />}
                  </button>
                </div>
              </div>

              <div className="form-field">
                <label htmlFor="confirmPassword">Confirm Password</label>
                <div className="password-input-container">
                  <input
                    id="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => {
                      setConfirmPassword(e.target.value);
                    }}
                    required
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  >
                    {showConfirmPassword ? <EyeIcon /> : <EyeOffIcon />}
                  </button>
                </div>
              </div>

              {error ? <div className="error-message">{error}</div> : null}

              <button
                className="reset-button"
                disabled={isSubmitting}
                type="submit"
              >
                {isSubmitting ? "Resetting..." : "Reset Password"}
              </button>
            </form>
          </div>
        </div>

        <div className="copyright">
          <span>Copyright 2023-2025</span>
          <span>•</span>
          <a
            target="_blank"
            href="https://www.toshiba.com/"
            rel="noopener noreferrer"
          >
            Toshiba Corporation
          </a>
        </div>
      </div>
    </div>
  );
}
