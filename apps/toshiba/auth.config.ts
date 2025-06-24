import type { NextAuthConfig } from "next-auth";
import { stockConfig } from "@repo/lib";

export const authConfig = {
  session: { strategy: "jwt", maxAge: 3600 },
  pages: {
    signIn: "/login",
  },
  callbacks: {
    authorized({ auth, request: { nextUrl } }) {
      // if (process.env.NODE_ENV === "development") return true;
      const isLoggedIn = Boolean(auth?.user);

      // If the user is already logged in and trying to access the login page,
      // redirect them to the home page
      if (isLoggedIn && nextUrl.pathname === "/login") {
        return Response.redirect(new URL("/", nextUrl));
      }

      if (isLoggedIn) return true;
      return false; // Redirect unauthenticated users to login page
    },
    ...stockConfig.callbacks,
    // Override the session callback to include the needsPasswordReset property
    async session({ session, token, user }) {
      session.user ? (session.user.id = token.sub ?? user.id) : null;
      Object.assign(session, { authToken: token.access_token });
      Object.assign(session, { error: token.error });

      // Then add our custom properties from the token
      if (token.needsPasswordReset !== undefined) {
        if (!session.user) {
          session.user = {};
        }
        session.user.needsPasswordReset = token.needsPasswordReset;
      }

      return session;
    },
    // Override the JWT callback to include the needsPasswordReset property
    async jwt({ token, user, account }) {
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
          if (user?.needsPasswordReset !== undefined) {
            token.needsPasswordReset = user.needsPasswordReset;
          }
          return token;
        }

        if (account.provider === "credentials") {
          const newToken = {
            ...token,
            access_token: user.accessToken,
            expires_at: Math.floor(Date.now() / 1000 + 3600),
            refresh_token: user.refreshToken,
            provider: "credentials" as const,
          };

          if (user?.needsPasswordReset !== undefined) {
            newToken.needsPasswordReset = user.needsPasswordReset;
          }

          return newToken;
        }
      }

      if (Date.now() < token.expires_at * 1000) {
        return token;
      }

      try {
        if (token.provider === "credentials") {
          const authApiUrl = process.env.AUTH_API_URL;
          if (!authApiUrl) {
            throw new Error("AUTH_API_URL is not configured");
          }

          const apiUrl = authApiUrl.replace("localhost", "127.0.0.1");
          const tenantId = process.env.AUTH_TENANT_ID ?? "default";

          const response = await fetch(`${apiUrl}/api/auth/refresh`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-Tenant-ID": tenantId,
            },
            body: JSON.stringify({
              refresh_token: token.refresh_token,
            }),
          });

          if (!response.ok) {
            throw new Error(
              `Auth API token refresh failed: ${response.statusText}`
            );
          }

          const tokensOrError = (await response.json()) as {
            access_token: string;
            refresh_token: string;
            token_type: string;
          };

          return {
            ...token,
            access_token: tokensOrError.access_token,
            expires_at: Math.floor(Date.now() / 1000 + 3600),
            refresh_token: tokensOrError.refresh_token,
            provider: "credentials" as const,
          };
        }
        throw new Error("Unknown provider");
      } catch (error) {
        // eslint-disable-next-line no-console -- Need this in case it fails
        console.error("Error refreshing access_token", error);
        token.error = "RefreshAccessTokenError";
        return token;
      }
    },
  },
  providers: [], // Add providers with an empty array for now
  trustHost: true,
  secret: process.env.AUTH_SECRET,
  jwt: { maxAge: 60 * 60 },
} satisfies NextAuthConfig;
