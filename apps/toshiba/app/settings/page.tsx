"use client";

import { useState, useEffect, useRef } from "react";
import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import { ProjectSidebar } from "../components/advanced/ProjectSidebar";
import { TOTPSetup, SMSMFASetup, EmailMFASetup } from "../components/mfa";
import { UserDetailResponse, MfaSetupResponse } from "../lib/authApiClient";
import { getMFAConfig, isMFADisableAllowed } from "../lib/mfaConfig";
import { changeUserPassword } from "../lib/actions";
import { toggleBiometricMFA } from "../lib/services/userService";
import "./page.scss";

const LockIcon = ({ size = 14 }: { size?: number }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
  >
    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
    <circle cx="12" cy="16" r="1" />
    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
  </svg>
);

const KeyIcon = ({ size = 14 }: { size?: number }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
  >
    <circle cx="7" cy="7" r="3" />
    <path d="m10 10 11 11" />
    <path d="m15 15 1 1" />
    <path d="m18 18 1 1" />
  </svg>
);

const EyeIcon = ({ size = 16 }: { size?: number }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
  >
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
    <circle cx="12" cy="12" r="3" />
  </svg>
);

const EyeOffIcon = ({ size = 16 }: { size?: number }) => (
  <svg
    width={size}
    height={size}
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

export default function Settings(): JSX.Element {
  const [isExpanded, setIsExpanded] = useState(false);
  // FIXME: Remove this when there are more categories in /settings - currently defaulting to security/change-password since it's the only active category
  const [selectedCategory, setSelectedCategory] = useState<string>("security");
  const [selectedSubcategory, setSelectedSubcategory] =
    useState<string>("change-password");

  const mfaConfig = getMFAConfig();
  const allowDisableAll = isMFADisableAllowed();

  const getEnabledMFACount = () => {
    let count = 0;
    if (emailEnabled) count++;
    if (smsEnabled) count++;
    if (totpEnabled) count++;
    if (biometricEnabled) count++;
    return count;
  };

  const shouldDisableToggle = (currentMethodEnabled: boolean) => {
    if (allowDisableAll) return false;
    const enabledCount = getEnabledMFACount();
    return currentMethodEnabled && enabledCount === 1;
  };

  // Password change form state
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const isSubmittingRef = useRef(false);

  // Password visibility state
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // MFA toggle state
  const [totpEnabled, setTotpEnabled] = useState(false);
  const [smsEnabled, setSmsEnabled] = useState(false);
  const [emailEnabled, setEmailEnabled] = useState(false);
  const [biometricEnabled, setBiometricEnabled] = useState(false);

  // MFA modal and setup state
  const [showTOTPModal, setShowTOTPModal] = useState(false);
  const [showSMSModal, setShowSMSModal] = useState(false);
  const [showEmailModal, setShowEmailModal] = useState(false);
  // const [showBiometricModal, setShowBiometricModal] = useState(false);
  const [userDetails, setUserDetails] = useState<UserDetailResponse | null>(
    null
  );
  const [totpSetupData, setTotpSetupData] = useState<MfaSetupResponse | null>(
    null
  );
  const [mfaError, setMfaError] = useState<string>("");
  const [successMessage, setSuccessMessage] = useState<string>("");
  const [isLoadingMFA, setIsLoadingMFA] = useState(false);

  // Load user details on component mount
  useEffect(() => {
    loadUserDetails();
  }, []);

  // Handle hash navigation to MFA section
  useEffect(() => {
    const hash = window.location.hash;

    if (hash === "#mfa") {
      // Set the correct category and subcategory to show MFA section
      setSelectedCategory("security");
      setSelectedSubcategory("multi-factor-auth");

      // Wait for the component to render, then scroll to MFA section
      setTimeout(() => {
        const mfaSection = document.getElementById("mfa-section");
        if (mfaSection) {
          mfaSection.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }, 100);
    }
    // FIXME: Remove this when there are more categories in /settings - currently all hashes default to security category
    else if (hash === "#change-password") {
      // Set the correct category and subcategory to show change password section
      setSelectedCategory("security");
      setSelectedSubcategory("change-password");

      // Wait for the component to render, then scroll to change password section
      setTimeout(() => {
        const changePasswordSection = document.querySelector(
          ".settings-content-display"
        );
        if (changePasswordSection) {
          changePasswordSection.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
        }
      }, 100);
    }
  }, []);

  // Load user details from API
  const loadUserDetails = async () => {
    try {
      setIsLoadingMFA(true);
      const response = await fetch("/api/auth/me");

      if (!response.ok) {
        throw new Error("Failed to load user details");
      }

      const data = await response.json();
      setUserDetails(data);
      setTotpEnabled(data.mfa_enabled || false);
      setSmsEnabled(data.sms_mfa_enabled || false);
      setEmailEnabled(data.email_mfa_enabled || false);
      setBiometricEnabled(data.biometric_mfa_enabled || false);
    } catch (error) {
      setMfaError(
        error instanceof Error ? error.message : "Failed to load user details"
      );
    } finally {
      setIsLoadingMFA(false);
    }
  };

  // TOTP MFA setup functions
  const handleSetupTOTP = async () => {
    try {
      setMfaError("");
      const response = await fetch("/api/auth/mfa/setup", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to setup TOTP MFA");
      }

      const data = await response.json();
      setTotpSetupData(data);
      setShowTOTPModal(true);
    } catch (error) {
      setMfaError(
        error instanceof Error ? error.message : "Failed to setup TOTP MFA"
      );
      setTotpEnabled(false); // Reset toggle on error
    }
  };

  const handleVerifyTOTP = async (code: string) => {
    try {
      setMfaError("");
      setIsLoadingMFA(true);
      const response = await fetch("/api/auth/mfa/verify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ code }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to verify TOTP code");
      }

      // Success! Close modal and show success message
      setShowTOTPModal(false);
      setTotpEnabled(true);
      await loadUserDetails(); // Refresh user details
    } catch (error) {
      setMfaError(
        error instanceof Error ? error.message : "Failed to verify TOTP code"
      );
      throw error; // Re-throw to be handled by TOTPSetup component
    } finally {
      setIsLoadingMFA(false);
    }
  };

  const handleDisableTOTP = async () => {
    try {
      setMfaError("");
      setIsLoadingMFA(true);
      const response = await fetch("/api/auth/mfa/disable", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to disable TOTP MFA");
      }

      setTotpEnabled(false);
      await loadUserDetails(); // Refresh user details
    } catch (error) {
      setMfaError(
        error instanceof Error ? error.message : "Failed to disable TOTP MFA"
      );
      setTotpEnabled(true); // Reset toggle on error
    } finally {
      setIsLoadingMFA(false);
    }
  };

  // SMS MFA setup functions
  const handleSetupSMS = async (phoneNumber: string) => {
    try {
      setMfaError("");
      setIsLoadingMFA(true);
      const response = await fetch("/api/auth/mfa/sms/setup", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ phone_number: phoneNumber }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to setup SMS MFA");
      }

      // SMS sent successfully
      return true;
    } catch (error) {
      setMfaError(
        error instanceof Error ? error.message : "Failed to setup SMS MFA"
      );
      throw error;
    } finally {
      setIsLoadingMFA(false);
    }
  };

  const handleVerifySMS = async (code: string) => {
    try {
      setMfaError("");
      setIsLoadingMFA(true);
      const response = await fetch("/api/auth/mfa/sms/verify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ code }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to verify SMS code");
      }

      // Success! Close modal and show success message
      setShowSMSModal(false);
      setSmsEnabled(true);
      await loadUserDetails(); // Refresh user details
      return true;
    } catch (error) {
      setMfaError(
        error instanceof Error ? error.message : "Failed to verify SMS code"
      );
      throw error;
    } finally {
      setIsLoadingMFA(false);
    }
  };

  const handleDisableSMS = async () => {
    try {
      setMfaError("");
      setIsLoadingMFA(true);
      const response = await fetch("/api/auth/mfa/sms/disable", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to disable SMS MFA");
      }

      setSmsEnabled(false);
      await loadUserDetails(); // Refresh user details
    } catch (error) {
      setMfaError(
        error instanceof Error ? error.message : "Failed to disable SMS MFA"
      );
      setSmsEnabled(true); // Reset toggle on error
    } finally {
      setIsLoadingMFA(false);
    }
  };

  // Email MFA setup functions
  const handleSetupEmail = async () => {
    try {
      setMfaError("");
      setIsLoadingMFA(true);
      const response = await fetch("/api/email-mfa/setup", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to setup Email MFA");
      }

      // Email sent successfully
      return true;
    } catch (error) {
      setMfaError(
        error instanceof Error ? error.message : "Failed to setup Email MFA"
      );
      throw error;
    } finally {
      setIsLoadingMFA(false);
    }
  };

  const handleVerifyEmail = async (code: string) => {
    try {
      setMfaError("");
      setIsLoadingMFA(true);
      const response = await fetch("/api/email-mfa/verify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ mfa_code: code }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to verify Email code");
      }

      // Success! Close modal and show success message
      setShowEmailModal(false);
      setEmailEnabled(true);
      await loadUserDetails(); // Refresh user details
      return true;
    } catch (error) {
      setMfaError(
        error instanceof Error ? error.message : "Failed to verify Email code"
      );
      throw error;
    } finally {
      setIsLoadingMFA(false);
    }
  };

  const handleDisableEmail = async () => {
    try {
      setMfaError("");
      setIsLoadingMFA(true);
      const response = await fetch("/api/email-mfa/disable", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to disable Email MFA");
      }

      setEmailEnabled(false);
      await loadUserDetails(); // Refresh user details
    } catch (error) {
      setMfaError(
        error instanceof Error
          ? error.message
          : "Failed to disable Email MFA"
      );
      setEmailEnabled(true); // Reset toggle on error
    } finally {
      setIsLoadingMFA(false);
    }
  };

  // Biometric MFA functions
  const handleDisableBiometric = async () => {
    try {
      setMfaError("");
      setIsLoadingMFA(true);

      const result = await toggleBiometricMFA(false);

      if (result.success) {
        setBiometricEnabled(false);
        setSuccessMessage("Biometric MFA disabled. All registered devices have been removed.");
        setTimeout(() => setSuccessMessage(""), 5000);
        await loadUserDetails(); // Refresh user details
      } else {
        throw new Error(result.message);
      }
    } catch (error) {
      setMfaError(
        error instanceof Error
          ? error.message
          : "Failed to disable Biometric MFA"
      );
      setBiometricEnabled(true); // Reset toggle on error
    } finally {
      setIsLoadingMFA(false);
    }
  };

  // Password change handler
  const handleChangePassword = async () => {
    // Only allow one submission at a time
    if (isSubmittingRef.current) {
      return;
    }

    if (!currentPassword || !newPassword || !confirmPassword) {
      setError("All fields are required.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsSubmitting(true);
    setError(null);
    isSubmittingRef.current = true; // Mark as in progress

    try {
      const result = await changeUserPassword(currentPassword, newPassword);

      if (result.success) {
        setIsSuccess(true);
        setCurrentPassword("");
        setNewPassword("");
        setConfirmPassword("");
      } else {
        setError(result.message);
        isSubmittingRef.current = false; // Reset on error to allow retry
      }
    } catch (err) {
      console.error("Change password error:", err);
      setError("An unexpected error occurred. Please try again.");
      isSubmittingRef.current = false; // Reset on error to allow retry
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCategoryClick = (category: string) => {
    if (selectedCategory === category) {
      // If clicking the same category, toggle it closed
      setSelectedCategory("");
      setSelectedSubcategory("");
    } else {
      // If clicking a different category, open it
      setSelectedCategory(category);
      setSelectedSubcategory(""); // Reset subcategory when changing main category
    }
  };

  const handleSubcategoryClick = (subcategory: string) => {
    setSelectedSubcategory(subcategory);
  };

  const renderContent = () => {
    if (
      selectedCategory === "security" &&
      selectedSubcategory === "change-password"
    ) {
      return (
        <div className="settings-content-display">
          <h2>Change Password</h2>
          <p className="hint-text">
            Your new password must be at least 9 characters long and include
            uppercase letters, lowercase letters, numbers, and special
            characters.
          </p>

          <div className="password-change-form-container">
            {isSuccess ? (
              <div className="success-message">
                <h3>Password Changed Successfully</h3>
                <p>
                  Your password has been successfully updated. You can continue
                  using the system with your new password.
                </p>
                <button
                  className="continue-button"
                  onClick={() => {
                    setIsSuccess(false);
                    isSubmittingRef.current = false; // Reset ref when continuing
                  }}
                  type="button"
                >
                  Continue
                </button>
              </div>
            ) : (
              <form
                className="password-form"
                onSubmit={(e) => {
                  e.preventDefault();
                  void handleChangePassword();
                }}
              >
                <div className="form-fields">
                  <div className="form-field">
                    <label htmlFor="currentPassword">Current Password</label>
                    <div className="password-input-container">
                      <div className="password-lock-icon">
                        <LockIcon size={16} />
                      </div>
                      <input
                        id="currentPassword"
                        type={showCurrentPassword ? "text" : "password"}
                        value={currentPassword}
                        onChange={(e) => setCurrentPassword(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            document.getElementById("newPassword")?.focus();
                            e.preventDefault();
                          }
                        }}
                        required
                      />
                      <button
                        type="button"
                        className="password-toggle"
                        onClick={() =>
                          setShowCurrentPassword(!showCurrentPassword)
                        }
                      >
                        {showCurrentPassword ? <EyeIcon /> : <EyeOffIcon />}
                      </button>
                    </div>
                  </div>

                  <div className="form-field">
                    <label htmlFor="newPassword">New Password</label>
                    <div className="password-input-container">
                      <div className="password-lock-icon">
                        <LockIcon size={16} />
                      </div>
                      <input
                        id="newPassword"
                        type={showNewPassword ? "text" : "password"}
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            document.getElementById("confirmPassword")?.focus();
                            e.preventDefault();
                          }
                        }}
                        required
                      />
                      <button
                        type="button"
                        className="password-toggle"
                        onClick={() => setShowNewPassword(!showNewPassword)}
                      >
                        {showNewPassword ? <EyeIcon /> : <EyeOffIcon />}
                      </button>
                    </div>
                  </div>

                  <div className="form-field">
                    <label htmlFor="confirmPassword">
                      Confirm New Password
                    </label>
                    <div className="password-input-container">
                      <div className="password-lock-icon">
                        <LockIcon size={16} />
                      </div>
                      <input
                        id="confirmPassword"
                        type={showConfirmPassword ? "text" : "password"}
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            void handleChangePassword();
                            e.preventDefault();
                          }
                        }}
                        required
                      />
                      <button
                        type="button"
                        className="password-toggle"
                        onClick={() =>
                          setShowConfirmPassword(!showConfirmPassword)
                        }
                      >
                        {showConfirmPassword ? <EyeIcon /> : <EyeOffIcon />}
                      </button>
                    </div>
                  </div>

                  {error ? <div className="error-message">{error}</div> : null}

                  <div className="button-group">
                    <button
                      className="submit-button"
                      disabled={isSubmitting}
                      type="submit"
                    >
                      {isSubmitting ? "Changing..." : "Change Password"}
                    </button>
                  </div>
                </div>
              </form>
            )}
          </div>
        </div>
      );
    }

    if (
      selectedCategory === "security" &&
      selectedSubcategory === "multi-factor-auth"
    ) {
      return (
        <div className="settings-content-display" id="mfa-section">
          <h2>Multi-Factor Authentication</h2>
          <p className="hint-text">
            Secure your account with an additional layer of protection.
          </p>

          <div className="mfa-form-container">
            {mfaConfig.email && (
              <>
                <div className="mfa-method-section">
                  <div className="mfa-method-header">
                    <div className="mfa-method-info">
                      <h3>Email Authentication</h3>
                      <p>
                        {emailEnabled && userDetails?.email
                          ? `Send a code to ${userDetails.email.replace(/(.{2})(.*)(@.*)/, "$1***$3")}`
                          : "Use your email address to receive verification codes."}
                      </p>
                    </div>
                    <label
                      className="mfa-toggle"
                      title={
                        shouldDisableToggle(emailEnabled)
                          ? "Disabling MFA is not supported. At least one MFA method must remain enabled."
                          : ""
                      }
                    >
                      <input
                        type="checkbox"
                        checked={emailEnabled}
                        disabled={shouldDisableToggle(emailEnabled)}
                        onChange={(e) => {
                          const isEnabled = e.target.checked;
                          if (isEnabled && !emailEnabled) {
                            setEmailEnabled(true);
                            setShowEmailModal(true);
                          } else {
                            setEmailEnabled(isEnabled);
                          }
                        }}
                      />
                      <span
                        className={`mfa-toggle-slider ${shouldDisableToggle(emailEnabled) ? "disabled" : ""}`}
                      ></span>
                    </label>
                  </div>
                </div>
                {(mfaConfig.totp || mfaConfig.sms || mfaConfig.biometric) && (
                  <div className="mfa-separator"></div>
                )}
              </>
            )}

            {mfaConfig.biometric && (
              <>
                <div className="mfa-method-section">
                  <div className="mfa-method-header">
                    <div className="mfa-method-info">
                      <h3>Biometric Authentication</h3>
                      <p>
                        {biometricEnabled
                          ? "Use fingerprint or face recognition on your mobile device"
                          : "Enable to use biometric login on mobile devices"}
                      </p>
                    </div>
                    <label className="mfa-toggle">
                      <input
                        type="checkbox"
                        checked={biometricEnabled}
                        disabled={isLoadingMFA || shouldDisableToggle(biometricEnabled)}
                        onChange={async (e) => {
                          const isEnabled = e.target.checked;

                          if (isEnabled && !biometricEnabled) {
                            // Enable biometric
                            try {
                              setIsLoadingMFA(true);
                              const result = await toggleBiometricMFA(true);

                              if (result.success) {
                                setBiometricEnabled(true);
                                setSuccessMessage("Biometric MFA enabled. Register devices on your mobile app.");
                                setTimeout(() => setSuccessMessage(""), 5000);
                                await loadUserDetails();
                              } else {
                                setMfaError(result.message);
                                setBiometricEnabled(false);
                              }
                            } catch (error) {
                              setMfaError("Failed to enable biometric MFA");
                              setBiometricEnabled(false);
                            } finally {
                              setIsLoadingMFA(false);
                            }
                          } else if (!isEnabled && biometricEnabled) {
                            // Disable biometric
                            handleDisableBiometric();
                          }
                        }}
                      />
                      <span className="mfa-toggle-slider" />
                    </label>
                  </div>

                  {/* Success message */}
                  {biometricEnabled && (
                    <div className="mfa-status success">
                      Biometric authentication is enabled
                      <p style={{ fontSize: '0.9em', marginTop: '8px', color: '#6b7280' }}>
                        Open your mobile app to register your device with fingerprint or face recognition.
                      </p>
                    </div>
                  )}
                </div>
              </>
            )}

            {mfaConfig.totp && (
              <>
                <div className="mfa-method-section">
                  <div className="mfa-method-header">
                    <div className="mfa-method-info">
                      <h3>Authenticator App (TOTP)</h3>
                      <p>
                        Use an authenticator app like Google Authenticator or
                        Authy to generate codes.
                      </p>
                    </div>
                    <label
                      className="mfa-toggle"
                      title={
                        shouldDisableToggle(totpEnabled)
                          ? "Disabling MFA is not supported. At least one MFA method must remain enabled."
                          : ""
                      }
                    >
                      <input
                        type="checkbox"
                        checked={totpEnabled}
                        disabled={shouldDisableToggle(totpEnabled)}
                        onChange={(e) => {
                          const isEnabled = e.target.checked;
                          if (isEnabled && !totpEnabled) {
                            // Switching from disabled to enabled - show modal
                            handleSetupTOTP();
                          } else {
                            // Just update the visual state for now
                            setTotpEnabled(isEnabled);
                          }
                        }}
                      />
                      <span
                        className={`mfa-toggle-slider ${shouldDisableToggle(totpEnabled) ? "disabled" : ""}`}
                      ></span>
                    </label>
                  </div>
                </div>
                {mfaConfig.sms && <div className="mfa-separator"></div>}
              </>
            )}

            {mfaConfig.sms && (
              <div className="mfa-method-section">
                <div className="mfa-method-header">
                  <div className="mfa-method-info">
                    <h3>SMS Authentication</h3>
                    <p>
                      {smsEnabled && userDetails?.phone_number
                        ? `Send an SMS code to ${userDetails.phone_number.replace(/(\d{3})(\d{3})(\d{4})/, "***-***-$3")}`
                        : "Use your phone number to receive SMS codes."}
                    </p>
                  </div>
                  <label
                    className="mfa-toggle"
                    title={
                      shouldDisableToggle(smsEnabled)
                        ? "Disabling MFA is not supported. At least one MFA method must remain enabled."
                        : ""
                    }
                  >
                    <input
                      type="checkbox"
                      checked={smsEnabled}
                      disabled={shouldDisableToggle(smsEnabled)}
                      onChange={(e) => {
                        const isEnabled = e.target.checked;
                        if (isEnabled && !smsEnabled) {
                          // Switching from disabled to enabled - show modal
                          setSmsEnabled(true); // Set visual state first
                          setShowSMSModal(true);
                        } else {
                          // Just update the visual state for now
                          setSmsEnabled(isEnabled);
                        }
                      }}
                    />
                    <span
                      className={`mfa-toggle-slider ${shouldDisableToggle(smsEnabled) ? "disabled" : ""}`}
                    ></span>
                  </label>
                </div>
              </div>
            )}
          </div>
        </div>
      );
    }

    // Show nothing when no specific subcategory is selected
    return null;
  };

  // Modal components
  const renderModals = () => {
    return (
      <>
        {/* TOTP Setup Modal */}
        {mfaConfig.totp && showTOTPModal && totpSetupData && (
          <div
            className="mfa-modal-overlay"
            onClick={(e) => {
              if (e.target === e.currentTarget) {
                setShowTOTPModal(false);
                setTotpEnabled(false); // Reset toggle on cancel
                setMfaError("");
              }
            }}
          >
            <div className="mfa-modal-content">
              <TOTPSetup
                secret={totpSetupData.secret}
                qrCodeUri={totpSetupData.qr_code_uri}
                onVerify={handleVerifyTOTP}
                onCancel={() => {
                  setShowTOTPModal(false);
                  setTotpEnabled(false); // Reset toggle on cancel
                  setMfaError("");
                }}
                error={mfaError}
                isLoading={isLoadingMFA}
              />
            </div>
          </div>
        )}

        {/* SMS Setup Modal */}
        {mfaConfig.sms && showSMSModal && (
          <div
            className="mfa-modal-overlay"
            onClick={(e) => {
              if (e.target === e.currentTarget) {
                setShowSMSModal(false);
                setSmsEnabled(false); // Reset toggle on cancel
                setMfaError("");
              }
            }}
          >
            <div className="mfa-modal-content">
              <SMSMFASetup
                onSetup={async (phoneNumber: string) => {
                  await handleSetupSMS(phoneNumber);
                }}
                onVerify={async (code: string) => {
                  await handleVerifySMS(code);
                }}
                onCancel={() => {
                  setShowSMSModal(false);
                  setSmsEnabled(false); // Reset toggle on cancel
                  setMfaError("");
                }}
                error={mfaError}
                initialPhoneNumber={userDetails?.phone_number || ""}
              />
            </div>
          </div>
        )}

        {/* Email MFA Setup Modal */}
        {mfaConfig.email && showEmailModal && (
          <div
            className="mfa-modal-overlay"
            onClick={(e) => {
              if (e.target === e.currentTarget) {
                setShowEmailModal(false);
                setEmailEnabled(false); // Reset toggle on cancel
                setMfaError("");
              }
            }}
          >
            <div className="mfa-modal-content">
              <EmailMFASetup
                onSetup={async () => {
                  await handleSetupEmail();
                }}
                onVerify={async (code: string) => {
                  await handleVerifyEmail(code);
                }}
                onCancel={() => {
                  setShowEmailModal(false);
                  setEmailEnabled(false); // Reset toggle on cancel
                  setMfaError("");
                }}
                error={mfaError}
                userEmail={userDetails?.email || ""}
              />
            </div>
          </div>
        )}
      </>
    );
  };

  return (
    <>
      <main
        className={`settings-advanced-container ${isExpanded ? "sidebar-expanded" : "sidebar-collapsed"}`}
      >
        <ProjectSidebar isExpanded={isExpanded} setIsExpanded={setIsExpanded} />
        <div className="settings-main-area">
          <div className="settings-header">
            <span>Settings</span>
          </div>
          <div className="settings-content">
            <div className="settings-layout">
              <div className="settings-left-column">
                <div className="category-navigation">
                  {/* Profile Category - Hidden */}
                  {/* <CommonButton
                    className={`category-button ${selectedCategory === "profile" ? "selected" : ""}`}
                    onClick={() => handleCategoryClick("profile")}
                    noBackground
                  >
                    <span>Profile</span>
                    <ElevaiteIcons.SVGChevron className="accordion-arrow" />
                  </CommonButton> */}

                  {/* Account Category - Hidden */}
                  {/* <CommonButton
                    className={`category-button ${selectedCategory === "account" ? "selected" : ""}`}
                    onClick={() => handleCategoryClick("account")}
                    noBackground
                  >
                    <span>Account</span>
                    <ElevaiteIcons.SVGChevron className="accordion-arrow" />
                  </CommonButton> */}

                  {/* Security Category */}
                  <CommonButton
                    className={`category-button ${selectedCategory === "security" ? "selected" : ""} ${selectedCategory === "security" ? "expanded" : ""}`}
                    onClick={() => handleCategoryClick("security")}
                    noBackground
                  >
                    <span>Security</span>
                    <ElevaiteIcons.SVGChevron className="accordion-arrow" />
                  </CommonButton>

                  {/* Security Subcategories */}
                  {selectedCategory === "security" && (
                    <div className="subcategory-list">
                      <CommonButton
                        className={`subcategory-button ${selectedSubcategory === "change-password" ? "selected" : ""}`}
                        onClick={() =>
                          handleSubcategoryClick("change-password")
                        }
                        noBackground
                      >
                        <LockIcon size={14} />
                        <span>Change Password</span>
                      </CommonButton>
                      <CommonButton
                        className={`subcategory-button ${selectedSubcategory === "multi-factor-auth" ? "selected" : ""}`}
                        onClick={() =>
                          handleSubcategoryClick("multi-factor-auth")
                        }
                        noBackground
                      >
                        <KeyIcon size={14} />
                        <span>Multi-Factor Authentication</span>
                      </CommonButton>
                    </div>
                  )}
                </div>
              </div>

              <div className="settings-right-column">{renderContent()}</div>
            </div>
          </div>
        </div>
      </main>

      {/* Render MFA Modals */}
      {renderModals()}
    </>
  );
}






