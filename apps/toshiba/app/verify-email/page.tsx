"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { AuthFluff, ElevaiteIcons } from "@repo/ui/components";
import Link from "next/link";
import "../login/page.scss";

interface VerificationResult {
  success: boolean;
}

export default function VerifyEmailPage() {
  const searchParams = useSearchParams();
  const [verificationResult, setVerificationResult] =
    useState<VerificationResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = searchParams.get("token");

    if (!token) {
      setVerificationResult({
        success: false,
        message: "Invalid verification link. No token provided.",
      });
      setIsLoading(false);
      return;
    }

    verifyEmail(token);
  }, [searchParams]);

  const verifyEmail = async (token: string) => {
    try {
      const backendUrl = process.env.NEXT_PUBLIC_AUTH_API_URL;
      const tenantId = process.env.NEXT_PUBLIC_AUTH_TENANT_ID ?? "default";

      if (!backendUrl) {
        setVerificationResult({
          success: false,
        });
        setIsLoading(false);
        return;
      }

      const apiUrl = backendUrl.replace("localhost", "127.0.0.1");

      const response = await fetch(`${apiUrl}/api/auth/verify-email`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Tenant-ID": tenantId,
        },
        body: JSON.stringify({
          token: token,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setVerificationResult({
          success: true,
        });
      } else {
        const errorData = await response.json();
        setVerificationResult({
          success: false,
        });
      }
    } catch (error) {
      console.error("Email verification error:", error);
      setVerificationResult({
        success: false,
      });
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
          <div className="ui-w-full ui-max-w-xl ui-text-center">
            {isLoading ? (
              <div className="ui-flex ui-flex-col ui-items-center ui-gap-4">
                <div className="ui-animate-spin ui-rounded-full ui-h-8 ui-w-8 ui-border-b-2 ui-border-orange-500"></div>
                <p className="ui-text-gray-400">Verifying your email...</p>
              </div>
            ) : verificationResult ? (
              <div className="ui-flex ui-flex-col ui-items-center ui-gap-4">
                {verificationResult.success ? (
                  <>
                    <div className="ui-text-green-500 ui-text-6xl">✓</div>
                    <h3 className="ui-text-lg ui-font-semibold ui-text-green-400 ui-mb-2">
                      Email Verified Successfully!
                    </h3>
                    <p className="ui-text-sm ui-text-gray-500 ui-mb-4">
                      Your account is now active. You can log in to access your
                      account.
                    </p>
                    <Link
                      href="/login"
                      className="ui-py-2 ui-px-5 ui-bg-orange-500 ui-rounded-lg ui-w-32 ui-text-xs ui-font-medium ui-text-center ui-block"
                    >
                      Go to Login
                    </Link>
                  </>
                ) : (
                  <>
                    <div className="ui-text-red-500 ui-text-6xl">✗</div>
                    <h3 className="ui-text-lg ui-font-semibold ui-text-red-400 ui-mb-2">
                      Verification Failed
                    </h3>
                    <div className="ui-flex ui-flex-col ui-gap-3 ui-items-center">
                      <Link
                        href="/resend-verification"
                        className="ui-py-2 ui-px-5 ui-bg-orange-500 ui-rounded-lg ui-text-xs ui-font-medium"
                      >
                        Resend Verification Email
                      </Link>
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
                  </>
                )}
              </div>
            ) : null}
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
