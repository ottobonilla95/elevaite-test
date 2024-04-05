import type { NextAuthConfig } from "next-auth";
import { type TokenSet } from "@auth/core/types";
import { type AuthConfig } from "@auth/core";
import { registerToBackend } from "./app/lib/rbacActions";

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

function getDomainWithoutSubdomain(url: string | URL): string {
  const urlParts = new URL(url).hostname.split(".");

  return urlParts
    .slice(0)
    .slice(-(urlParts.length === 4 ? 3 : 2))
    .join(".");
}

const NEXTAUTH_URL_INTERNAL = process.env.NEXTAUTH_URL_INTERNAL;
const ELEVAITE_HOMEPAGE = process.env.ELEVAITE_HOMEPAGE;
if (!NEXTAUTH_URL_INTERNAL)
  throw new Error("NEXTAUTH_URL_INTERNAL does not exist in the env");
if (!ELEVAITE_HOMEPAGE)
  throw new Error("ELEVAITE_HOMEPAGE does not exist in the env");
const useSecureCookies = NEXTAUTH_URL_INTERNAL.startsWith("https://");
const cookiePrefix = useSecureCookies ? "__Secure-" : "";
const hostName = getDomainWithoutSubdomain(NEXTAUTH_URL_INTERNAL);

type LaxType = "lax";

const LAX: LaxType = "lax";

const cookies = {
  sessionToken: {
    name: `${cookiePrefix}authjs.session-token`,
    options: {
      httpOnly: true,
      sameSite: LAX,
      path: "/",
      secure: useSecureCookies,
      domain: hostName === "localhost" ? hostName : `.${hostName}`, // add a . in front so that subdomains are included
    },
  },
};

const _config = {
  callbacks: {
    async jwt({ account, token }) {
      if (account) {
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
      Object.assign(session, { authToken: token.authToken });
      return session;
    },
    async signIn(params) {
      const email = params.profile?.email ?? params.user.email;
      const firstName = params.profile?.given_name;
      const lastName = params.profile?.family_name;
      const authToken = params.account?.access_token;
      if (!email || !firstName || !lastName || !authToken)
        throw new Error("Missing identifier in provider response", {
          cause: { email, firstName, lastName, authToken },
        });

      try {
        await registerToBackend({
          email,
          firstName,
          lastName,
          authToken,
        });
      } catch (error) {
        // eslint-disable-next-line no-console -- Temporary
        console.error(error);
        return false;
      }
      return true;
    },
  },
  providers: [],
} as AuthConfig;

export const authConfig = {
  session: { strategy: "jwt", maxAge: 3600, updateAge: 1800 },
  cookies,
  pages: {
    signIn: "/login",
  },
  callbacks: {
    authorized({ auth, request: { nextUrl } }) {
      const isLoggedIn = Boolean(auth?.user);
      if (isLoggedIn)
        return Response.redirect(new URL(ELEVAITE_HOMEPAGE, nextUrl));
      return false; // Redirect unauthenticated users to login page
    },
    ..._config.callbacks,
  },
  jwt: { maxAge: 60 * 60 },
  providers: [],
  // basePath: "/api/auth",
  trustHost: true,
  // secret: process.env.AUTH_SECRET,
} satisfies NextAuthConfig;
