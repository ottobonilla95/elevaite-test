"use client";
import { GoogleColorIcon, CommonButton } from "@repo/ui/components";
import type { JSX, FormEvent } from "react";
import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { signIn } from "next-auth/react";
import { checkMfaRequired } from "../../lib/mfaActions";
import {
  MailIcon,
  LockIcon,
  EyeIcon,
  EyeOffIcon,
  SsoIcon,
  ArrowRightIcon,
} from "../../components/icons";
import { Copyright } from "../../components/Copyright";
import { VideoPanel } from "../../components/VideoPanel";
import "./page.scss";

function Login(): JSX.Element {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  // Initialize from localStorage on mount
  useEffect(() => {
    setMounted(true);
    if (typeof window !== "undefined") {
      const rememberedEmail = localStorage.getItem("rememberedEmail");
      const remembered = localStorage.getItem("rememberMe") === "true";
      if (rememberedEmail && remembered) {
        setEmail(rememberedEmail);
        setRememberMe(true);
      }
    }
  }, []);

  const handleSubmit = useCallback(
    async (e: FormEvent<HTMLFormElement>): Promise<void> => {
      e.preventDefault();
      setIsLoading(true);
      setError(null);

      try {
        // Handle remember me
        if (rememberMe) {
          localStorage.setItem("rememberedEmail", email);
          localStorage.setItem("rememberMe", "true");
        } else {
          localStorage.removeItem("rememberedEmail");
          localStorage.removeItem("rememberMe");
        }

        // Check if MFA is required
        const mfaResult = await checkMfaRequired(email, password);

        if (mfaResult?.required && mfaResult.methods.length > 0) {
          // Store credentials for MFA flow
          sessionStorage.setItem("mfa_email", email);
          sessionStorage.setItem("mfa_password", password);

          // Build MFA redirect URL
          const params = new URLSearchParams();
          params.set("methods", mfaResult.methods.join(","));
          if (mfaResult.maskedPhone) {
            params.set("phone", mfaResult.maskedPhone);
          }

          router.push(`/mfa?${params.toString()}`);
          return;
        }

        // No MFA required, proceed with normal authentication
        const result = await signIn("credentials", {
          email,
          password,
          redirect: false,
        });

        if (result?.error) {
          if (result.error === "Email not verified.") {
            window.location.href = `/email-verification-error?email=${encodeURIComponent(email)}`;
            return;
          }
          setError("Invalid credentials. Please try again.");
        } else {
          window.location.href =
            process.env.NEXT_PUBLIC_ELEVAITE_HOMEPAGE ?? "/";
        }
      } catch {
        setError("Something went wrong. Please try again.");
      } finally {
        setIsLoading(false);
      }
    },
    [email, password, rememberMe, router],
  );

  const handleGoogleSignIn = useCallback(async (): Promise<void> => {
    try {
      await signIn("google", {
        callbackUrl: process.env.NEXT_PUBLIC_ELEVAITE_HOMEPAGE ?? "/",
      });
    } catch {
      setError("Failed to sign in with Google.");
    }
  }, []);

  const handleFormSubmit = (e: FormEvent<HTMLFormElement>): void => {
    handleSubmit(e).catch(() => {
      setError("Something went wrong. Please try again.");
      setIsLoading(false);
    });
  };

  const handleGoogleClick = (): void => {
    handleGoogleSignIn().catch(() => {
      setError("Failed to sign in with Google.");
    });
  };

  if (!mounted) {
    return <div className="login-page-container" />;
  }

  return (
    <div className="login-page-container">
      <div className="left-column">
        {/* Main panel with form */}
        <div className="main-panel">
          {/* Logo - centered at top (includes tagline in image) */}
          <div className="logo-section">
            <Image
              src="/images/logos/login-logo.png"
              alt="ElevAIte"
              width={170}
              height={54}
              priority
            />
          </div>

          <div className="form-wrapper">
            <div className="login-heading">
              <p>Start your experience with ElevAIte by signing in</p>
            </div>

            <form className="login-form" onSubmit={handleFormSubmit}>
              <div className="input-group">
                <label htmlFor="email">Email Address*</label>
                <div className="input-wrapper">
                  <span className="input-icon">
                    <MailIcon />
                  </span>
                  <div className="divider" />
                  <input
                    id="email"
                    type="email"
                    placeholder="john.smith@gmail.com"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                    }}
                    required
                    disabled={isLoading}
                  />
                </div>
              </div>

              <div className="input-group">
                <label htmlFor="password">Password*</label>
                <div className="input-wrapper">
                  <span className="input-icon">
                    <LockIcon />
                  </span>
                  <div className="divider" />
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                    }}
                    required
                    disabled={isLoading}
                  />
                  <CommonButton
                    overrideClass
                    className="toggle-password"
                    onClick={() => {
                      setShowPassword(!showPassword);
                    }}
                    aria-label={
                      showPassword ? "Hide password" : "Show password"
                    }
                  >
                    {showPassword ? <EyeIcon /> : <EyeOffIcon />}
                  </CommonButton>
                </div>
              </div>

              <div className="auth-options">
                <label className="remember-me">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => {
                      setRememberMe(e.target.checked);
                    }}
                    disabled={isLoading}
                  />
                  <span>Remember me</span>
                </label>
                <Link href="/forgot-password" className="forgot-password">
                  Forgot password?
                </Link>
              </div>

              {error ? <p className="credentials-error">{error}</p> : null}

              <CommonButton
                overrideClass
                className="submit-btn"
                type="submit"
                disabled={isLoading}
              >
                {isLoading ? "Signing in..." : "Sign In"}
              </CommonButton>
            </form>

            <div className="social-section">
              <div className="login-divider">
                <div className="line" />
                <span>or continue with</span>
                <div className="line" />
              </div>

              <div className="social-buttons">
                <CommonButton
                  overrideClass
                  className="social-btn"
                  onClick={handleGoogleClick}
                  disabled={isLoading}
                >
                  <GoogleColorIcon />
                  Sign in with Google
                </CommonButton>
                <CommonButton
                  overrideClass
                  className="social-btn"
                  disabled={isLoading}
                >
                  <SsoIcon />
                  Sign in with SSO
                </CommonButton>
              </div>
            </div>
          </div>

          <Copyright />
        </div>

        {/* Sign up CTA card (separate from main panel) */}
        <div className="signup-cta-card">
          <div className="cta-text">
            <p>Don&apos;t have an account with us yet?</p>
            <p className="orange-text">
              Sign up and explore the power of our products.
            </p>
          </div>
          <Link href="/signup" className="cta-button">
            <ArrowRightIcon />
          </Link>
        </div>
      </div>

      <VideoPanel />
    </div>
  );
}

export default Login;
