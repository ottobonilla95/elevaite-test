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

const NEXTAUTH_URL = process.env.NEXTAUTH_URL;
if (!NEXTAUTH_URL) throw new Error("NEXTAUTH_URL does not exist in the env");

const useSecureCookies = NEXTAUTH_URL.startsWith("https://");
const cookiePrefix = useSecureCookies ? "__Secure-" : "";
const hostName = getDomainWithoutSubdomain(NEXTAUTH_URL);

const cookies = {
  sessionToken: {
    name: `${cookiePrefix}authjs.session-token`,
    options: {
      httpOnly: true,
      sameSite: "lax",
      path: "/",
      secure: useSecureCookies,
      domain: hostName === "localhost" ? hostName : `.${hostName}`, // add a . in front so that subdomains are included
    },
  },
};

export const { auth, signIn, signOut } = NextAuth({
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
