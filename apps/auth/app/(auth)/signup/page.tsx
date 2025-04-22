import { redirect } from "next/navigation";
import type { JSX } from "react";

// Preserved for future re-enablement
/*
import { AuthFluff, SignUpForm, ElevaiteIcons } from "@repo/ui/components";
import type { JSX } from "react";
import "../login/page.scss";

function SignUp(): JSX.Element {
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
            <span className="main">Sign up to ElevAIte</span>
            <span>Create your account below.</span>
          </div>
          <SignUpForm />
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
*/

function SignUp(): JSX.Element {
  redirect("/login");
}

export default SignUp;
