"use client";
import { AuthFluff, ElevaiteIcons } from "@repo/ui/components";
import Link from "next/link";
import type { JSX } from "react";
import { useState } from "react";
import "../login/page.scss";

function ForgotPassword(): JSX.Element {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  async function handleSubmit(e: React.FormEvent): Promise<void> {
    e.preventDefault();

    if (!email.includes("@")) {
      setMessage({
        type: "error",
        text: "Please enter a valid email address.",
      });
      return;
    }

    setIsSubmitting(true);
    setMessage(null);

    try {
      const response = await fetch("/api/auth/forgot-password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email }),
      });

      if (response.ok) {
        setMessage({
          type: "success",
          text: "If this email exists in our system, we've sent a temporary password. Check your inbox and spam folder, then return to log in.",
        });
        setEmail("");
      } else {
        const data = (await response.json()) as { message?: string };
        setMessage({
          type: "error",
          text: data.message ?? "Something went wrong. Please try again later.",
        });
      }
    } catch (error: unknown) {
      setMessage({
        type: "error",
        text:
          error instanceof Error
            ? error.message
            : "An unexpected error occurred. Please try again later.",
      });
    } finally {
      setIsSubmitting(false);
    }
  }
  return (
    <div className="login-page-container">
      <div className="auth-fluff-container">
        <div />
        <div className="center-block">
          <div className="center-header">
            <ElevaiteIcons.SVGNavbarLogo />
            <span>Elevate your business by AI.</span>
          </div>
          <div className="auth-fluff-content">
            <AuthFluff mode={1} />
          </div>
        </div>
        <div className="version">
          <span>Version 2.0</span>
        </div>
      </div>

      <div className="login-form-container">
        <div />

        <div className="center-block">
          <div className="title">
            <span className="main">Forgot Password</span>
            <span
              className="ui-w-full ui-max-w-xl ui-text-center ui-text-sm"
              style={{ color: "var(--ev-colors-secondaryText)" }}
            >
              Enter your email address, and we&apos;ll send a temporary password
              if an account is associated with it.{" "}
              <em>
                We don&apos;t store your password and will never send it via
                email.
              </em>
            </span>
          </div>

          <div className="forgot-password-form ui-w-full ui-max-w-xl">
            {message ? (
              <div
                className="ui-w-full ui-mb-6 ui-rounded-lg mb-5 ui-text-sm"
                style={{
                  backgroundColor:
                    message.type === "success"
                      ? "var(--ev-colors-success-background, #dcfce7)"
                      : "var(--ev-colors-error-background, #fef2f2)",
                  color:
                    message.type === "success"
                      ? "var(--ev-colors-success-text, #166534)"
                      : "var(--ev-colors-error-text, #991b1b)",
                  paddingLeft: "5%",
                  paddingTop: "1%",
                  paddingBottom: "1%",
                }}
              >
                {message.text}
              </div>
            ) : null}

            <form
              className="ui-flex ui-flex-col ui-items-start ui-gap-3 ui-font-inter ui-w-full"
              onSubmit={handleSubmit}
            >
              <div className="ui-relative ui-w-full">
                <input
                  type="email"
                  id="email"
                  placeholder="Email Address"
                  className="ui-w-full ui-py-[13px] ui-px-5 ui-rounded-lg ui-border-none ui-outline-none"
                  style={{
                    backgroundColor:
                      "var(--ev-colors-inputBackground, #161616)",
                  }}
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                  }}
                  required
                />
              </div>

              <div className="ui-h-16" />

              <div className="ui-w-full ui-flex ui-justify-end">
                <button
                  className="ui-py-2 ui-px-5 ui-rounded-lg ui-w-32 ui-text-xs ui-font-medium disabled:ui-opacity-50"
                  style={{ backgroundColor: "var(--ev-colors-highlight)" }}
                  type="submit"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? "Sending..." : "Reset Password"}
                </button>
              </div>

              <div className="ui-flex ui-justify-start ui-w-full ui-mt-4">
                <span
                  className="ui-text-sm"
                  style={{ color: "var(--ev-colors-secondaryText)" }}
                >
                  Received your temporary password?{" "}
                  <Link
                    href="/login"
                    className="hover:ui-underline"
                    style={{ color: "var(--ev-colors-highlight)" }}
                  >
                    Sign in
                  </Link>{" "}
                  to continue.
                </span>
              </div>
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

export default ForgotPassword;
