"use client";
import { GoogleColorIcon } from "@repo/ui/components";
import type { JSX, FormEvent } from "react";
import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { signIn } from "next-auth/react";
import { checkMfaRequired } from "../../lib/mfaActions";
import "./page.scss";

// Icons
function MailIcon(): JSX.Element {
  return (
    <svg
      width="17"
      height="14"
      viewBox="0 0 20 17"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        fill="currentColor"
        d="M18 .5H2C.9.5.01 1.4.01 2.5L0 14.5c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2v-12c0-1.1-.9-2-2-2Zm0 4-8 5-8-5v-2l8 5 8-5v2Z"
      />
    </svg>
  );
}

function LockIcon(): JSX.Element {
  return (
    <svg
      width="14"
      height="17"
      viewBox="0 0 18 22"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        fill="currentColor"
        d="M15 7.5h2a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H1a1 1 0 0 1-1-1v-12a1 1 0 0 1 1-1h2v-1a6 6 0 1 1 12 0v1Zm-2 0v-1a4 4 0 1 0-8 0v1h8Zm-5 6v2h2v-2H8Zm-4 0v2h2v-2H4Zm8 0v2h2v-2h-2Z"
      />
    </svg>
  );
}

function EyeOffIcon(): JSX.Element {
  return (
    <svg
      width="17"
      height="17"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24" />
      <path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 11 8 11 8a13.16 13.16 0 0 1-1.67 2.68" />
      <path d="M6.61 6.61A13.526 13.526 0 0 0 1 12s4 8 11 8a9.74 9.74 0 0 0 5.39-1.61" />
      <line x1="2" y1="2" x2="22" y2="22" />
    </svg>
  );
}

function EyeIcon(): JSX.Element {
  return (
    <svg
      width="17"
      height="17"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function SsoIcon(): JSX.Element {
  return (
    <svg
      width="12"
      height="16"
      viewBox="0 0 18 22"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        fill="currentColor"
        d="M15 7.5h2a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H1a1 1 0 0 1-1-1v-12a1 1 0 0 1 1-1h2v-1a6 6 0 1 1 12 0v1Zm-2 0v-1a4 4 0 1 0-8 0v1h8Zm-5 6v2h2v-2H8Zm-4 0v2h2v-2H4Zm8 0v2h2v-2h-2Z"
      />
    </svg>
  );
}

function ArrowRightIcon(): JSX.Element {
  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <line x1="5" y1="12" x2="19" y2="12" />
      <polyline points="12 5 19 12 12 19" />
    </svg>
  );
}

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
                  <button
                    type="button"
                    className="toggle-password"
                    onClick={() => {
                      setShowPassword(!showPassword);
                    }}
                    aria-label={
                      showPassword ? "Hide password" : "Show password"
                    }
                  >
                    {showPassword ? <EyeIcon /> : <EyeOffIcon />}
                  </button>
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

              <button type="submit" className="submit-btn" disabled={isLoading}>
                {isLoading ? "Signing in..." : "Sign In"}
              </button>
            </form>

            <div className="social-section">
              <div className="login-divider">
                <div className="line" />
                <span>or continue with</span>
                <div className="line" />
              </div>

              <div className="social-buttons">
                <button
                  type="button"
                  className="social-btn"
                  onClick={handleGoogleClick}
                  disabled={isLoading}
                >
                  <GoogleColorIcon />
                  Sign in with Google
                </button>
                <button
                  type="button"
                  className="social-btn"
                  disabled={isLoading}
                >
                  <SsoIcon />
                  Sign in with SSO
                </button>
              </div>
            </div>
          </div>

          <p className="copyright">
            Copyright 2023 -{" "}
            <a
              href="https://www.iopex.com/"
              target="_blank"
              rel="noopener noreferrer"
            >
              iOPEX Technologies
            </a>
          </p>
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

      <div className="right-panel">
        <video className="arrows-video" autoPlay loop muted playsInline>
          <source src="/arrows.mp4" type="video/mp4" />
        </video>
      </div>
    </div>
  );
}

export default Login;
