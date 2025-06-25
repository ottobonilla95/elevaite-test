"use client";

import { AuthFluff, ElevaiteIcons } from "@repo/ui/components";
import { useState, useEffect } from "react";
import type { JSX } from "react";
import { useSession } from "next-auth/react";
import { resetPassword, logout } from "../lib/actions";
import "./page.scss";

export default function ResetPassword(): JSX.Element {
  const [email, setEmail] = useState<string | null>(null);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
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
      }
    } catch (err) {
      // Fail silently
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
                <input
                  id="newPassword"
                  type="password"
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
