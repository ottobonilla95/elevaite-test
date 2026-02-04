"use client";
import { GoogleColorIcon, CommonButton } from "@repo/ui/components";
import type { JSX, FormEvent } from "react";
import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import Image from "next/image";
import { signIn } from "next-auth/react";
import {
  MailIcon,
  LockIcon,
  EyeIcon,
  EyeOffIcon,
  UserIcon,
  SsoIcon,
  ArrowRightIcon,
} from "../../components/icons";
import { Copyright } from "../../components/Copyright";
import { VideoPanel } from "../../components/VideoPanel";
import "./page.scss";

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

            <Copyright />
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

        <VideoPanel />
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
                  <CommonButton
                    overrideClass
                    className="toggle-password"
                    onClick={() => {
                      setShowConfirmPassword(!showConfirmPassword);
                    }}
                    aria-label={
                      showConfirmPassword ? "Hide password" : "Show password"
                    }
                  >
                    {showConfirmPassword ? <EyeIcon /> : <EyeOffIcon />}
                  </CommonButton>
                </div>
                {confirmPassword.length > 0 && password !== confirmPassword && (
                  <p className="error-message">Passwords do not match</p>
                )}
              </div>

              {error ? <p className="credentials-error">{error}</p> : null}

              <CommonButton
                overrideClass
                className="submit-btn"
                type="submit"
                disabled={isLoading}
              >
                {isLoading ? "Creating account..." : "Sign Up"}
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
                  Sign up with Google
                </CommonButton>
                <CommonButton
                  overrideClass
                  className="social-btn"
                  disabled={isLoading}
                >
                  <SsoIcon />
                  Sign up with SSO
                </CommonButton>
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
