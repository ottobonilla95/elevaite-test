import { redirect } from "next/navigation";
import type { JSX } from "react";
import { AuthFluff, ElevaiteIcons } from "@repo/ui/components";
import { auth } from "../../auth";
import { authenticate } from "../lib/actions.ts";
import { CustomLoginForm } from "../components/CustomLoginForm";
import "./page.scss";
import "./hide-register.css";

export default async function LoginPage(): Promise<JSX.Element> {
  const session = await auth();

  // If the user is already logged in, redirect to the home page
  if (session?.user) {
    redirect("/");
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
            <span className="main">Sign in to Toshiba</span>
            <br />
            <span className="ui-text-sm">Enter your login details below.</span>
          </div>
          <CustomLoginForm authenticate={authenticate} />
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
