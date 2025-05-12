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

    if (!email || !email.includes("@")) {
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
          text: "If your email exists in our system, you will receive password reset instructions shortly.",
        });
        setEmail("");
      } else {
        const data = await response.json();
        setMessage({
          type: "error",
          text: data.message || "Something went wrong. Please try again later.",
        });
      }
    } catch (error) {
      setMessage({
        type: "error",
        text: "An unexpected error occurred. Please try again later.",
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
            <span className="ui-w-full ui-max-w-xl ui-text-center">
              Enter the email address you used when you joined and we&apos;ll
              send you instructions to reset your password.
              <br />
              <br />
              For security reasons, we do NOT store your password. So rest
              assured that we will never send your password via email.
            </span>
          </div>

          <div className="forgot-password-form ui-w-full ui-max-w-xl">
            {message && (
              <div
                className={`ui-w-full ui-p-4 ui-mb-4 ui-rounded-lg ${
                  message.type === "success"
                    ? "ui-bg-green-100 ui-text-green-800"
                    : "ui-bg-red-100 ui-text-red-800"
                }`}
              >
                {message.text}
              </div>
            )}

            <form
              className="ui-flex ui-flex-col ui-items-start ui-gap-3 ui-font-inter ui-w-full"
              onSubmit={handleSubmit}
            >
              <div className="ui-relative ui-w-full">
                <input
                  type="email"
                  id="email"
                  placeholder="Email Address"
                  className="ui-w-full ui-py-[13px] ui-px-5 ui-bg-[#161616] ui-rounded-lg ui-border-none ui-outline-none"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              <div className="ui-h-16" />

              <div className="ui-w-full ui-flex ui-justify-end">
                <button
                  className="ui-py-2 ui-px-5 ui-bg-orange-500 ui-rounded-lg ui-w-32 ui-text-xs ui-font-medium disabled:ui-opacity-50"
                  type="submit"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? "Sending..." : "Reset Password"}
                </button>
              </div>

              <div className="ui-flex ui-justify-start ui-w-full ui-mt-4">
                <span className="ui-text-sm ui-text-gray-400">
                  Remember your password?{" "}
                  <Link
                    href="/login"
                    className="ui-text-[#E75F33] hover:ui-underline"
                  >
                    Sign in
                  </Link>
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
            href="https://www.iopex.com/"
            rel="noopener noreferrer"
          >
            iOPEX Technologies
          </a>
        </div>
      </div>
    </div>
  );
}

export default ForgotPassword;
