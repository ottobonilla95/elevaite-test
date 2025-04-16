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
            <span>Enter your email to reset your password.</span>
          </div>
          
          <div className="forgot-password-form">
            <form className="ui-flex ui-flex-col ui-items-start ui-gap-3 ui-font-inter ui-w-full">
              <label className="ui-text-sm ui-text-gray-400">Email</label>
              <div className="ui-relative ui-w-full">
                <input
                  type="email"
                  placeholder="Enter your email"
                  className="ui-w-full ui-py-3 ui-pl-12 ui-pr-4 ui-bg-[#282828] ui-rounded-lg ui-border-none ui-outline-none"
                />
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width={20}
                  height={17}
                  fill="none"
                  className="ui-absolute ui-left-4 ui-top-1/2 ui-transform ui--translate-y-1/2"
                >
                  <path
                    fill="#898989"
                    d="M18 .5H2C.9.5.01 1.4.01 2.5L0 14.5c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2v-12c0-1.1-.9-2-2-2Zm0 4-8 5-8-5v-2l8 5 8-5v2Z"
                  />
                </svg>
              </div>
              
              <div className="ui-flex ui-flex-row ui-gap-4 ui-w-full ui-mt-4">
                <button
                  className="ui-bg-[#E75F33] ui-py-3 ui-px-10 ui-rounded-lg ui-flex-1"
                  type="submit"
                >
                  Reset Password
                </button>
              </div>
              
              <div className="ui-flex ui-justify-center ui-w-full ui-mt-2">
                <Link
                  href="/login"
                  className="ui-text-sm ui-text-gray-400 hover:ui-text-gray-300"
                >
                  Back to Login
                </Link>
              </div>
            </form>
          </div>
        </div>

        <div className="copyright">
          <span>Copyright 2023-2024</span>
          <span>•</span>
          <a target="_blank" href="https://www.iopex.com/" rel="noopener noreferrer">
            iOPEX Technologies
          </a>
        </div>
      </div>
    </div>
  );
}

export default ForgotPassword;
