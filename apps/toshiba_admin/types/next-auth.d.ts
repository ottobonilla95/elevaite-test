/* eslint-disable unicorn/filename-case -- The filename is important */

// eslint-disable-next-line @typescript-eslint/no-unused-vars -- This is important
import NextAuth, { DefaultSession } from "next-auth";

declare module "next-auth" {
  interface Session {
    authToken?: string;
    error?: "RefreshAccessTokenError";
    user?: {
      needsPasswordReset?: boolean;
    } & DefaultSession["user"];
  }

  interface User {
    accessToken?: string;
    refreshToken?: string;
    needsPasswordReset?: boolean;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    needsPasswordReset?: boolean;
  }
}
