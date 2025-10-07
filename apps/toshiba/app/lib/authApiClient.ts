export interface LoginRequest {
  email: string;
  password: string;
  totp_code?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  password_change_required?: boolean;
  grace_period?: {
    in_grace_period: boolean;
    days_remaining: number;
    grace_period_days: number;
    expires_at?: string;
    auto_enable_at?: string;
    auto_enable_method: string;
    error?: string;
  };
}

export interface UserResponse {
  id: number;
  email: string;
  full_name: string | null;
  is_verified: boolean;
  mfa_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserDetailResponse extends UserResponse {
  status: string;
  last_login: string | null;
  is_superuser: boolean;
  application_admin: boolean;
  is_password_temporary: boolean;
  sms_mfa_enabled?: boolean;
  phone_verified?: boolean;
  phone_number?: string;
  email_mfa_enabled?: boolean;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

// MFA-related interfaces
export interface MfaSetupResponse {
  secret: string;
  qr_code_uri: string;
}

export interface MfaVerifyRequest {
  totp_code: string;
}

export interface SMSMFASetupRequest {
  phone_number: string;
}

export interface SMSMFAVerifyRequest {
  mfa_code: string;
}

export interface SMSMFAResponse {
  message: string;
  message_id?: string;
}

export interface EmailMFASetupRequest {
  // No additional fields needed as email is from user account
}

export interface EmailMFAVerifyRequest {
  mfa_code: string;
}

export interface EmailMFAResponse {
  message: string;
  email?: string;
}

/**
 * Auth API client
 */
export class AuthApiClient {
  private baseUrl: string;
  private tenantId: string;

  constructor(baseUrl: string, tenantId = "default") {
    // Use IPv4 explicitly to avoid IPv6 connection issues
    this.baseUrl = baseUrl.replace("localhost", "127.0.0.1");
    this.tenantId = tenantId;
  }

  /**
   * Set the tenant ID for all requests
   */
  setTenantId(tenantId: string): void {
    this.tenantId = tenantId;
  }

  /**
   * Get the default headers for all requests
   */
  private getHeaders(
    additionalHeaders: Record<string, string> = {}
  ): Record<string, string> {
    return {
      "Content-Type": "application/json",
      "X-Tenant-ID": this.tenantId,
      ...additionalHeaders,
    };
  }

  /**
   * Login with email and password, optionally with TOTP code
   */
  async login(
    email: string,
    password: string,
    totpCode?: string
  ): Promise<TokenResponse> {
    // Create AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      controller.abort();
    }, 5000); // 5 second timeout

    try {
      const loginData: LoginRequest = { email, password };
      if (totpCode) {
        loginData.totp_code = totpCode;
      }

      const response = await fetch(`${this.baseUrl}/api/auth/login`, {
        method: "POST",
        headers: this.getHeaders(),
        body: JSON.stringify(loginData),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = (await response.json()) as { detail?: string };

        // Only log unexpected errors to avoid cluttering console during normal auth flow
        if (
          response.status !== 400 ||
          !errorData.detail?.includes("code required")
        ) {
          // Don't log expected auth errors (403 email_not_verified, 423 account_locked, 429 rate_limit)
          if (
            !(
              response.status === 403 &&
              errorData.detail === "email_not_verified"
            ) &&
            !(
              response.status === 423 && errorData.detail === "account_locked"
            ) &&
            !(response.status === 429) // Rate limit errors
          ) {
            console.log(
              "AuthApiClient error response:",
              response.status,
              errorData
            );
          }
        }

        if (
          response.status === 403 &&
          errorData.detail === "email_not_verified"
        ) {
          throw new Error("email_not_verified");
        }

        if (response.status === 423 && errorData.detail === "account_locked") {
          throw new Error("account_locked");
        }

        if (response.status === 429) {
          throw new Error("rate_limit_exceeded");
        }

        if (
          response.status === 400 &&
          errorData.detail?.includes("MFA code required")
        ) {
          const mfaType = response.headers.get("X-MFA-Type");
          const mfaMethods = response.headers.get("X-MFA-Methods");
          const maskedPhone = response.headers.get("X-Phone-Masked");
          const maskedEmail = response.headers.get("X-Email-Masked");

          if (mfaType === "MULTIPLE" && mfaMethods) {
            const methods = mfaMethods.split(",");
            const error = new Error("MFA_REQUIRED_MULTIPLE");
            (error as any).availableMethods = methods;
            (error as any).maskedPhone = maskedPhone;
            (error as any).maskedEmail = maskedEmail;
            throw error;
          }
          // Single method cases
          else if (
            mfaType === "TOTP" ||
            errorData.detail === "TOTP code required"
          ) {
            throw new Error("MFA_REQUIRED_TOTP");
          } else if (
            mfaType === "SMS" ||
            errorData.detail?.includes("SMS code required")
          ) {
            const error = new Error("MFA_REQUIRED_SMS");
            (error as any).maskedPhone = maskedPhone;
            throw error;
          } else if (
            mfaType === "EMAIL" ||
            errorData.detail?.includes("Email code required")
          ) {
            const error = new Error("MFA_REQUIRED_EMAIL");
            (error as any).maskedEmail = maskedEmail;
            throw error;
          }
        }

        if (
          response.status === 400 &&
          errorData.detail === "TOTP code required"
        ) {
          throw new Error("MFA_REQUIRED_TOTP");
        }

        if (
          response.status === 400 &&
          (errorData.detail === "SMS code required" ||
            errorData.detail?.includes("SMS code required"))
        ) {
          throw new Error("MFA_REQUIRED_SMS");
        }

        if (
          response.status === 400 &&
          errorData.detail === "Invalid TOTP code"
        ) {
          throw new Error("invalid_totp");
        }

        if (
          response.status === 400 &&
          errorData.detail === "Invalid MFA code"
        ) {
          throw new Error("Invalid MFA code");
        }

        throw new Error(errorData.detail ?? "Login failed");
      }

      return response.json() as Promise<TokenResponse>;
    } catch (error) {
      clearTimeout(timeoutId);

      // Check if the request was aborted due to timeout
      if (error instanceof Error && error.name === "AbortError") {
        throw new Error(
          `Request timed out. Could not connect to auth API at ${this.baseUrl}`
        );
      }

      // Re-throw the original error
      throw error;
    }
  }

  /**
   * Get current user information
   */
  async getCurrentUser(accessToken: string): Promise<UserDetailResponse> {
    // Create AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      controller.abort();
    }, 5000); // 5 second timeout

