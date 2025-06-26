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

declare module "next-auth/jwt" {
  interface JWT {
    access_token: string | undefined;
    expires_at: number;
    refresh_token: string | undefined;
    provider: "google" | "credentials";
    error?: "RefreshAccessTokenError";
  }
}

declare module "next-auth" {
  interface Session {
    error?: "RefreshAccessTokenError";
    user?: {
      accountMemberships?: UserAccountMembershipObject[];
      rbacId?: string;
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
  const AUTH_API_REFRESH_ENDPOINT = `${AUTH_API_URL}/api/auth/refresh`;

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
  }

  const tokensOrError = (await response.json()) as AuthApiTokenResponse;

  if (!response.ok) {
    throw new TokenRefreshError(
      response.status,
      "auth_api",
      `Auth API token refresh failed: ${response.statusText}`
    );
  }

  return {
    ...token,
    access_token: tokensOrError.access_token,
    // Default token expiration to 1 hour (3600 seconds)
    expires_at: Math.floor(Date.now() / 1000 + 3600),
    refresh_token: tokensOrError.refresh_token,
    provider: "credentials" as const,
  };
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
    // eslint-disable-next-line @typescript-eslint/require-await -- temp
    async session({ session, token, user }) {
      // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- you never know
      session.user ? (session.user.id = token.sub ?? user.id) : null;
      Object.assign(session, { authToken: token.access_token });
      Object.assign(session, { error: token.error });
      // const authToken = token.access_token;
      // const RBAC_URL = process.env.RBAC_BACKEND_URL;
      // if (!RBAC_URL)
      //   throw new Error("RBAC_BACKEND_URL does not exist in the env");
      // const registerURL = new URL(`${RBAC_URL}/auth/register`);
      // const registerHeaders = new Headers();
      // registerHeaders.append("Content-Type", "application/json");
      // if (!authToken) throw Error("authToken doesn't exist");
      // registerHeaders.append("Authorization", `Bearer ${authToken}`);
      // const body = JSON.stringify({
      //   // org_id: ORG_ID,
      //   firstname: "",
      //   lastname: "",
      //   // email,
      // });
      // const registerRes = await fetch(registerURL, {
      //   body,
      //   headers: registerHeaders,
      //   method: "POST",
      // });
      // if (!registerRes.ok) {
      //   // eslint-disable-next-line no-console -- Need this in case this breaks like that.
      //   console.error(registerRes.statusText);
      //   throw new Error("Something went wrong.", { cause: registerRes });
      // }
      // const dbUser: unknown = await registerRes.json();
      // if (isDBUser(dbUser)) {
      //   const url = new URL(`${RBAC_URL}/users/${dbUser.id}/profile`);
      //   const headers = new Headers();
      //   headers.append("Content-Type", "application/json");
      //   headers.append("Authorization", `Bearer ${authToken ? authToken : ""}`);
      //   const response = await fetch(url, {
      //     method: "GET",
      //     headers,
      //     cache: "no-store",
      //   });
      //   if (!response.ok) {
      //     if (response.status === 422) {
      //       const errorData: unknown = await response.json();
      //       // eslint-disable-next-line no-console -- Need this in case this breaks like that.
      //       console.dir(errorData, { depth: null });
      //     }
      //     throw new Error("Failed to fetch projects");
      //   }
      //   const fullUser: unknown = await response.json();
      //   if (isUserObject(fullUser)) {
      //     Object.assign(session.user, {
      //       accountMemberships: fullUser.account_memberships,
      //     });
      //     Object.assign(session.user, { roles: fullUser.roles });
      //     Object.assign(session.user, { rbacId: fullUser.id });
      //   }
      // }
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

function isObject(item: unknown): item is object {
  return Boolean(item) && item !== null && typeof item === "object";
}

function isDBUser(obj: unknown): obj is DBUser {
  return isObject(obj) && "is_superadmin" in obj && "organization_id" in obj;
}

function isUserObject(item: unknown): item is UserObject {
  return (
    isObject(item) &&
    "id" in item &&
    "organization_id" in item &&
    "firstname" in item &&
    "lastname" in item &&
    "email" in item &&
    "is_superadmin" in item &&
    "created_at" in item &&
    "updated_at" in item
  );
}

interface UserObject {
  id: string;
  organization_id: string;
  firstname?: string;
  lastname?: string;
  email?: string;
  is_superadmin: boolean;
  created_at: string;
  updated_at: string;
  is_account_admin?: boolean;
  roles?: UserRoleObject[];
  account_memberships?: UserAccountMembershipObject[];
}
interface UserRoleObject {
  id: string;
  name: string;
}
interface UserAccountMembershipObject {
  account_id: string;
  account_name: string;
  is_admin: boolean;
  roles: UserRoleObject[];
}
