import type { TokenSet } from "@auth/core/types";
import type { AuthConfig } from "@auth/core";
// import type { NextAuthConfig } from "next-auth";

declare module "@auth/core/types" {
  interface Session {
    error?: "RefreshAccessTokenError";
  }
}

declare module "@auth/core/jwt" {
  interface JWT {
    access_token: string;
    expires_at: number;
    refresh_token: string;
    error?: "RefreshAccessTokenError";
  }
}

const _config = {
  callbacks: {
    async jwt({ account, token }) {
      if (account) {
        if (!account.access_token || !account.refresh_token)
          throw new Error("Account doesn't contain tokens");
        // Save the access token and refresh token in the JWT on the initial login
        const _res = {
          ...token,
          access_token: account.access_token,
          expires_at: Math.floor(Date.now() / 1000 + (account.expires_in ?? 0)),
          refresh_token: account.refresh_token,
        };
        return _res;
      } else if (Date.now() < token.expires_at * 1000) {
        // If the access token has not expired yet, return it
        return token;
      }
      // If the access token has expired, try to refresh it
      try {
        // https://accounts.google.com/.well-known/openid-configuration
        // We need the `token_endpoint`.

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
            refresh_token: token.refresh_token,
          }),
          method: "POST",
        });

        const tokens: TokenSet = (await response.json()) as TokenSet;

        if (!response.ok)
          throw new Error("Refresh response failed", { cause: tokens });

        if (!tokens.access_token)
          throw new Error("Refresh response didn't contain access_token", {
            cause: tokens,
          });

        return {
          ...token, // Keep the previous token properties
          access_token: tokens.access_token,
          expires_at: Math.floor(Date.now() / 1000 + (tokens.expires_in ?? 0)),
          // Fall back to old refresh token, but note that
          // many providers may only allow using a refresh token once.
          refresh_token: tokens.refresh_token ?? token.refresh_token,
        };
      } catch (error) {
        // eslint-disable-next-line no-console -- we want this one
        console.error("Error refreshing access token", error);
        // The error property will be used client-side to handle the refresh token error
        return { ...token, error: "RefreshAccessTokenError" as const };
      }
    },
    // eslint-disable-next-line @typescript-eslint/require-await -- has to be async according to documentation
    async session({ session, token, user }) {
      // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- you never know
      session.user ? (session.user.id = token.sub ?? user.id) : null;
      Object.assign(session, { authToken: token.access_token });
      Object.assign(session, { error: token.error });
      return session;
    },
  },
  providers: [],
} satisfies AuthConfig;

export const stockConfig: AuthConfig = _config;