    try {
      const response = await fetch(`${this.baseUrl}/api/auth/me`, {
        method: "GET",
        headers: this.getHeaders({
          Authorization: `Bearer ${accessToken}`,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = (await response.json()) as { detail?: string };
        throw new Error(errorData.detail ?? "Failed to get user information");
      }

      return response.json() as Promise<UserDetailResponse>;
    } catch (error) {
      clearTimeout(timeoutId);

      // Check if the request was aborted due to timeout
      if (error instanceof Error && error.name === "AbortError") {
        throw new Error(
          `Request timed out. Could not connect to auth API at ${this.baseUrl}`
        );
      }

      // Re-throw the original error
      throw error;
    }
  }

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken: string): Promise<TokenResponse> {
    const response = await fetch(`${this.baseUrl}/api/auth/refresh`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      throw new Error(errorData.detail ?? "Failed to refresh token");
    }

    return response.json() as Promise<TokenResponse>;
  }

  /**
   * Register a new user
   */
  async register(
    email: string,
    password: string,
    fullName?: string
  ): Promise<UserResponse> {
    const response = await fetch(`${this.baseUrl}/api/auth/register`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify({
        email,
        password,
        full_name: fullName,
      }),
    });

    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      throw new Error(errorData.detail ?? "Registration failed");
    }

