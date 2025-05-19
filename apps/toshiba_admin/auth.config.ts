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

      // Allow access to login and forgot-password pages without a session
      if (
        nextUrl.pathname === "/login" ||
        nextUrl.pathname === "/forgot-password" ||
        nextUrl.pathname === "/api/auth/check-admin-status" ||
        nextUrl.pathname.startsWith("/api/auth")
      ) {
        return (
          isLoggedIn ||
          nextUrl.pathname === "/login" ||
          nextUrl.pathname === "/forgot-password"
        );
      }

      if (isLoggedIn) return true;
      return false; // Redirect unauthenticated users to login page
    },
    // Override the session callback to include the needsPasswordReset property
    async session({ session, token, user }) {
      // Debug logging

      // First call the stock session callback
      const stockSession = await stockConfig.callbacks.session({
        session,
        token,
        user,
        newSession: undefined,
      });

      // Then add our custom properties from the token
      if (!stockSession.user) {
        stockSession.user = {};
      }

      if (token.needsPasswordReset !== undefined) {
        stockSession.user.needsPasswordReset = token.needsPasswordReset;
      }

      if (token.isAdmin !== undefined) {
        stockSession.user.isAdmin = token.isAdmin;
      }

      return stockSession;
    },
    // Override the JWT callback to include the needsPasswordReset property
    async jwt({ token, user, account }) {
      // Debug logging

      // First call the stock JWT callback
      const stockToken = await stockConfig.callbacks.jwt({
        token,
        user,
        account,
      });

      // Then add our custom properties from the user
      if (user.needsPasswordReset !== undefined) {
        stockToken.needsPasswordReset = user.needsPasswordReset;
      }

      if (user.isAdmin !== undefined) {
        stockToken.isAdmin = user.isAdmin;
      }

      return stockToken;
    },
  },
  providers: [], // Add providers with an empty array for now
  trustHost: true,
  secret: process.env.AUTH_SECRET,
  jwt: { maxAge: 60 * 60 },
} satisfies NextAuthConfig;
