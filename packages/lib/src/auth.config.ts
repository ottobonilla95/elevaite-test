import type { DefaultSession, NextAuthConfig } from "next-auth";
// eslint-disable-next-line @typescript-eslint/consistent-type-imports -- Needed as variable
import { JWT } from "next-auth/jwt";

class TokenRefreshError extends Error {
  constructor(
    public statusCode: number,
    public providerName: string,
    message: string
  ) {
    super(message);
    this.name = "TokenRefreshError";
  }
}

// RBAC types
export interface RoleAssignment {
  user_id: number;
  role_id: string;
  resource_id: string;
  resource_type: "organization" | "account" | "project";
  created_at: string;
  role_name?: string;
}

export interface GroupMembership {
  user_id: number;
  group_id: string;
  resource_id: string;
  resource_type: string;
  created_at: string;
  group?: {
    id: string;
    name: string;
    description?: string;
  };
}

export interface PermissionOverride {
  user_id: number;
  resource_id: string;
  resource_type: string;
  allow_actions: string[];
  deny_actions: string[];
}

export interface UserRbac {
  user_id: number;
  is_superuser: boolean;
  role_assignments: RoleAssignment[];
  group_memberships: GroupMembership[];
  permission_overrides: PermissionOverride[];
}

declare module "next-auth/jwt" {
  interface JWT {
    access_token: string | undefined;
    expires_at: number;
    refresh_token: string | undefined;
    provider: "google" | "credentials";
    error?: "RefreshAccessTokenError";
    rbac?: UserRbac | null;
    rbac_fetched_at?: number;
  }
}

declare module "next-auth" {
  interface Session {
    error?: "RefreshAccessTokenError";
    user?: {
      accountMemberships?: UserAccountMembershipObject[];
      rbacId?: string;
      rbac?: UserRbac;
    } & DefaultSession["user"];
  }

  interface User {
    accessToken?: string;
    refreshToken?: string;
    givenName?: string;
    familyName?: string;
  }
}

async function refreshGoogleToken(token: JWT): Promise<JWT> {
  const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID;
  const GOOGLE_CLIENT_SECRET = process.env.GOOGLE_CLIENT_SECRET;

  if (!GOOGLE_CLIENT_ID || !GOOGLE_CLIENT_SECRET) {
    throw new Error("Google client credentials are not configured properly.");
  }

  if (!token.refresh_token) {
    throw new Error(
      "Missing refresh token. Cannot refresh Google access token."
    );
  }

  const response = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    body: new URLSearchParams({
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion, @typescript-eslint/no-unnecessary-type-assertion -- Straight from the docs https://authjs.dev/guides/refresh-token-rotation?framework=next-js
      client_id: GOOGLE_CLIENT_ID!,
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion, @typescript-eslint/no-unnecessary-type-assertion -- Straight from the docs https://authjs.dev/guides/refresh-token-rotation?framework=next-js
      client_secret: GOOGLE_CLIENT_SECRET!,
      grant_type: "refresh_token",
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion, @typescript-eslint/no-unnecessary-type-assertion -- Straight from the docs https://authjs.dev/guides/refresh-token-rotation?framework=next-js
      refresh_token: token.refresh_token!,
    }),
  });

  interface GoogleTokenResponse {
    access_token: string;
    expires_in: number;
    refresh_token?: string;
    error?: string;
    error_description?: string;
  }

  const tokensOrError = (await response.json()) as GoogleTokenResponse;

  if (!response.ok) {
    throw new TokenRefreshError(
      response.status,
      "google",
      `Google token refresh failed: ${tokensOrError.error_description ?? "Unknown error"}`
    );
  }

  if (!tokensOrError.access_token) {
    throw new Error("Google response is missing an access token.");
  }

  return {
    ...token,
    access_token: tokensOrError.access_token,
    expires_at: Math.floor(Date.now() / 1000 + tokensOrError.expires_in),
    refresh_token: tokensOrError.refresh_token ?? token.refresh_token,
    provider: "google" as const,
  };
}

async function refreshAuthApiToken(token: JWT): Promise<JWT> {
  const AUTH_API_URL = process.env.NEXT_PUBLIC_AUTH_API_URL;
  if (!AUTH_API_URL) {
    throw new Error("NEXT_PUBLIC_AUTH_API_URL is not defined in environment");
  }
  const apiUrl = AUTH_API_URL.replace("localhost", "127.0.0.1");
  const AUTH_API_REFRESH_ENDPOINT = `${apiUrl}/api/auth/refresh`;

  // Get tenant ID from environment or use default
  const TENANT_ID = process.env.AUTH_TENANT_ID ?? "default";

  if (!token.refresh_token) {
    throw new Error("Missing refresh token. Cannot refresh access token.");
  }

  const headers = new Headers();
  headers.append("Content-Type", "application/json");
  headers.append("X-Tenant-ID", TENANT_ID);

  const response = await fetch(AUTH_API_REFRESH_ENDPOINT, {
    headers,
    body: JSON.stringify({
      refresh_token: token.refresh_token,
    }),
    method: "POST",
  });

  interface AuthApiTokenResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
    password_change_required?: boolean;
  }

  const tokensOrError = (await response.json()) as AuthApiTokenResponse;

  if (!response.ok) {
    throw new TokenRefreshError(
      response.status,
      "auth_api",
      `Auth API token refresh failed: ${response.statusText}`
    );
  }

  const refreshedToken = {
    ...token,
    access_token: tokensOrError.access_token,
    // Default token expiration to 1 hour (3600 seconds)
    expires_at: Math.floor(Date.now() / 1000 + 3600),
    refresh_token: tokensOrError.refresh_token,
    provider: "credentials" as const,
  } as JWT & { needsPasswordReset?: boolean };

  // Preserve or update the needsPasswordReset flag from refresh response
  if (tokensOrError.password_change_required !== undefined) {
    refreshedToken.needsPasswordReset = tokensOrError.password_change_required;
  }

  return refreshedToken;
}

