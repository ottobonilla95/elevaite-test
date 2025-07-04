/* eslint-disable unicorn/filename-case -- The filename is important */

// eslint-disable-next-line @typescript-eslint/no-unused-vars -- This is important
import NextAuth, { DefaultSession } from "next-auth";

declare module "next-auth" {
  interface Session {
    authToken?: string;
    error?: "RefreshAccessTokenError";
    user?: {
      needsPasswordReset?: boolean;
      is_superuser?: boolean;
      application_admin?: boolean;
      mfa_enabled?: boolean;
      sms_mfa_enabled?: boolean;
      phone_verified?: boolean;
      phone_number?: string;
    } & DefaultSession["user"];
  }

  interface User {
    accessToken?: string;
    refreshToken?: string;
    needsPasswordReset?: boolean;
    is_superuser?: boolean;
    application_admin?: boolean;
    mfa_enabled?: boolean;
    sms_mfa_enabled?: boolean;
    phone_verified?: boolean;
    phone_number?: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    needsPasswordReset?: boolean;
    is_superuser?: boolean;
    application_admin?: boolean;
    mfa_enabled?: boolean;
    sms_mfa_enabled?: boolean;
    phone_verified?: boolean;
    phone_number?: string;
  }
}
