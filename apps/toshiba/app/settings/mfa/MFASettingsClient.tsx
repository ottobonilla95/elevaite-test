"use client";

import { useState, useEffect } from "react";
import { User } from "next-auth";
import { UserDetailResponse, MfaSetupResponse } from "../../lib/authApiClient";
import {
  MFAStatusIndicator,
  TOTPSetup,
  SMSMFASetup,
} from "../../components/mfa";

interface MFASettingsClientProps {
  user: User;
  accessToken: string;
}

export function MFASettingsClient({
  user: _user,
}: MFASettingsClientProps): JSX.Element {
  const [userDetails, setUserDetails] = useState<UserDetailResponse | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [showTOTPSetup, setShowTOTPSetup] = useState(false);
  const [showSMSSetup, setShowSMSSetup] = useState(false);
  const [totpSetupData, setTotpSetupData] = useState<MfaSetupResponse | null>(
    null
  );

  useEffect(() => {
    loadUserDetails();
  }, []);

  const loadUserDetails = async () => {
    try {
      setIsLoading(true);
      const response = await fetch("/api/auth/me");

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to load user details");
      }

      const details = await response.json();
      setUserDetails(details);
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Failed to load user details"
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleSetupTOTP = async () => {
    try {
      setError("");
      const response = await fetch("/api/auth/mfa/setup", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to setup TOTP");
      }

      const setupData = await response.json();
      setTotpSetupData(setupData);
      setShowTOTPSetup(true);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Failed to setup TOTP");
    }
  };

  const handleVerifyTOTP = async (code: string) => {
    try {
      setError("");
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

      setShowTOTPSetup(false);
      setTotpSetupData(null);
      await loadUserDetails();
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Failed to verify TOTP code"
      );
      throw error;
    }
  };

  const handleSetupSMS = async (phoneNumber: string) => {
    try {
      setError("");
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
      setError(
        error instanceof Error ? error.message : "Failed to setup SMS MFA"
      );
      throw error;
    }
  };

  const handleVerifySMS = async (code: string) => {
    try {
      setError("");
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

      setShowSMSSetup(false);
      await loadUserDetails();
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Failed to verify SMS code"
      );
      throw error;
    }
  };

  if (isLoading) {
    return (
      <div className="ui-flex ui-justify-center ui-items-center ui-py-12">
        <div className="ui-text-gray-400">Loading...</div>
      </div>
    );
  }

  if (!userDetails) {
    return (
      <div className="ui-text-center ui-py-12">
        <div className="ui-text-red-500">Failed to load user details</div>
        <button
          onClick={loadUserDetails}
          className="ui-mt-4 ui-px-4 ui-py-2 ui-bg-[#E75F33] ui-text-white ui-rounded ui-hover:ui-bg-[#d54d26]"
        >
          Retry
        </button>
      </div>
    );
  }

  // Show TOTP setup modal
  if (showTOTPSetup && totpSetupData) {
    return (
      <TOTPSetup
        secret={totpSetupData.secret}
        qrCodeUri={totpSetupData.qr_code_uri}
        onVerify={handleVerifyTOTP}
        onCancel={() => {
          setShowTOTPSetup(false);
          setTotpSetupData(null);
          setError("");
        }}
        error={error}
      />
    );
  }

  // Show SMS setup modal
  if (showSMSSetup) {
    return (
      <SMSMFASetup
        onSetup={handleSetupSMS}
        onVerify={handleVerifySMS}
        onCancel={() => {
          setShowSMSSetup(false);
          setError("");
        }}
        error={error}
        initialPhoneNumber={userDetails.phone_number || ""}
      />
    );
  }

  return (
    <div className="ui-space-y-8">
      {/* Current MFA Status */}
      <div className="ui-bg-[#1a1a1a] ui-rounded-lg ui-p-6 ui-border ui-border-gray-700">
        <h2 className="ui-text-xl ui-font-semibold ui-text-white ui-mb-4">
          Current Status
        </h2>
        <MFAStatusIndicator
          mfaEnabled={userDetails.mfa_enabled}
          smsMfaEnabled={userDetails.sms_mfa_enabled}
          phoneVerified={userDetails.phone_verified}
        />
      </div>

      {/* TOTP Authentication */}
      <div className="ui-bg-[#1a1a1a] ui-rounded-lg ui-p-6 ui-border ui-border-gray-700">
        <div className="ui-flex ui-justify-between ui-items-start ui-mb-4">
          <div>
            <h3 className="ui-text-lg ui-font-semibold ui-text-white ui-mb-2">
              Authenticator App (TOTP)
            </h3>
            <p className="ui-text-gray-400 ui-text-sm">
              Use an authenticator app like Google Authenticator or Authy to
              generate codes
            </p>
          </div>
          <div className="ui-flex ui-items-center ui-gap-2">
            {userDetails.mfa_enabled ? (
              <span className="ui-px-3 ui-py-1 ui-bg-green-100 ui-text-green-800 ui-rounded-full ui-text-sm ui-font-medium">
                Enabled
              </span>
            ) : (
              <button
                onClick={handleSetupTOTP}
                className="ui-px-4 ui-py-2 ui-bg-[#E75F33] ui-text-white ui-rounded ui-hover:ui-bg-[#d54d26] ui-transition-colors"
              >
                Set Up
              </button>
            )}
          </div>
        </div>
      </div>

      {/* SMS Authentication */}
      <div className="ui-bg-[#1a1a1a] ui-rounded-lg ui-p-6 ui-border ui-border-gray-700">
        <div className="ui-flex ui-justify-between ui-items-start ui-mb-4">
          <div>
            <h3 className="ui-text-lg ui-font-semibold ui-text-white ui-mb-2">
              SMS Authentication
            </h3>
            <p className="ui-text-gray-400 ui-text-sm">
              Receive verification codes via text message
            </p>
            {userDetails.phone_number && (
              <p className="ui-text-gray-300 ui-text-sm ui-mt-1">
                Phone: {userDetails.phone_number}
              </p>
            )}
          </div>
          <div className="ui-flex ui-items-center ui-gap-2">
            {userDetails.sms_mfa_enabled ? (
              <span className="ui-px-3 ui-py-1 ui-bg-green-100 ui-text-green-800 ui-rounded-full ui-text-sm ui-font-medium">
                {userDetails.phone_verified ? "Enabled" : "Setup Required"}
              </span>
            ) : (
              <button
                onClick={() => setShowSMSSetup(true)}
                className="ui-px-4 ui-py-2 ui-bg-[#E75F33] ui-text-white ui-rounded ui-hover:ui-bg-[#d54d26] ui-transition-colors"
              >
                Set Up
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="ui-bg-red-900 ui-border ui-border-red-700 ui-text-red-100 ui-px-4 ui-py-3 ui-rounded">
          {error}
        </div>
      )}
    </div>
  );
}