    return response.json() as Promise<UserResponse>;
  }

  // MFA-related methods

  /**
   * Set up TOTP MFA for the current user
   */
  async setupMFA(accessToken: string): Promise<MfaSetupResponse> {
    const response = await fetch(`${this.baseUrl}/api/auth/mfa/setup`, {
      method: "POST",
      headers: this.getHeaders({
        Authorization: `Bearer ${accessToken}`,
      }),
    });

    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      throw new Error(errorData.detail ?? "MFA setup failed");
    }

    return response.json() as Promise<MfaSetupResponse>;
  }

  /**
   * Activate TOTP MFA after verification
   */
  async activateMFA(
    accessToken: string,
    totpCode: string
  ): Promise<{ message: string }> {
    const response = await fetch(`${this.baseUrl}/api/auth/mfa/activate`, {
      method: "POST",
      headers: this.getHeaders({
        Authorization: `Bearer ${accessToken}`,
      }),
      body: JSON.stringify({ totp_code: totpCode }),
    });

    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      throw new Error(errorData.detail ?? "MFA activation failed");
    }

    return response.json() as Promise<{ message: string }>;
  }

  /**
   * Set up SMS MFA for the current user
   */
  async setupSMSMFA(
    accessToken: string,
    phoneNumber: string
  ): Promise<SMSMFAResponse> {
    const response = await fetch(`${this.baseUrl}/api/sms-mfa/setup`, {
      method: "POST",
      headers: this.getHeaders({
        Authorization: `Bearer ${accessToken}`,
      }),
      body: JSON.stringify({ phone_number: phoneNumber }),
    });

    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      throw new Error(errorData.detail ?? "SMS MFA setup failed");
    }

    return response.json() as Promise<SMSMFAResponse>;
  }

  /**
   * Send SMS MFA code to the user's phone
   */
  async sendSMSMFACode(accessToken: string): Promise<SMSMFAResponse> {
    const response = await fetch(`${this.baseUrl}/api/sms-mfa/send-code`, {
      method: "POST",
      headers: this.getHeaders({
        Authorization: `Bearer ${accessToken}`,
      }),
    });

    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      throw new Error(errorData.detail ?? "Failed to send SMS MFA code");
    }

    return response.json() as Promise<SMSMFAResponse>;
  }

  /**
   * Verify SMS MFA code
   */
  async verifySMSMFA(
    accessToken: string,
    mfaCode: string
  ): Promise<SMSMFAResponse> {
    const response = await fetch(`${this.baseUrl}/api/sms-mfa/verify`, {
      method: "POST",
      headers: this.getHeaders({
        Authorization: `Bearer ${accessToken}`,
      }),
      body: JSON.stringify({ mfa_code: mfaCode }),
    });

    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      throw new Error(errorData.detail ?? "SMS MFA verification failed");
    }

    return response.json() as Promise<SMSMFAResponse>;
  }

  /**
   * Resend SMS MFA code during login flow
   */
  async resendSMSCodeForLogin(
    email: string,
    password: string
  ): Promise<{ message: string }> {
    const response = await fetch(`${this.baseUrl}/api/auth/resend-sms-code`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      throw new Error(errorData.detail ?? "Failed to resend SMS code");
    }

    return response.json() as Promise<{ message: string }>;
  }

  // Email MFA methods

  /**
   * Set up Email MFA for the current user
   */
  async setupEmailMFA(accessToken: string): Promise<EmailMFAResponse> {
    const response = await fetch(`${this.baseUrl}/api/email-mfa/setup`, {
      method: "POST",
      headers: this.getHeaders({
        Authorization: `Bearer ${accessToken}`,
      }),
      body: JSON.stringify({}),
    });

    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      throw new Error(errorData.detail ?? "Email MFA setup failed");
    }

    return response.json() as Promise<EmailMFAResponse>;
  }

  /**
   * Send Email MFA code to the user's email
   */
  async sendEmailMFACode(accessToken: string): Promise<EmailMFAResponse> {
    const response = await fetch(`${this.baseUrl}/api/email-mfa/send-code`, {
      method: "POST",
      headers: this.getHeaders({
        Authorization: `Bearer ${accessToken}`,
      }),
    });

    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      throw new Error(errorData.detail ?? "Failed to send Email MFA code");
    }

    return response.json() as Promise<EmailMFAResponse>;
  }

  /**
   * Verify Email MFA code
   */
  async verifyEmailMFA(
    accessToken: string,
    mfaCode: string
  ): Promise<EmailMFAResponse> {
    const response = await fetch(`${this.baseUrl}/api/email-mfa/verify`, {
      method: "POST",
      headers: this.getHeaders({
        Authorization: `Bearer ${accessToken}`,
      }),
      body: JSON.stringify({ mfa_code: mfaCode }),
    });

    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      throw new Error(errorData.detail ?? "Email MFA verification failed");
    }

    return response.json() as Promise<EmailMFAResponse>;
  }

  /**
   * Get Email MFA status for the current user
   */
  async getEmailMFAStatus(accessToken: string): Promise<EmailMFAResponse> {
    const response = await fetch(`${this.baseUrl}/api/email-mfa/status`, {
      method: "GET",
      headers: this.getHeaders({
        Authorization: `Bearer ${accessToken}`,
      }),
    });

    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      throw new Error(errorData.detail ?? "Failed to get Email MFA status");
    }

    return response.json() as Promise<EmailMFAResponse>;
  }

  /**
   * Disable Email MFA for the current user
   */
  async disableEmailMFA(accessToken: string): Promise<EmailMFAResponse> {
    const response = await fetch(`${this.baseUrl}/api/email-mfa/disable`, {
      method: "POST",
      headers: this.getHeaders({
        Authorization: `Bearer ${accessToken}`,
      }),
    });

    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      throw new Error(errorData.detail ?? "Failed to disable Email MFA");
    }

    return response.json() as Promise<EmailMFAResponse>;
  }
}
