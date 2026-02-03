"use client";
import { GoogleColorIcon } from "@repo/ui/components";
import type { JSX, FormEvent } from "react";
import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import Image from "next/image";
import { signIn } from "next-auth/react";
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

function UserIcon(): JSX.Element {
  return (
    <svg
      width="17"
      height="17"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        fill="currentColor"
        d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"
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

// Password validation requirements
interface PasswordValidation {
  minLength: boolean;
  hasLowercase: boolean;
  hasUppercase: boolean;
  hasDigit: boolean;
  hasSpecial: boolean;
}

function validatePassword(password: string): PasswordValidation {
  return {
    minLength: password.length >= 9,
    hasLowercase: /[a-z]/.test(password),
    hasUppercase: /[A-Z]/.test(password),
    hasDigit: /\d/.test(password),
    hasSpecial: /[!@#$%^&*(),.?":{}|<>]/.test(password),
  };
}

function isPasswordValid(validation: PasswordValidation): boolean {
  return (
    validation.minLength &&
    validation.hasLowercase &&
    validation.hasUppercase &&
    validation.hasDigit &&
    validation.hasSpecial
  );
}

function SignUp(): JSX.Element {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [passwordValidation, setPasswordValidation] =
    useState<PasswordValidation>({
      minLength: false,
      hasLowercase: false,
      hasUppercase: false,
      hasDigit: false,
      hasSpecial: false,
    });

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    setPasswordValidation(validatePassword(password));
  }, [password]);

  const handleSubmit = useCallback(
    async (e: FormEvent<HTMLFormElement>): Promise<void> => {
      e.preventDefault();
      setIsLoading(true);
      setError(null);

      // Validate passwords match
      if (password !== confirmPassword) {
        setError("Passwords do not match.");
        setIsLoading(false);
        return;
      }

      // Validate password strength
      if (!isPasswordValid(passwordValidation)) {
        setError("Password does not meet all requirements.");
        setIsLoading(false);
        return;
      }

      try {
        const AUTH_API_URL = process.env.NEXT_PUBLIC_AUTH_API_URL;
        if (!AUTH_API_URL) {
          setError("Server configuration error.");
          setIsLoading(false);
          return;
        }

        const response = await fetch(`${AUTH_API_URL}/api/auth/register`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email,
            password,
            full_name: `${firstName} ${lastName}`.trim(),
          }),
        });

        if (!response.ok) {
          const data = (await response.json()) as { detail?: string };
          if (data.detail) {
            setError(data.detail);
          } else {
            setError("Registration failed. Please try again.");
          }
          setIsLoading(false);
          return;
        }

        // Registration successful
        setSuccess(true);
      } catch {
        setError("Something went wrong. Please try again.");
      } finally {
        setIsLoading(false);
      }
    },
    [email, password, confirmPassword, firstName, lastName, passwordValidation],
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

  const handleGoogleClick = (): void => {
    handleGoogleSignIn().catch(() => {
      setError("Failed to sign in with Google.");
    });
  };

  const handleFormSubmit = (e: FormEvent<HTMLFormElement>): void => {
    handleSubmit(e).catch(() => {
      setError("Something went wrong. Please try again.");
      setIsLoading(false);
    });
  };

  if (!mounted) {
    return <div className="signup-page-container" />;
  }

  // Success state
  if (success) {
    return (
      <div className="signup-page-container">
        <div className="left-column">
          <div className="main-panel">
            <div className="logo-container">
              <Image
                src="/images/logos/logo.png"
                alt="ElevAIte"
                width={85}
                height={27}
                priority
              />
            </div>

            <div className="form-wrapper">
              <div className="success-content">
                <div className="success-icon">
                  <svg
                    width="64"
                    height="64"
                    viewBox="0 0 24 24"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <circle cx="12" cy="12" r="10" fill="#22c55e" />
                    <path
                      d="M8 12l2.5 2.5L16 9"
                      stroke="white"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
                <h1>Check your email</h1>
                <p>
                  We&apos;ve sent a verification link to{" "}
                  <strong>{email}</strong>. Please check your inbox and click
                  the link to verify your account.
                </p>
                <Link href="/login" className="back-to-login-btn">
                  Back to Sign In
                </Link>
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

          <div className="login-cta-card">
            <div className="cta-text">
              <p>Already have an account?</p>
              <p className="orange-text">
                Sign in and continue your journey with ElevAIte.
              </p>
            </div>
            <Link href="/login" className="cta-button">
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

  return (
    <div className="signup-page-container">
      <div className="left-column">
        <div className="main-panel">
          <div className="logo-container">
            <Image
              src="/images/logos/logo.png"
              alt="ElevAIte"
              width={85}
              height={27}
              priority
            />
          </div>

          <div className="form-wrapper">
            <div className="signup-heading">
              <h1>Create your account.</h1>
              <p>Join ElevAIte and start exploring the power of AI</p>
            </div>

            <form className="signup-form" onSubmit={handleFormSubmit}>
              <div className="name-row">
                <div className="input-group">
                  <label htmlFor="firstName">First Name*</label>
                  <div className="input-wrapper">
                    <span className="input-icon">
                      <UserIcon />
                    </span>
                    <div className="divider" />
                    <input
                      id="firstName"
                      type="text"
                      placeholder="John"
                      value={firstName}
                      onChange={(e) => {
                        setFirstName(e.target.value);
                      }}
                      required
                      disabled={isLoading}
                    />
                  </div>
                </div>

                <div className="input-group">
                  <label htmlFor="lastName">Last Name*</label>
                  <div className="input-wrapper">
                    <span className="input-icon">
                      <UserIcon />
                    </span>
                    <div className="divider" />
                    <input
                      id="lastName"
                      type="text"
                      placeholder="Smith"
                      value={lastName}
                      onChange={(e) => {
                        setLastName(e.target.value);
                      }}
                      required
                      disabled={isLoading}
                    />
                  </div>
                </div>
              </div>

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
                    placeholder="Create a strong password"
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
                {password.length > 0 && (
                  <div className="password-requirements">
                    <span
                      className={
                        passwordValidation.minLength ? "valid" : "invalid"
                      }
                    >
                      • At least 9 characters
                    </span>
                    <span
                      className={
                        passwordValidation.hasLowercase ? "valid" : "invalid"
                      }
                    >
                      • One lowercase letter
                    </span>
                    <span
                      className={
                        passwordValidation.hasUppercase ? "valid" : "invalid"
                      }
                    >
                      • One uppercase letter
                    </span>
                    <span
                      className={
                        passwordValidation.hasDigit ? "valid" : "invalid"
                      }
                    >
                      • One digit
                    </span>
                    <span
                      className={
                        passwordValidation.hasSpecial ? "valid" : "invalid"
                      }
                    >
                      • One special character (!@#$%^&amp;*...)
                    </span>
                  </div>
                )}
              </div>

              <div className="input-group">
                <label htmlFor="confirmPassword">Confirm Password*</label>
                <div className="input-wrapper">
                  <span className="input-icon">
                    <LockIcon />
                  </span>
                  <div className="divider" />
                  <input
                    id="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="Confirm your password"
                    value={confirmPassword}
                    onChange={(e) => {
                      setConfirmPassword(e.target.value);
                    }}
                    required
                    disabled={isLoading}
                  />
                  <button
                    type="button"
                    className="toggle-password"
                    onClick={() => {
                      setShowConfirmPassword(!showConfirmPassword);
                    }}
                    aria-label={
                      showConfirmPassword ? "Hide password" : "Show password"
                    }
                  >
                    {showConfirmPassword ? <EyeIcon /> : <EyeOffIcon />}
                  </button>
                </div>
                {confirmPassword.length > 0 && password !== confirmPassword && (
                  <p className="error-message">Passwords do not match</p>
                )}
              </div>

              {error ? <p className="credentials-error">{error}</p> : null}

              <button type="submit" className="submit-btn" disabled={isLoading}>
                {isLoading ? "Creating account..." : "Sign Up"}
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
                  Sign up with Google
                </button>
                <button
                  type="button"
                  className="social-btn"
                  disabled={isLoading}
                >
                  <SsoIcon />
                  Sign up with SSO
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

        <div className="login-cta-card">
          <div className="cta-text">
            <p>Already have an account?</p>
            <p className="orange-text">
              Sign in and continue your journey with ElevAIte.
            </p>
          </div>
          <Link href="/login" className="cta-button">
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

export default SignUp;
