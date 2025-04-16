import { AuthFluff, ElevaiteIcons } from "@repo/ui/components";
import Link from "next/link";
import type { JSX } from "react";
import "../login/page.scss";

function ForgotPassword(): JSX.Element {
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
            <span className="ui-w-3/5 ui-text-center">
              Enter the email address you used when you joined and we&apos;ll
              send you instructions to reset your password.
              <br />
              <br />
              For security reasons, we do NOT store your password. So rest
              assured that we will never send your password via email.
            </span>
          </div>

          <div className="forgot-password-form ui-w-3/5">
            <form className="ui-flex ui-flex-col ui-items-start ui-gap-3 ui-font-inter ui-w-full">
              <label
                className="ui-text-lg ui-font-semibold ui-font-source_sans"
                htmlFor="email"
              >
                Email
              </label>
              <div className="ui-relative ui-w-full">
                <input
                  type="email"
                  id="email"
                  placeholder="Enter your email"
                  className="ui-w-full ui-py-[13px] ui-px-5 ui-bg-[#161616] ui-rounded-lg ui-border-none ui-outline-none"
                />
              </div>

              <div className="ui-w-full ui-mt-4 ui-flex ui-justify-start">
                <button
                  className="ui-py-3 ui-px-10 ui-bg-orange-500 ui-rounded-lg ui-w-1/3 ui-font-medium"
                  type="submit"
                >
                  Send Reset Instructions
                </button>
              </div>

              <div className="ui-flex ui-justify-center ui-w-full ui-mt-4">
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
          <span>Copyright 2023-2024</span>
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
