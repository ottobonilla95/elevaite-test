import type { NextAuthConfig } from "next-auth";

function getDomainWithoutSubdomain(url: string | URL): string {
  const urlParts = new URL(url).hostname.split(".");

  return urlParts
    .slice(0)
    .slice(-(urlParts.length === 4 ? 3 : 2))
    .join(".");
}

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
export const authConfig = {
  cookies,
  pages: {
    signIn: "/login",
  },
  callbacks: {
    authorized({ auth, request: { nextUrl } }) {
      const isLoggedIn = Boolean(auth?.user);
      const isOnDashboard = nextUrl.pathname.startsWith("/homepage");
      if (isOnDashboard) {
        if (isLoggedIn) return true;
        return false; // Redirect unauthenticated users to login page
      } else if (isLoggedIn) {
        return Response.redirect(new URL("/homepage", nextUrl));
      }
      return true;
    },
  },
  providers: [],
} satisfies NextAuthConfig;
