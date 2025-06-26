"use client";

import { useState } from "react";
import { AuthFluff, ElevaiteIcons } from "@repo/ui/components";
import Link from "next/link";
import "../login/page.scss";

export default function ResendVerificationPage() {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [isSuccess, setIsSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email) {
      setMessage("Please enter your email address.");
      setIsSuccess(false);
      return;
    }

    setIsLoading(true);
    setMessage("");

    try {
      const backendUrl = process.env.NEXT_PUBLIC_AUTH_API_URL;
      const tenantId = process.env.NEXT_PUBLIC_AUTH_TENANT_ID ?? "default";

      if (!backendUrl) {
        setMessage(
          "The app is misconfigured, please contact a site administrator."
        );
        setIsSuccess(false);
        setIsLoading(false);
        return;
      }

      const apiUrl = backendUrl.replace("localhost", "127.0.0.1");

      const response = await fetch(`${apiUrl}/api/auth/resend-verification`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Tenant-ID": tenantId,
        },
        body: JSON.stringify({
          email: email,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setMessage(data.message || "Verification email sent successfully!");
        setIsSuccess(true);
      } else {
        setMessage(
          data.detail || data.message || "Failed to send verification email."
        );
        setIsSuccess(false);
      }
    } catch (error) {
      console.error("Resend verification error:", error);
      setMessage("An unexpected error occurred. Please try again later.");
      setIsSuccess(false);
    } finally {
      setIsLoading(false);
    }
  };

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
            <span className="main">Resend Verification Email</span>
            <span className="ui-w-full ui-max-w-xl ui-text-center">
              Enter your email address to receive a new verification link
            </span>
          </div>

          <div className="ui-w-full ui-max-w-xl">
            {message && (
              <div
                className={`ui-w-full ui-p-4 ui-mb-4 ui-rounded-lg ${
                  isSuccess
                    ? "ui-bg-green-100 ui-text-green-800"
                    : "ui-bg-red-100 ui-text-red-800"
                }`}
              >
                {message}
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
                  disabled={isLoading}
                />
              </div>

              <div className="ui-h-16" />

              <div className="ui-w-full ui-flex ui-justify-end">
                <button
                  className="ui-py-2 ui-px-5 ui-bg-orange-500 ui-rounded-lg ui-w-32 ui-text-xs ui-font-medium disabled:ui-opacity-50"
                  type="submit"
                  disabled={isLoading}
                >
                  {isLoading ? "Sending..." : "Send Email"}
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
