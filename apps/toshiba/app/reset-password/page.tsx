"use client";

import { AuthFluff, ElevaiteIcons } from "@repo/ui/components";
import { useState, useEffect } from "react";
import type { JSX } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { resetPassword } from "../lib/actions";
import "./page.scss";

export default function ResetPassword(): JSX.Element {
  const [isSuccess, setIsSuccess] = useState(false);
  const [email, setEmail] = useState<string | null>(null);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();
  const { data: session, status } = useSession();

  useEffect(() => {
    // If session is still loading, do nothing
    if (status === "loading") return;

    // If user is not authenticated, redirect to login
    if (status === "unauthenticated") {
      router.push("/login");
      return;
    }

    // At this point, we know status is 'authenticated' and session exists
    if (session && session.user) {
      // Set email from session
      if (session.user.email) {
        setEmail(session.user.email);
      }

      // Check if user needs to reset password
      const needsReset =
        "needsPasswordReset" in session.user &&
        session.user.needsPasswordReset === true;

      // If they don't need to reset, redirect to home
      if (!needsReset) {
        router.push("/");
      }
    }
  }, [status, session, router]);

  const handleResetPassword = async (): Promise<void> => {
    // Validate passwords
    if (newPassword !== confirmPassword) {
      setError("Passwords don't match");
      return;
    }

    // Password validation
    if (newPassword.length < 12) {
      setError("Password must be at least 12 characters");
      return;
    }

    // Check for uppercase, lowercase, numbers, and special characters
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
      await resetPassword(newPassword);
      setIsSuccess(true);
    } catch (err) {
      setError("Failed to reset password. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleContinue = (): void => {
    // Redirect to the main application
    window.location.href = "/";
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

          {isSuccess ? (
            <div className="success-message">
              <h2>Password Reset Successful</h2>
              <p>
                Your password has been successfully reset. You can now use your
                new password to access the system.
              </p>
              <button
                className="continue-button"
                onClick={handleContinue}
                disabled={isSubmitting}
                type="button"
              >
                Continue to Application
              </button>
            </div>
          ) : (
            <div className="reset-password-form">
              <div className="reset-password-explanation">
                <p>
                  For security reasons, you need to set a new password for your
                  account.
                  {email ? (
                    <span>
                      {" "}
                      This will be used for your account:{" "}
                      <strong>{email}</strong>.
                    </span>
                  ) : null}
                </p>
                <p>
                  Please choose a strong password that you haven&apos;t used
                  before. Your password must be at least 12 characters long and
                  include uppercase letters, lowercase letters, numbers, and
                  special characters.
                </p>
              </div>

              <div className="form-fields">
                <div className="form-field">
                  <label htmlFor="newPassword">New Password</label>
                  <input
                    id="newPassword"
                    type="password"
                    value={newPassword}
                    onChange={(e) => {
                      setNewPassword(e.target.value);
                    }}
                    required
                  />
                </div>

                <div className="form-field">
                  <label htmlFor="confirmPassword">Confirm Password</label>
                  <input
                    id="confirmPassword"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => {
                      setConfirmPassword(e.target.value);
                    }}
                    required
                  />
                </div>

                {error ? <div className="error-message">{error}</div> : null}

                <button
                  className="reset-button"
                  onClick={handleResetPassword}
                  disabled={isSubmitting}
                  type="button"
                >
                  {isSubmitting ? "Resetting..." : "Reset Password"}
                </button>
              </div>
            </div>
          )}
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
