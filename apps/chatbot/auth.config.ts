import type { NextAuthConfig } from "next-auth";

export const authConfig = {
  callbacks: {
    authorized({ auth, request: { nextUrl: _nextUrl } }) {
      // if (process.env.NODE_ENV === "development") return true;
      const isLoggedIn = Boolean(auth?.user);
      if (isLoggedIn) return true;
      return false; // Redirect unauthenticated users to login page
    },
    // eslint-disable-next-line @typescript-eslint/require-await -- has to be async according to documentation
    async session({ session, token, user }) {
      session.user ? (session.user.id = token.sub || user.id) : null;
      return session;
    },
  },
  providers: [], // Add providers with an empty array for now
  trustHost: true,
  secret: process.env.AUTH_SECRET,
} satisfies NextAuthConfig;