// RBAC cache duration in seconds (5 minutes)
const RBAC_CACHE_DURATION = 5 * 60;

async function fetchUserRbac(accessToken: string): Promise<UserRbac | null> {
  const AUTH_API_URL = process.env.NEXT_PUBLIC_AUTH_API_URL;
  if (!AUTH_API_URL) {
    // RBAC fetching is optional - if no auth API URL, skip silently
    return null;
  }

  const apiUrl = AUTH_API_URL.replace("localhost", "127.0.0.1");
  const TENANT_ID = process.env.AUTH_TENANT_ID ?? "default";

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      controller.abort();
    }, 5000);

    const response = await fetch(`${apiUrl}/api/rbac/me`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
        "X-Tenant-ID": TENANT_ID,
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      // Don't throw on RBAC fetch failure - it's non-critical
      // eslint-disable-next-line no-console -- Need this for debugging
      console.warn("Failed to fetch RBAC:", response.status);
      return null;
    }

    return (await response.json()) as UserRbac;
  } catch (error) {
    // eslint-disable-next-line no-console -- Need this for debugging
    console.warn("Error fetching RBAC:", error);
    return null;
  }
}

const _config = {
  callbacks: {
    async jwt({ account, token, user }): Promise<JWT> {
      if (account) {
        if (
          !account.access_token &&
          !account.refresh_token &&
          !user.accessToken &&
          !user.refreshToken
        ) {
          throw new Error("Account doesn't contain tokens");
        }
        if (
          Boolean(account.access_token) &&
          (account.access_token === token.access_token ||
            user.accessToken === token.access_token) &&
          Boolean(account.refresh_token) &&
          (account.refresh_token === token.refresh_token ||
            user.refreshToken === token.refresh_token) &&
          Boolean(account.provider) &&
          account.provider === token.provider
        ) {
          return token;
        }

        if (account.provider === "google") {
          return {
            ...token,
            access_token: account.access_token,
            expires_at: Math.floor(
              Date.now() / 1000 + (account.expires_in ?? 0)
            ),
            refresh_token: account.refresh_token,
            provider: "google" as const,
          };
        }

        if (account.provider === "credentials") {
          return {
            ...token,
            access_token: user.accessToken,
            expires_at: Math.floor(Date.now() / 1000 + 3600),
            refresh_token: user.refreshToken,
            provider: "credentials" as const,
          };
        }
      }

      if (Date.now() < token.expires_at * 1000) {
        return token;
      }

      try {
        switch (token.provider) {
          case "google":
            return await refreshGoogleToken(token);
          case "credentials":
            return await refreshAuthApiToken(token);
          default:
            throw new Error("Unknown provider");
        }
      } catch (error) {
        // eslint-disable-next-line no-console -- Need this in case it fails
        console.error("Error refreshing access_token", error);
        // If we fail to refresh the token, return an error so we can handle it on the page
        token.error = "RefreshAccessTokenError";
        return token;
      }
    },
    async session({ session, token, user }) {
      // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- you never know
      session.user ? (session.user.id = token.sub ?? user.id) : null;
      Object.assign(session, { authToken: token.access_token });
      Object.assign(session, { error: token.error });

      // Fetch RBAC if we have an access token and cache is stale
      if (token.access_token) {
        const now = Math.floor(Date.now() / 1000);
        const rbacStale =
          !token.rbac_fetched_at ||
          now - token.rbac_fetched_at > RBAC_CACHE_DURATION;

        if (rbacStale) {
          const rbac = await fetchUserRbac(token.access_token);
          if (rbac) {
            token.rbac = rbac;
            token.rbac_fetched_at = now;
          }
        }

        // Always add RBAC to session if available
        if (token.rbac) {
          session.user.rbac = token.rbac;
          session.user.rbacId = String(token.rbac.user_id);
        }
      }

      return session;
    },
  },
  providers: [],
} satisfies NextAuthConfig;

export const stockConfig: NextAuthConfig = _config;
export interface DBUser {
  id: string;
  organization_id: string;
  firstname: string;
  lastname: string;
  email: string;
  is_superadmin: boolean;
  created_at: string;
  updated_at: string;
}

interface UserAccountMembershipObject {
  account_id: string;
  account_name: string;
  is_admin: boolean;
  roles: { id: string; name: string }[];
}
