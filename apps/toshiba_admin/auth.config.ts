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
    // Override the session callback to include the needsPasswordReset property
    async session({ session, token, user }) {
      // Debug logging
      console.log("Auth Config - Session callback - Token:", token);
      console.log("Auth Config - Session callback - User:", user);

      // First call the stock session callback
      const stockSession = await stockConfig.callbacks.session({
        session,
        token,
        user,
      });

      console.log(
        "Auth Config - Session callback - Stock session:",
        stockSession
      );

      // Then add our custom properties from the token
      if (token.needsPasswordReset !== undefined) {
        if (!stockSession.user) {
          stockSession.user = {};
        }
        stockSession.user.needsPasswordReset = token.needsPasswordReset;
        console.log(
          "Auth Config - Session callback - Added needsPasswordReset:",
          token.needsPasswordReset
        );
      }

      console.log(
        "Auth Config - Session callback - Final session:",
        stockSession
      );

      return stockSession;
    },
    // Override the JWT callback to include the needsPasswordReset property
    async jwt({ token, user, account }) {
      // Debug logging
      console.log("Auth Config - JWT callback - Token:", token);
      console.log("Auth Config - JWT callback - User:", user);
      console.log("Auth Config - JWT callback - Account:", account);

      // First call the stock JWT callback
      const stockToken = await stockConfig.callbacks.jwt({
        token,
        user,
        account,
      });

      console.log("Auth Config - JWT callback - Stock token:", stockToken);

      // Then add our custom properties from the user
      if (user?.needsPasswordReset !== undefined) {
        stockToken.needsPasswordReset = user.needsPasswordReset;
        console.log(
          "Auth Config - JWT callback - Added needsPasswordReset:",
          user.needsPasswordReset
        );
      }

      console.log("Auth Config - JWT callback - Final token:", stockToken);

      return stockToken;
    },
  },
  providers: [], // Add providers with an empty array for now
  trustHost: true,
  secret: process.env.AUTH_SECRET,
  jwt: { maxAge: 60 * 60 },
} satisfies NextAuthConfig;
