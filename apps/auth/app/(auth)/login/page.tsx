import { AuthFluff, LogInForm, ElevaiteIcons } from "@repo/ui/components";
import type { JSX } from "react";
import { authenticate, authenticateGoogle } from "../../lib/actions";
import "./page.scss";

function Login(): JSX.Element {
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
            <span className="main">Sign in to ElevAIte</span>
            <span>Enter your login details below.</span>
          </div>
          <LogInForm
            authenticate={authenticate}
            authenticateGoogle={authenticateGoogle}
          />
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

export default Login;
