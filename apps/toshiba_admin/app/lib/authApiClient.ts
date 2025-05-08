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

  constructor(baseUrl: string, tenantId: string = "default") {
    this.baseUrl = baseUrl;
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
    const response = await fetch(`${this.baseUrl}/api/auth/login`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Login failed");
    }

    return response.json();
  }

  /**
   * Get current user information
   */
  async getCurrentUser(accessToken: string): Promise<UserDetailResponse> {
    const response = await fetch(`${this.baseUrl}/api/auth/me`, {
      method: "GET",
      headers: this.getHeaders({
        Authorization: `Bearer ${accessToken}`,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to get user information");
    }

    return response.json();
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
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to refresh token");
    }

    return response.json();
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
      const errorData = await response.json();
      throw new Error(errorData.detail || "Registration failed");
    }

    return response.json();
  }
}
