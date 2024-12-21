import type { NextAuthConfig } from "next-auth";
import { stockConfig } from "@repo/lib";

export const authConfig = {
  session: { strategy: "jwt", maxAge: 5*3600 },
  callbacks: {
    authorized({ auth, request: { nextUrl: _nextUrl } }) {
      // if (process.env.NODE_ENV === "development") return true;
      const isLoggedIn = Boolean(auth?.user);
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
