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
  },
  providers: [], // Add providers with an empty array for now
  trustHost: true,
  secret: process.env.AUTH_SECRET,
  jwt: { maxAge: 60 * 60 },
} satisfies NextAuthConfig;
