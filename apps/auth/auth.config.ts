import type { NextAuthConfig } from "next-auth";
import { stockConfig } from "@repo/lib";
// eslint-disable-next-line @typescript-eslint/no-unused-vars -- Will be used when the registration is back
import { IDP, registerToBackend } from "./app/lib/rbacActions";

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
  pkceCodeVerifier: {
    name: `${cookiePrefix}authjs.pkce-code-verifier`,
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
      if (isLoggedIn)
        return Response.redirect(new URL(ELEVAITE_HOMEPAGE, nextUrl));
      return false; // Redirect unauthenticated users to login page
    },
    // eslint-disable-next-line @typescript-eslint/require-await -- Will be async when the registration is back, needs async signature
    async signIn(params) {
      const email = params.profile?.email ?? params.user.email;
      const firstName = params.profile?.given_name ?? params.user.givenName;
      const lastName = params.profile?.family_name ?? params.user.familyName;
      const authToken = params.account?.access_token ?? params.user.accessToken;
      // console.dir(params);
      if (!email || !firstName || !lastName || !authToken)
        throw new Error("Missing identifier in provider response", {
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
