import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import { authConfig } from "./auth.config";

const getDomainWithoutSubdomain = (url: string | URL) => {
  const urlParts = new URL(url).hostname.split(".");

  return urlParts
    .slice(0)
    .slice(-(urlParts.length === 4 ? 3 : 2))
    .join(".");
};

const NEXTAUTH_URL_INTERNAL = process.env.NEXTAUTH_URL_INTERNAL;
if (!NEXTAUTH_URL_INTERNAL) {
  throw new Error("NEXTAUTH_URL_INTERNAL does not exist in the env");
}

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
};

export const { handlers, auth, signIn, signOut } = NextAuth({
  ...authConfig,
  cookies,
  useSecureCookies,
  providers: [
    Credentials({
      // eslint-disable-next-line @typescript-eslint/require-await -- Will be async soon, needs async signature
      async authorize() {
        return null;
      },
    }),
  ],
});
