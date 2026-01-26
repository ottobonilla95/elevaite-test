import type { NextAuthConfig, User, Account } from "next-auth";
import { stockConfig } from "@repo/lib";
import type { AdapterUser, Profile } from "next-auth/adapters";
// Commented out unused imports - will be used when registration is re-enabled
// import { IDP, registerToBackend } from "./app/lib/rbacActions";

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
// Environment-specific cookie prefix to prevent staging/prod cookie overlap
const envCookiePrefix = process.env.AUTH_COOKIE_PREFIX
  ? `${process.env.AUTH_COOKIE_PREFIX}.`
  : "";

type LaxType = "lax";

const LAX: LaxType = "lax";

const cookies = {
  sessionToken: {
    name: `${cookiePrefix}${envCookiePrefix}elevaite.session-token`,
    options: {
      httpOnly: true,
      sameSite: LAX,
      path: "/",
      secure: useSecureCookies,
      domain: hostName === "localhost" ? hostName : `.${hostName}`, // add a . in front so that subdomains are included
    },
  },
  pkceCodeVerifier: {
    name: `${cookiePrefix}${envCookiePrefix}elevaite.pkce-code-verifier`,
    options: {
      httpOnly: false,
      sameSite: LAX,
      path: "/",
      secure: useSecureCookies,
      domain: hostName === "localhost" ? hostName : `.${hostName}`,
    },
  },
};

export const authConfig = {
  session: { strategy: "jwt", maxAge: 3600, updateAge: 1800 },
  cookies,
  pages: {
    signIn: "/login",
  },
  callbacks: {
    authorized({ auth, request: { nextUrl } }) {
      const isLoggedIn = Boolean(auth?.user);

      // Allow access to reset-password page for authenticated users
      if (isLoggedIn && nextUrl.pathname === "/reset-password") {
        return true;
      }

      // Redirect authenticated users to homepage
      if (isLoggedIn) {
        return Response.redirect(new URL(ELEVAITE_HOMEPAGE, nextUrl));
      }

      return false; // Redirect unauthenticated users to login page
    },
    // eslint-disable-next-line @typescript-eslint/require-await -- Will be async when the registration is back, needs async signature
    async signIn(params: {
      user: User | AdapterUser;
      account: Account | null;
      profile?: Profile;
    }) {
      // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access -- Profile types vary by provider
      const email = params.profile?.email ?? params.user.email;
      // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-explicit-any -- Custom user properties
      const firstName =
        params.profile?.given_name ?? (params.user as any).givenName;
      // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-explicit-any -- Custom user properties
      const lastName =
        params.profile?.family_name ?? (params.user as any).familyName;
      // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-member-access -- Custom user properties
      const authToken =
        params.account?.access_token ?? (params.user as any).accessToken;
      // console.dir(params);
      if (!email || !firstName || !lastName || !authToken)
        throw new Error("Missing identifier in provider response", {
          // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment -- Error cause for debugging
          cause: { email, firstName, lastName, authToken },
        });

      // Registration functionality commented out
      // To re-enable, uncomment the code below
      /*
      try {
        await registerToBackend({
          // email,
          firstName,
          lastName,
          authToken,
          idp: params.profile ? IDP.GOOGLE : IDP.CREDENTIALS,
        });
      } catch (error) {
        // eslint-disable-next-line no-console -- Temporary
        console.error(error);
        return false;
      }
      */

      // Only allow existing users to sign in
      return true;
    },
    ...stockConfig.callbacks,
  },
  jwt: { maxAge: 60 * 60 },
  providers: [],
  // basePath: "/api/auth",
  trustHost: true,
  // secret: process.env.AUTH_SECRET,
} satisfies NextAuthConfig;
