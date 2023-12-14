"use client";
import type { JSX } from "react";
import { LogInForm, SignUpForm } from "../components/authentication";
import { AuthFluff } from "../components/AuthFluff";

interface LoginPageProps {
  signUp: boolean;
  mode: 1 | 2;
  authenticate: (
    prevstate: string,
    formData: Record<"email" | "password", string>
  ) => Promise<"Invalid credentials." | "Something went wrong." | undefined>;
}

export function LoginPage({ signUp, mode, authenticate }: LoginPageProps): JSX.Element {
  return (
    <div className="ui-w-screen ui-h-screen">
      <div className="ui-flex ui-items-center ui-justify-center ui-bg-[#161616] ui-w-1/2 ui-h-full ui-float-left">
        <AuthFluff mode={mode} />
      </div>
      <div className="ui-flex ui-items-center ui-justify-center ui-bg-[#282828] ui-h-full ui-w-1/2 ui-float-right">
        {signUp ? <SignUpForm /> : <LogInForm authenticate={authenticate} />}
      </div>
    </div>
  );
}
