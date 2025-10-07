import type { NextAuthConfig } from "next-auth";
import type { DefaultSession } from "next-auth";
import { stockConfig } from "@repo/lib";

export const authConfig = {
  session: {
    strategy: "jwt",
  },
  pages: {
    signIn: "/login",
  },
  // Suppress NextAuth debug logs during normal MFA flow
  debug: false,
  logger: {
    error: (error) => {
      // Only log actual errors, not expected MFA flow errors
      const errorMessage = error.message || String(error);
      if (
        (!errorMessage.includes("MFA_REQUIRED") &&
          !errorMessage.includes("CallbackRouteError")) ||
        process.env.NODE_ENV === "production"
      ) {
        console.error(`[auth][error]`, error);
      }
    },
    warn: (code) => {
      if (process.env.NODE_ENV === "production") {
        console.warn(`[auth][warn] ${code}`);
      }
    },
    debug: () => {
      // Suppress debug logs in development to reduce console clutter
    },
  },
  callbacks: {
    ...stockConfig.callbacks,
    async session({ session, token, user }) {
      const stockSession = stockConfig.callbacks?.session
        ? await stockConfig.callbacks.session({
          session,
          token,
          user,
          newSession: undefined,
        })
        : session;

      if (!stockSession.user) {
        stockSession.user = {} as DefaultSession["user"] & {
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
          refreshToken?: string;
        };
      }

      Object.assign(stockSession, { authToken: token.access_token });

      if (
        token.needsPasswordReset !== undefined &&
        token.needsPasswordReset !== null &&
        typeof token.needsPasswordReset === "boolean"
      ) {
        stockSession.user.needsPasswordReset = token.needsPasswordReset;
      }

      if (
        token.is_superuser !== undefined &&
        token.is_superuser !== null &&
        typeof token.is_superuser === "boolean"
      ) {
        stockSession.user.is_superuser = token.is_superuser;
      }

      if (
        token.application_admin !== undefined &&
        token.application_admin !== null &&
        typeof token.application_admin === "boolean"
      ) {
        stockSession.user.application_admin = token.application_admin;
      }

      if (
        token.is_manager !== undefined &&
        token.is_manager !== null &&
        typeof token.is_manager === "boolean"
      ) {
        stockSession.user.is_manager = token.is_manager;
      }

      if (
        token.mfa_enabled !== undefined &&
        token.mfa_enabled !== null &&
        typeof token.mfa_enabled === "boolean"
      ) {
        stockSession.user.mfa_enabled = token.mfa_enabled;
      }

      if (
        token.sms_mfa_enabled !== undefined &&
        token.sms_mfa_enabled !== null &&
        typeof token.sms_mfa_enabled === "boolean"
      ) {
        stockSession.user.sms_mfa_enabled = token.sms_mfa_enabled;
      }

      if (
        token.phone_verified !== undefined &&
        token.phone_verified !== null &&
        typeof token.phone_verified === "boolean"
      ) {
        stockSession.user.phone_verified = token.phone_verified;
      }

      if (
        token.phone_number !== undefined &&
        token.phone_number !== null &&
        typeof token.phone_number === "string"
      ) {
        stockSession.user.phone_number = token.phone_number;
      }

      if (
        token.email_mfa_enabled !== undefined &&
        token.email_mfa_enabled !== null &&
        typeof token.email_mfa_enabled === "boolean"
      ) {
        stockSession.user.email_mfa_enabled = token.email_mfa_enabled;
      }

      if (
        token.grace_period !== undefined &&
        token.grace_period !== null &&
        typeof token.grace_period === "object" &&
        "in_grace_period" in token.grace_period &&
        "days_remaining" in token.grace_period &&
        "grace_period_days" in token.grace_period &&
        "auto_enable_method" in token.grace_period
      ) {
        stockSession.user.grace_period = token.grace_period as {
          in_grace_period: boolean;
          days_remaining: number;
          grace_period_days: number;
          expires_at?: string;
          auto_enable_at?: string;
          auto_enable_method: string;
          error?: string;
        };
      }

      if (token.refresh_token) {
        stockSession.user.refreshToken = token.refresh_token;
      }

      return stockSession;
    },
    // Override the JWT callback to include the needsPasswordReset property
    async jwt({ token, user, account }) {
      if (account) {
        if (
          !account.access_token &&
          !account.refresh_token &&
          !user.accessToken &&
          !user.refreshToken
        ) {
          throw new Error("Account doesn't contain tokens");
        }
        if (
          Boolean(account.access_token) &&
          (account.access_token === token.access_token ||
            user.accessToken === token.access_token) &&
          Boolean(account.refresh_token) &&
          (account.refresh_token === token.refresh_token ||
            user.refreshToken === token.refresh_token) &&
          Boolean(account.provider) &&
          account.provider === token.provider
        ) {
          if (
            user?.needsPasswordReset !== undefined &&
            typeof user.needsPasswordReset === "boolean"
          ) {
            token.needsPasswordReset = user.needsPasswordReset;
          }
          if (
            user?.is_superuser !== undefined &&
            typeof user.is_superuser === "boolean"
          ) {
            token.is_superuser = user.is_superuser;
          }
          if (
            user?.application_admin !== undefined &&
            typeof user.application_admin === "boolean"
          ) {
            token.application_admin = user.application_admin;
          }
          if (
            user?.is_manager !== undefined &&
            typeof user.is_manager === "boolean"
          ) {
            token.is_manager = user.is_manager;
          }
          if (
            user?.mfa_enabled !== undefined &&
            typeof user.mfa_enabled === "boolean"
          ) {
            token.mfa_enabled = user.mfa_enabled;
          }
          if (
            user?.sms_mfa_enabled !== undefined &&
            typeof user.sms_mfa_enabled === "boolean"
          ) {
            token.sms_mfa_enabled = user.sms_mfa_enabled;
          }
          if (
            user?.phone_verified !== undefined &&
            typeof user.phone_verified === "boolean"
          ) {
            token.phone_verified = user.phone_verified;
          }
          if (
            user?.phone_number !== undefined &&
            typeof user.phone_number === "string"
          ) {
            token.phone_number = user.phone_number;
          }
          if (
            user?.email_mfa_enabled !== undefined &&
            typeof user.email_mfa_enabled === "boolean"
          ) {
            token.email_mfa_enabled = user.email_mfa_enabled;
          }
          if (user?.grace_period !== undefined) {
            token.grace_period = user.grace_period;
          }
          return token;
        }

        if (account.provider === "credentials") {
          const newToken: typeof token = {
            access_token: user.accessToken,
            expires_at: Math.floor(Date.now() / 1000 + 3600),
            refresh_token: user.refreshToken,
            provider: "credentials" as const,
            sub: user.id,
            email: user.email,
            name: user.name,
          };

          if (
            user?.needsPasswordReset !== undefined &&
            typeof user.needsPasswordReset === "boolean"
          ) {
            newToken.needsPasswordReset = user.needsPasswordReset;
          } else {
            newToken.needsPasswordReset = null;
          }
          if (
            user?.is_superuser !== undefined &&
            typeof user.is_superuser === "boolean"
          ) {
            newToken.is_superuser = user.is_superuser;
          } else {
            newToken.is_superuser = null;
          }
          if (
            user?.application_admin !== undefined &&
            typeof user.application_admin === "boolean"
          ) {
            newToken.application_admin = user.application_admin;
          } else {
            newToken.application_admin = null;
          }
          if (
            user?.is_manager !== undefined &&
            typeof user.is_manager === "boolean"
          ) {
            newToken.is_manager = user.is_manager;
          } else {
            newToken.is_manager = null;
          }
          if (
            user?.mfa_enabled !== undefined &&
            typeof user.mfa_enabled === "boolean"
          ) {
            newToken.mfa_enabled = user.mfa_enabled;
          } else {
            newToken.mfa_enabled = null;
          }
          if (
            user?.sms_mfa_enabled !== undefined &&
            typeof user.sms_mfa_enabled === "boolean"
          ) {
            newToken.sms_mfa_enabled = user.sms_mfa_enabled;
          } else {
            newToken.sms_mfa_enabled = null;
          }
          if (
            user?.phone_verified !== undefined &&
            typeof user.phone_verified === "boolean"
          ) {
            newToken.phone_verified = user.phone_verified;
          } else {
            newToken.phone_verified = null;
          }
          // For phone_number, set null explicitly if absent to avoid leaking
          newToken.phone_number =
            typeof user?.phone_number === "string" ? user.phone_number : null;

          if (
            user?.email_mfa_enabled !== undefined &&
            typeof user.email_mfa_enabled === "boolean"
          ) {
            newToken.email_mfa_enabled = user.email_mfa_enabled;
          } else {
            newToken.email_mfa_enabled = null;
          }
          if (user?.grace_period !== undefined) {
            newToken.grace_period = user.grace_period;
          } else {
            newToken.grace_period = null;
          }

          return newToken;
        }
      }

      if (Date.now() < token.expires_at * 1000) {
        return token;
      }

      try {
        if (token.provider === "credentials") {
          const authApiUrl = process.env.NEXT_PUBLIC_AUTH_API_URL;
          if (!authApiUrl) {
            throw new Error("NEXT_PUBLIC_AUTH_API_URL is not configured");
          }

          const apiUrl = authApiUrl.replace("localhost", "127.0.0.1");
          const tenantId = process.env.NEXT_PUBLIC_AUTH_TENANT_ID ?? "default";

          const response = await fetch(`${apiUrl}/api/auth/refresh`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-Tenant-ID": tenantId,
            },
            body: JSON.stringify({
              refresh_token: token.refresh_token,
            }),
          });

          if (!response.ok) {
            throw new Error(
              `Auth API token refresh failed: ${response.statusText}`
            );
          }

          const tokensOrError = (await response.json()) as {
            access_token: string;
            refresh_token: string;
            token_type: string;
            password_change_required?: boolean;
          };

          const refreshedToken: typeof token = {
            ...token,
            access_token: tokensOrError.access_token,
            expires_at: Math.floor(Date.now() / 1000 + 3600), // Default 1 hour, backend will enforce actual limits
            refresh_token: tokensOrError.refresh_token,
            provider: "credentials" as const,
          };

          // Preserve or update the needsPasswordReset flag from refresh response
          if (
            tokensOrError.password_change_required !== undefined &&
            typeof tokensOrError.password_change_required === "boolean"
          ) {
            refreshedToken.needsPasswordReset =
              tokensOrError.password_change_required;
          }

          return refreshedToken;
        }
        throw new Error("Unknown provider");
      } catch (error) {
        // eslint-disable-next-line no-console -- Need this in case it fails
        console.error("Error refreshing access_token", error);
        token.error = "RefreshAccessTokenError";
        return token;
      }
    },
  },
  providers: [], // Add providers with an empty array for now
  trustHost: true,
  secret: process.env.AUTH_SECRET,
  jwt: {},
} satisfies NextAuthConfig;
