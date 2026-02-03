"use server";

const AUTH_API_URL = process.env.AUTH_API_URL;

export interface MfaVerifyResult {
  success: boolean;
  error?: string;
  accessToken?: string;
  refreshToken?: string;
  passwordChangeRequired?: boolean;
}

export interface MfaResendResult {
  success: boolean;
  error?: string;
}

interface LoginApiResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  password_change_required?: boolean;
}

interface ApiErrorResponse {
  detail?: string;
}

async function parseJsonSafe<T>(response: Response): Promise<T> {
  try {
    return (await response.json()) as T;
  } catch {
    return {} as T;
  }
}

/**
 * Verify TOTP code and complete login
 */
export async function verifyTotpCode(
  email: string,
  password: string,
  code: string,
): Promise<MfaVerifyResult> {
  if (!AUTH_API_URL) {
    return { success: false, error: "Auth service not configured" };
  }

  try {
    const response = await fetch(`${AUTH_API_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        password,
        totp_code: code,
      }),
    });

    if (!response.ok) {
      const errorData = await parseJsonSafe<ApiErrorResponse>(response);
      return {
        success: false,
        error: errorData.detail ?? "Invalid verification code",
      };
    }

    const data = await parseJsonSafe<LoginApiResponse>(response);
    return {
      success: true,
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      passwordChangeRequired: data.password_change_required,
    };
  } catch (error) {
    // eslint-disable-next-line no-console -- Need for debugging MFA issues
    console.error("TOTP verification error:", error);
    return { success: false, error: "Verification failed. Please try again." };
  }
}

/**
 * Send SMS verification code
 */
export async function sendSmsCode(
  email: string,
  password: string,
): Promise<MfaResendResult> {
  if (!AUTH_API_URL) {
    return { success: false, error: "Auth service not configured" };
  }

  try {
    // First authenticate to get a temporary token for SMS sending
    const loginResponse = await fetch(`${AUTH_API_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    // Expect 400 with MFA required
    if (loginResponse.status === 400) {
      const mfaMethods = loginResponse.headers.get("X-MFA-Methods");
      if (mfaMethods?.includes("SMS")) {
        // Send SMS code using the SMS MFA endpoint
        const smsResponse = await fetch(
          `${AUTH_API_URL}/api/sms-mfa/send-code`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
          },
        );

        if (smsResponse.ok) {
          return { success: true };
        }

        const errorData = await parseJsonSafe<ApiErrorResponse>(smsResponse);
        return {
          success: false,
          error: errorData.detail ?? "Failed to send SMS code",
        };
      }
    }

    return { success: false, error: "SMS MFA not available" };
  } catch (error) {
    // eslint-disable-next-line no-console -- Need for debugging MFA issues
    console.error("SMS send error:", error);
    return {
      success: false,
      error: "Failed to send SMS code. Please try again.",
    };
  }
}

/**
 * Verify SMS code and complete login
 */
export async function verifySmsCode(
  email: string,
  password: string,
  code: string,
): Promise<MfaVerifyResult> {
  if (!AUTH_API_URL) {
    return { success: false, error: "Auth service not configured" };
  }

  try {
    const response = await fetch(`${AUTH_API_URL}/api/sms-mfa/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        password,
        code,
      }),
    });

    if (!response.ok) {
      const errorData = await parseJsonSafe<ApiErrorResponse>(response);
      return {
        success: false,
        error: errorData.detail ?? "Invalid verification code",
      };
    }

    const data = await parseJsonSafe<LoginApiResponse>(response);
    return {
      success: true,
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      passwordChangeRequired: data.password_change_required,
    };
  } catch (error) {
    // eslint-disable-next-line no-console -- Need for debugging MFA issues
    console.error("SMS verification error:", error);
    return { success: false, error: "Verification failed. Please try again." };
  }
}

/**
 * Check if MFA is required for a login attempt
 * Returns available MFA methods if required, null if not required
 */
export async function checkMfaRequired(
  email: string,
  password: string,
): Promise<{
  required: boolean;
  methods: string[];
  maskedPhone?: string;
} | null> {
  if (!AUTH_API_URL) {
    return null;
  }

  try {
    const response = await fetch(`${AUTH_API_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (response.status === 400) {
      const mfaMethods = response.headers.get("X-MFA-Methods");
      const mfaType = response.headers.get("X-MFA-Type");
      const maskedPhone =
        response.headers.get("X-MFA-Phone") ??
        response.headers.get("X-Phone-Masked");

      // Multiple MFA methods available
      if (mfaMethods) {
        return {
          required: true,
          methods: mfaMethods.split(",").map((m) => m.trim()),
          maskedPhone: maskedPhone ?? undefined,
        };
      }

      // Single MFA method (TOTP, SMS, or Email)
      if (mfaType && mfaType !== "MULTIPLE") {
        return {
          required: true,
          methods: [mfaType],
          maskedPhone: maskedPhone ?? undefined,
        };
      }
    }

    return { required: false, methods: [] };
  } catch (error) {
    // eslint-disable-next-line no-console -- Need for debugging MFA issues
    console.error("MFA check error:", error);
    return null;
  }
}
