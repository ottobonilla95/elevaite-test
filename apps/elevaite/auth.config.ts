import type { NextAuthConfig } from "next-auth";
import { stockConfig } from "@repo/lib";

export const authConfig = {
  session: { strategy: "jwt", maxAge: 3600 },
  callbacks: {
    authorized({ auth, request: { nextUrl: _nextUrl } }) {
      // Check if the user is logged in
      const isLoggedIn = Boolean(auth?.user);

      // Check for Alcatel account membership
      if (auth?.user?.accountMemberships) {
        const isAlcatel =
          auth.user.accountMemberships.filter(
            (membership) =>
              membership.account_id === "ab5eed01-46f1-423d-9da0-093814a898fc"
          ).length > 0;
        if (_nextUrl.pathname !== "/" && isAlcatel) return false;
      }

      // Only allow access if the user is logged in
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
