/**
 * Client for the Auth API
 */

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
}

export interface RefreshTokenRequest {
  refresh_token: string;
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
   * Login with email and password
   */
  async login(email: string, password: string): Promise<TokenResponse> {
    // Create AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      controller.abort();
    }, 5000); // 5 second timeout

    try {
      const response = await fetch(`${this.baseUrl}/api/auth/login`, {
        method: "POST",
        headers: this.getHeaders(),
        body: JSON.stringify({ email, password }),
        signal: controller.signal,
      });

      // Clear the timeout
      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = (await response.json()) as { detail?: string };
        throw new Error(errorData.detail ?? "Login failed");
      }

      return (await response.json()) as TokenResponse;
    } catch (error) {
      // Clear the timeout
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

      // Clear the timeout
      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = (await response.json()) as { detail?: string };
        throw new Error(errorData.detail ?? "Failed to get user information");
      }

      return (await response.json()) as UserDetailResponse;
    } catch (error) {
      // Clear the timeout
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

    return (await response.json()) as TokenResponse;
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

    return (await response.json()) as UserResponse;
  }
}
