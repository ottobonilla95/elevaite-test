import type { NextAuthConfig } from "next-auth";
import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import { z } from "zod";
import Google from "next-auth/providers/google";
import FusionAuth from "next-auth/providers/fusionauth";
import { authConfig } from "./auth.config";

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

export interface User {
  id: string;
  name: string;
  email: string;
  password: string;
}

export const authOptions: NextAuthConfig = {
  ...authConfig,
  cookies,
  // callbacks: {
  //   jwt({ token, user }) {
  //     // we store the user data and access token in the token
  //     if (user) {
  //       console.log(user);

  //       token.userId = user.id;
  //       token.accessToken = user.access_token;
  //       token.refreshToken = user.refresh_token;
  //     }

  //     return token;
  //   },

  //   session({ session, token }) {
  //     session.accessToken = token.accessToken;
  //     const { firstName, lastName, email } = token;
  //     session.user = {
  //       name: `${firstName} ${lastName}`,
  //       email,
  //       id: token.sub,
  //     };
  //     session.refreshToken = token.refreshToken;
  //     return session;
  //   },
  // },
  providers: [
    Credentials({
      // eslint-disable-next-line @typescript-eslint/require-await -- Will be async soon, needs async signature
      async authorize(credentials) {
        // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- Might be necessary, straight from the docs
        if (!credentials) return null;
        const parsedCredentials = z
          .object({ email: z.string().email(), password: z.string().min(6) })
          .safeParse(credentials);
        if (parsedCredentials.success) {
          const { email, password } = parsedCredentials.data;
          const user = getUser(email);
          if (!user) return null;
          const passwordsMatch = password === user.password;

          if (passwordsMatch) return user;
        }
        return null;
      },
    }),
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
      authorization: {
        params: {
          prompt: "consent",
          access_type: "offline",
          response_type: "code",
        },
      },
    }),
    FusionAuth({
      clientId: process.env.FUSIONAUTH_CLIENT_ID,
      clientSecret: process.env.FUSIONAUTH_CLIENT_SECRET,
      issuer: process.env.FUSIONAUTH_ISSUER,
    }),
  ],
};

const users: User[] = [{ email: "johnsmith@gmail.com", id: "1", name: "John Smith", password: "123456" }];

function getUser(email: string): User | null {
  try {
    const user = users.filter((_user) => _user.email === email);
    return user[0] ?? null;
  } catch (error) {
    // eslint-disable-next-line no-console -- TODO: Add a better server side logger
    console.error("Failed to fetch user:", error);
    throw new Error("Failed to fetch user.");
  }
}

export const { handlers, auth, signIn, signOut } = NextAuth(authOptions);
