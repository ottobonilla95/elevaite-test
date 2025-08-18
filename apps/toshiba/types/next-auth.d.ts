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
      email_mfa_enabled?: boolean;
      grace_period?: {
        in_grace_period: boolean;
        days_remaining: number;
        grace_period_days: number;
        expires_at?: string;
        auto_enable_at?: string;
        auto_enable_method: string;
        error?: string;
      };
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
    email_mfa_enabled?: boolean;
    grace_period?: {
      in_grace_period: boolean;
      days_remaining: number;
      grace_period_days: number;
      expires_at?: string;
      auto_enable_at?: string;
      auto_enable_method: string;
      error?: string;
    };
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    access_token: string | undefined;
    expires_at: number;
    refresh_token: string | undefined;
    provider: "google" | "credentials";
    error?: "RefreshAccessTokenError";
    needsPasswordReset?: boolean;
    is_superuser?: boolean;
    application_admin?: boolean;
    mfa_enabled?: boolean;
    sms_mfa_enabled?: boolean;
    phone_verified?: boolean;
    phone_number?: string;
    email_mfa_enabled?: boolean;
    grace_period?: {
      in_grace_period: boolean;
      days_remaining: number;
      grace_period_days: number;
      expires_at?: string;
      auto_enable_at?: string;
      auto_enable_method: string;
      error?: string;
    };
  }
}
