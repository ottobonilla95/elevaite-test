"use client";

import { AuthFluff, ElevaiteIcons } from "@repo/ui/components";
import { useState, useEffect } from "react";
import type { JSX } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { redirect } from "next/navigation";
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

  /* eslint-disable no-console -- Debug logging for troubleshooting one-time password flow */
  useEffect(() => {
    // Debug logging
    console.log("Reset Password Page - Session status:", status);
    console.log("Reset Password Page - Session:", session);

    // If session is still loading, do nothing
    if (status === "loading") {
      console.log("Reset Password Page - Session is loading");
      return;
    }

    // If user is not authenticated, redirect to login
    if (status === "unauthenticated") {
      console.log(
        "Reset Password Page - User is not authenticated, redirecting to login"
      );
      // Use window.location.href instead of router.push to avoid Next.js client-side routing
      // This will cause a full page reload and avoid any potential refresh loops
      window.location.href = "/login";
      return;
    }

    // At this point, we know status is 'authenticated' and session exists
    if (session && session.user) {
      console.log("Reset Password Page - User:", session.user);

      // Set email from session
      if (session.user.email) {
        console.log("Reset Password Page - Setting email:", session.user.email);
        setEmail(session.user.email);
      }

      console.log("Reset Password Page - User needs to reset password");

      // Set email from session
      if (session.user.email) {
        console.log("Reset Password Page - Setting email:", session.user.email);
        setEmail(session.user.email);
      }
    }
  }, [status, session, router]);
  /* eslint-enable no-console -- End of debug logging section */

  const handleResetPassword = async (): Promise<void> => {
    /* eslint-disable-next-line no-console -- Debug logging */
    console.log("Reset Password Page - Attempting to reset password");

    // Validate passwords
    if (newPassword !== confirmPassword) {
      setError("Passwords don't match");
      return;
    }

    // Password validation
    if (newPassword.length < 9) {
      setError("Password must be at least 9 characters");
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
      /* eslint-disable-next-line no-console -- Debug logging */
      console.log(
        "Reset Password Page - Calling resetPassword function with password length:",
        newPassword.length
      );

      // Call the server action to reset the password
      const result = await resetPassword(newPassword);

      /* eslint-disable-next-line no-console -- Debug logging */
      console.log("Reset Password Page - Password reset result:", result);

      if (result.success) {
        /* eslint-disable-next-line no-console -- Debug logging */
        console.log("Reset Password Page - Password reset successful");
        setIsSuccess(true);
      } else {
        /* eslint-disable-next-line no-console -- Debug logging */
        console.error(
          "Reset Password Page - Password reset failed:",
          result.message
        );
        // Ensure we have a string error message
        setError("Failed to reset password. Please try again.");
      }
    } catch (err) {
      /* eslint-disable-next-line no-console -- Debug logging */
      console.error(
        "Reset Password Page - Password reset failed with exception:",
        err
      );
      setError("Failed to reset password. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleContinue = async (): Promise<void> => {
    // Sign out and redirect to login
    try {
      /* eslint-disable-next-line no-console -- Debug logging */
      console.log("Reset Password Page - Signing out and redirecting to login");

      const { signOut } = await import("next-auth/react");
      await signOut({ redirect: true, callbackUrl: "/login" });
    } catch (err) {
      /* eslint-disable-next-line no-console -- Needed for error reporting */
      console.error("Error signing out:", err);

      // Fallback to manual redirect
      window.location.href = "/login";
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

          {isSuccess ? (
            <div className="success-message">
              <h2>Password Reset Successful</h2>
              <p>
                Your password has been successfully reset. You will be
                redirected to the login page where you can sign in with your new
                password.
              </p>
              <button
                className="continue-button"
                onClick={handleContinue}
                disabled={isSubmitting}
                type="button"
              >
                Continue to Login
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
