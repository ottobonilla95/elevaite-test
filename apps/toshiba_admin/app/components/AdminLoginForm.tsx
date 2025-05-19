"use client";
import { type SetStateAction, useState } from "react";
import { Button, ElevaiteIcons, Input } from "@repo/ui/components";
import { useFormState, useFormStatus } from "react-dom";

interface AdminLoginFormProps {
  authenticate: (
    prevstate: string,
    formData: Record<"email" | "password", string>
  ) => Promise<
    | "Invalid credentials."
    | "Email not verified."
    | "Admin access required."
    | "Something went wrong."
    | undefined
  >;
  authenticateGoogle: () => Promise<
    | "Invalid credentials."
    | "Email not verified."
    | "Admin access required."
    | "Something went wrong."
    | undefined
  >;
}

function SubmitButton() {
  const { pending } = useFormStatus();

  return (
    <Button
      type="submit"
      className="ui-w-full ui-mt-4"
      disabled={pending}
      loading={pending}
    >
      Sign In
    </Button>
  );
}

export function AdminLoginForm({
  authenticate,
  authenticateGoogle,
}: AdminLoginFormProps) {
  const [errorMessage, dispatch] = useFormState(authenticate, undefined);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);

  const handleGoogleLogin = async () => {
    const result = await authenticateGoogle();
    if (result) {
      // Display error message
      console.error("Google login error:", result);
    }
  };

  return (
    <div className="ui-w-full ui-max-w-md">
      <form action={dispatch} className="ui-space-y-4">
        <div className="ui-space-y-2">
          <Input
            type="email"
            name="email"
            placeholder="Email"
            required
            value={email}
            onChange={(e: { target: { value: SetStateAction<string> } }) => {
              setEmail(e.target.value);
            }}
          />
        </div>
        <div className="ui-space-y-2">
          <Input
            type="password"
            name="password"
            placeholder="Password"
            required
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
            }}
          />
        </div>
        <div className="ui-flex ui-items-center ui-justify-between">
          <div className="ui-flex ui-items-center ui-space-x-2">
            <input
              type="checkbox"
              id="remember-me"
              name="rememberMe"
              checked={rememberMe}
              onChange={(e) => {
                setRememberMe(e.target.checked);
              }}
              className="ui-h-4 ui-w-4 ui-rounded ui-border-gray-300 ui-text-blue-600 focus:ui-ring-blue-500"
            />
            <label
              htmlFor="remember-me"
              className="ui-text-sm ui-text-gray-900"
            >
              Remember me
            </label>
          </div>
          <div className="ui-text-sm">
            <a
              href="/forgot-password"
              className="ui-font-medium ui-text-blue-600 hover:ui-text-blue-500"
            >
              Forgot password?
            </a>
          </div>
        </div>
        {errorMessage ? (
          <div className="ui-rounded-md ui-bg-red-50 ui-p-4">
            <div className="ui-flex">
              <div className="ui-flex-shrink-0">
                <ElevaiteIcons.SVGWarning className="ui-h-5 ui-w-5 ui-text-red-400" />
              </div>
              <div className="ui-ml-3">
                <h3 className="ui-text-sm ui-font-medium ui-text-red-800">
                  {errorMessage}
                </h3>
              </div>
            </div>
          </div>
        ) : null}
        <SubmitButton />
      </form>
      <div className="ui-mt-6">
        <div className="ui-relative">
          <div className="ui-absolute ui-inset-0 ui-flex ui-items-center">
            <div className="ui-w-full ui-border-t ui-border-gray-300" />
          </div>
          <div className="ui-relative ui-flex ui-justify-center ui-text-sm">
            <span className="ui-bg-white ui-px-2 ui-text-gray-500">
              Or continue with
            </span>
          </div>
        </div>
        <div className="ui-mt-6">
          <button
            type="button"
            onClick={handleGoogleLogin}
            className="ui-flex ui-w-full ui-items-center ui-justify-center ui-rounded-md ui-border ui-border-gray-300 ui-bg-white ui-px-4 ui-py-2 ui-text-sm ui-font-medium ui-text-gray-700 ui-shadow-sm hover:ui-bg-gray-50"
          >
            <ElevaiteIcons.SVGGoogle className="ui-h-5 ui-w-5 ui-mr-2" />
            Google
          </button>
        </div>
      </div>
    </div>
  );
}
