"use client";

import { useState, useEffect } from "react";
import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import { ProjectSidebar } from "../components/advanced/ProjectSidebar";
import { TOTPSetup, SMSMFASetup } from "../components/mfa";
import { UserDetailResponse, MfaSetupResponse } from "../lib/authApiClient";
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
  const [selectedCategory, setSelectedCategory] = useState<string>("profile");
  const [selectedSubcategory, setSelectedSubcategory] = useState<string>("");

  // Password change form state
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  // Password visibility state
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // MFA toggle state
  const [totpEnabled, setTotpEnabled] = useState(false);
  const [smsEnabled, setSmsEnabled] = useState(false);

  // MFA modal and setup state
  const [showTOTPModal, setShowTOTPModal] = useState(false);
  const [showSMSModal, setShowSMSModal] = useState(false);
  const [userDetails, setUserDetails] = useState<UserDetailResponse | null>(
    null
  );
  const [totpSetupData, setTotpSetupData] = useState<MfaSetupResponse | null>(
    null
  );
  const [mfaError, setMfaError] = useState<string>("");
  const [isLoadingMFA, setIsLoadingMFA] = useState(false);

  // Load user details on component mount
  useEffect(() => {
    loadUserDetails();
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
      const response = await fetch("/api/auth/mfa/activate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ totp_code: code }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to verify TOTP code");
      }

      setShowTOTPModal(false);
      await loadUserDetails();
    } catch (error) {
      setMfaError(
        error instanceof Error ? error.message : "Failed to verify TOTP code"
      );
      throw error;
    }
  };

  // SMS MFA setup functions
  const handleSetupSMS = async (phoneNumber: string) => {
    try {
      setMfaError("");
      const response = await fetch("/api/sms-mfa/setup", {
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
    } catch (error) {
      setMfaError(
        error instanceof Error ? error.message : "Failed to setup SMS MFA"
      );
      throw error;
    }
  };

  const handleVerifySMS = async (code: string) => {
    try {
      setMfaError("");
      const response = await fetch("/api/sms-mfa/verify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ mfa_code: code }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to verify SMS code");
      }

      setShowSMSModal(false);
      await loadUserDetails();
    } catch (error) {
      setMfaError(
        error instanceof Error ? error.message : "Failed to verify SMS code"
      );
      throw error;
    }
  };

  const handleChangePassword = async (): Promise<void> => {
    if (!currentPassword) {
      setError("Current password is required");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("New passwords don't match");
      return;
    }

    if (newPassword.length < 9) {
      setError("New password must be at least 9 characters");
      return;
    }

    const hasUppercase = /[A-Z]/.test(newPassword);
    const hasLowercase = /[a-z]/.test(newPassword);
    const hasNumber = /[0-9]/.test(newPassword);
    const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(newPassword);

    if (!hasUppercase || !hasLowercase || !hasNumber || !hasSpecial) {
      setError(
        "New password must include uppercase, lowercase, numbers, and special characters"
      );
      return;
    }

    if (currentPassword === newPassword) {
      setError("New password must be different from current password");
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      const response = await fetch("/api/auth/change-password-user", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setIsSuccess(true);
        setCurrentPassword("");
        setNewPassword("");
        setConfirmPassword("");
      } else {
        setError(data.detail || "Failed to change password. Please try again.");
      }
    } catch (err) {
      console.error("Change password error:", err);
      setError("An unexpected error occurred. Please try again.");
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
                  onClick={() => setIsSuccess(false)}
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
        <div className="settings-content-display">
          <h2>Multi-Factor Authentication</h2>
          <p className="hint-text">
            Secure your account with an additional layer of protection.
          </p>

          <div className="mfa-form-container">
            <div className="mfa-method-section">
              <div className="mfa-method-header">
                <div className="mfa-method-info">
                  <h3>Authenticator App (TOTP)</h3>
                  <p>
                    Use an authenticator app like Google Authenticator or Authy
                    to generate codes.
                  </p>
                </div>
                <label className="mfa-toggle">
                  <input
                    type="checkbox"
                    checked={totpEnabled}
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
                  <span className="mfa-toggle-slider"></span>
                </label>
              </div>
            </div>

            <div className="mfa-separator"></div>

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
                <label className="mfa-toggle">
                  <input
                    type="checkbox"
                    checked={smsEnabled}
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
                  <span className="mfa-toggle-slider"></span>
                </label>
              </div>
            </div>
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
        {showTOTPModal && totpSetupData && (
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
        {showSMSModal && (
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
                onSetup={handleSetupSMS}
                onVerify={handleVerifySMS}
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
                  {/* Profile Category */}
                  <CommonButton
                    className={`category-button ${selectedCategory === "profile" ? "selected" : ""}`}
                    onClick={() => handleCategoryClick("profile")}
                    noBackground
                  >
                    <span>Profile</span>
                    <ElevaiteIcons.SVGChevron className="accordion-arrow" />
                  </CommonButton>

                  {/* Account Category */}
                  <CommonButton
                    className={`category-button ${selectedCategory === "account" ? "selected" : ""}`}
                    onClick={() => handleCategoryClick("account")}
                    noBackground
                  >
                    <span>Account</span>
                    <ElevaiteIcons.SVGChevron className="accordion-arrow" />
                  </CommonButton>

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
