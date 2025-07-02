"use client";

import { AuthFluff, ElevaiteIcons } from "@repo/ui/components";
import { useState, useEffect } from "react";
import type { JSX } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import "./page.scss";

export default function ChangePassword(): JSX.Element {
  const [email, setEmail] = useState<string | null>(null);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRedirecting, setIsRedirecting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (isRedirecting) {
      return;
    }

    if (status === "loading") {
      return;
    }

    if (status === "unauthenticated") {
      setIsRedirecting(true);
      window.location.href = "/login";
      return;
    }

    if (session && session.user) {
      if (session.user.email) {
        setEmail(session.user.email);
      }
    }
  }, [status, session, isRedirecting]);

  const handleChangePassword = async (): Promise<void> => {
    if (!currentPassword) {
      setError("Current password is required");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("New passwords don't match");
      return;
    }

    if (newPassword.length < 9) {
      setError("New password must be at least 9 characters");
      return;
    }

    const hasUppercase = /[A-Z]/.test(newPassword);
    const hasLowercase = /[a-z]/.test(newPassword);
    const hasNumber = /[0-9]/.test(newPassword);
    const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(newPassword);

    if (!hasUppercase || !hasLowercase || !hasNumber || !hasSpecial) {
      setError(
        "New password must include uppercase, lowercase, numbers, and special characters"
      );
      return;
    }

    if (currentPassword === newPassword) {
      setError("New password must be different from current password");
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      const response = await fetch("/api/auth/change-password-user", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setIsSuccess(true);
      } else {
        setError(data.detail || "Failed to change password. Please try again.");
      }
    } catch (err) {
      console.error("Change password error:", err);
      setError("An unexpected error occurred. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleContinue = (): void => {
    router.push("/");
  };

  const handleBackToHomepage = (): void => {
    router.push("/");
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
            <span className="main">Change Your Password</span>
            <span>Update your password to keep your account secure.</span>
          </div>

          {isSuccess ? (
            <div className="success-message">
              <h2>Password Changed Successfully</h2>
              <p>
                Your password has been successfully updated. You can continue
                using the system with your new password.
              </p>
              <button
                className="continue-button"
                onClick={handleContinue}
                type="button"
              >
                Continue to Application
              </button>
            </div>
          ) : (
            <div className="reset-password-form">
              <div className="reset-password-explanation">
                <p>
                  To change your password, please provide your current password
                  and choose a new secure password.
                  {email ? (
                    <span>
                      {" "}
                      This will update the password for your account:{" "}
                      <strong>{email}</strong>.
                    </span>
                  ) : null}
                </p>
                <p>
                  Your new password must be at least 9 characters long and
                  include uppercase letters, lowercase letters, numbers, and
                  special characters.
                </p>
              </div>

              <form
                className="form-fields"
                onSubmit={(e) => {
                  e.preventDefault();
                  void handleChangePassword();
                }}
              >
                <div className="form-field">
                  <label htmlFor="currentPassword">Current Password</label>
                  <input
                    id="currentPassword"
                    type="password"
                    value={currentPassword}
                    onChange={(e) => {
                      setCurrentPassword(e.target.value);
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        document.getElementById("newPassword")?.focus();
                        e.preventDefault();
                      }
                    }}
                    required
                  />
                </div>

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
                        document.getElementById("confirmPassword")?.focus();
                        e.preventDefault();
                      }
                    }}
                    required
                  />
                </div>

                <div className="form-field">
                  <label htmlFor="confirmPassword">Confirm New Password</label>
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

                <div className="button-group">
                  <button
                    className="back-button"
                    type="button"
                    onClick={handleBackToHomepage}
                  >
                    Back to Homepage
                  </button>
                  <button
                    className="reset-button"
                    disabled={isSubmitting}
                    type="submit"
                  >
                    {isSubmitting ? "Changing..." : "Change Password"}
                  </button>
                </div>
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
