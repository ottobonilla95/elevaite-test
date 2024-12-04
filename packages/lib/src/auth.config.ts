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
  if (!GOOGLE_CLIENT_ID)
    throw new Error("GOOGLE_CLIENT_ID does not exist in the env");

  const GOOGLE_CLIENT_SECRET = process.env.GOOGLE_CLIENT_SECRET;
  if (!GOOGLE_CLIENT_SECRET)
    throw new Error("GOOGLE_CLIENT_SECRET does not exist in the env");

  const response = await fetch("https://oauth2.googleapis.com/token", {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      client_id: GOOGLE_CLIENT_ID,
      client_secret: GOOGLE_CLIENT_SECRET,
      grant_type: "refresh_token",
      refresh_token: token.refresh_token ?? token.access_token ?? "",
    }),
    method: "POST",
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

  return {
    ...token,
    access_token: tokensOrError.access_token,
    expires_at: Math.floor(Date.now() / 1000 + tokensOrError.expires_in),
    refresh_token: tokensOrError.refresh_token ?? token.refresh_token,
    provider: "google",
  };
}

async function refreshFusionAuthToken(token: JWT): Promise<JWT> {
  const FUSIONAUTH_ISSUER = process.env.FUSIONAUTH_ISSUER;
  if (!FUSIONAUTH_ISSUER) {
    throw new Error("FUSIONAUTH_ISSUER is not defined in environment");
  }
  const FUSIONAUTH_TOKEN_ENDPOINT = `${FUSIONAUTH_ISSUER}/api/jwt/refresh`;

  const FUSIONAUTH_CLIENT_ID = process.env.FUSIONAUTH_CLIENT_ID;
  if (!FUSIONAUTH_CLIENT_ID) {
    throw new Error("FUSIONAUTH_CLIENT_ID is not defined in environment");
  }

  const FUSIONAUTH_CLIENT_SECRET = process.env.FUSIONAUTH_CLIENT_SECRET;
  if (!FUSIONAUTH_CLIENT_SECRET) {
    throw new Error("FUSIONAUTH_CLIENT_SECRET is not defined in environment");
  }
  const headers = new Headers();
  headers.append("Content-Type", "application/json");

  const response = await fetch(FUSIONAUTH_TOKEN_ENDPOINT, {
    headers,
    body: JSON.stringify({
      refreshToken: token.refresh_token ?? "",
      token: token.access_token
    }),
    method: "POST",
  });

  interface FusionAuthTokenResponse {
    token: string;
    refreshToken: string;
  }

  const tokensOrError = (await response.json()) as FusionAuthTokenResponse;

  // eslint-disable-next-line no-console -- debugging
  console.dir(tokensOrError, { depth: 100 })

  if (!response.ok) {
    throw new TokenRefreshError(
      response.status,
      "fusionauth",
      `FusionAuth token refresh failed: ${response.statusText}`
    );
  }

  return {
    ...token,
    access_token: tokensOrError.token,
    expires_at: Math.floor(Date.now() / 1000 + 360000),
    refresh_token: tokensOrError.refreshToken,
    provider: "credentials",
  };
}

const _config = {
  callbacks: {
    async jwt({ account, token, user }): Promise<JWT> {
      console.log("called jwt")
      if (account) {
        if (!(user.accessToken ?? user.refreshToken) && !(account.access_token ?? account.refresh_token))
          throw new Error("Account doesn't contain tokens");

        if (account.provider === "google") {
          return {
            ...token,
            access_token: account.access_token,
            expires_at: Math.floor(
              Date.now() / 1000 + (account.expires_in ?? 0)
            ),
            refresh_token: account.refresh_token,
            provider: "google",
          };
        }

        if (account.provider === "credentials") {
          return {
            ...token,
            access_token: account.access_token,
            expires_at: Math.floor(
              (Date.now() / 1000) + 3600
            ),
            refresh_token: user.refreshToken,
            provider: "credentials",
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
            return await refreshFusionAuthToken(token);
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
      console.log("called session")
      // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- you never know
      session.user ? (session.user.id = token.sub ?? user.id) : null;
      Object.assign(session, { authToken: token.access_token });
      Object.assign(session, { error: token.error });
      const authToken = token.access_token;
      const RBAC_URL = process.env.RBAC_BACKEND_URL;
      if (!RBAC_URL)
        throw new Error("RBAC_BACKEND_URL does not exist in the env");
      const registerURL = new URL(`${RBAC_URL}/auth/register`);
      const registerHeaders = new Headers();
      registerHeaders.append("Content-Type", "application/json");
      registerHeaders.append(
        "Authorization",
        `Bearer ${authToken ? authToken : ""}`
      );
      const body = JSON.stringify({
        // org_id: ORG_ID,
        firstname: "",
        lastname: "",
        // email,
      });
      const registerRes = await fetch(registerURL, {
        body,
        headers: registerHeaders,
        method: "POST",
      });
      if (!registerRes.ok) {
        // eslint-disable-next-line no-console -- Need this in case this breaks like that.
        console.error(registerRes.statusText);
        throw new Error("Something went wrong.", { cause: registerRes });
      }
      const dbUser: unknown = await registerRes.json();
      if (isDBUser(dbUser)) {
        const url = new URL(`${RBAC_URL}/users/${dbUser.id}/profile`);
        const headers = new Headers();
        headers.append("Content-Type", "application/json");
        headers.append("Authorization", `Bearer ${authToken ? authToken : ""}`);
        const response = await fetch(url, {
          method: "GET",
          headers,
          cache: "no-store",
        });
        if (!response.ok) {
          if (response.status === 422) {
            const errorData: unknown = await response.json();
            // eslint-disable-next-line no-console -- Need this in case this breaks like that.
            console.dir(errorData, { depth: null });
          }
          throw new Error("Failed to fetch projects");
        }
        const fullUser: unknown = await response.json();
        if (isUserObject(fullUser)) {
          Object.assign(session.user, {
            accountMemberships: fullUser.account_memberships,
          });
          Object.assign(session.user, { roles: fullUser.roles });
          Object.assign(session.user, { rbacId: fullUser.id });
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
