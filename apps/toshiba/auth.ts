import type { NextAuthConfig, User } from "next-auth";
import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import { z } from "zod";
import { authConfig } from "./auth.config";
import { AuthApiClient } from "./app/lib/authApiClient";

const getDomainWithoutSubdomain = (url: string | URL): string => {
  const urlParts = new URL(url).hostname.split(".");

  return urlParts
    .slice(0)
    .slice(-(urlParts.length === 4 ? 3 : 2))
    .join(".");
};

const NEXTAUTH_URL_INTERNAL =
  process.env.NEXTAUTH_URL_INTERNAL || "http://localhost:3005";

const useSecureCookies = NEXTAUTH_URL_INTERNAL.startsWith("https://");
const cookiePrefix = useSecureCookies ? "__Secure-" : "";
const hostName = getDomainWithoutSubdomain(NEXTAUTH_URL_INTERNAL);

type LaxType = "lax";

const LAX: LaxType = "lax";

const cookies = {
  sessionToken: {
    name: `${cookiePrefix}toshiba.session-token`,
    options: {
      httpOnly: true,
      sameSite: LAX,
      path: "/",
      secure: useSecureCookies,
      domain: hostName === "localhost" ? hostName : `.${hostName}`, // add a . in front so that subdomains are included
    },
  },
};

const authApiUrl =
  process.env.NEXT_PUBLIC_AUTH_API_URL ?? "http://127.0.0.1:8004";

const apiUrl = authApiUrl.replace("localhost", "127.0.0.1");

const tenantId = process.env.NEXT_PUBLIC_AUTH_TENANT_ID ?? "default";

// Create an instance of the Auth API client with the tenant ID
const authApiClient = new AuthApiClient(apiUrl, tenantId);

// eslint-disable-next-line @typescript-eslint/require-await -- Temporary
export async function logoutUser(): Promise<void> {
  try {
    // In a real implementation, you would call the logout endpoint
    // This is a placeholder for now
  } catch (error) {
    throw new Error("Something went wrong during logout");
  }
}

export const authOptions: NextAuthConfig = {
  ...authConfig,
  cookies,
  debug: process.env.NODE_ENV !== "production",
  providers: [
    Credentials({
      async authorize(credentials) {
        const parsedCredentials = z
          .object({
            email: z.string().email(),
            password: z.string().min(6),
            totp_code: z.string().optional(),
          })
          .safeParse(credentials);

        if (parsedCredentials.success) {
          const { email, password, totp_code } = parsedCredentials.data;

          try {
            // Call the Auth API to login with optional TOTP code
            const tokenResponse = await authApiClient.login(
              email,
              password,
              totp_code
            );

            // Get user details using the access token
            const userDetails = await authApiClient.getCurrentUser(
              tokenResponse.access_token
            );

            // Check if password change is required
            // This is set by the auth-api when the user has a temporary password
            const needsPasswordReset =
              tokenResponse.password_change_required === true;

            const userObject = {
              id: userDetails.id.toString(),
              email: userDetails.email,
              name: userDetails.full_name ?? email,
              accessToken: tokenResponse.access_token,
              refreshToken: tokenResponse.refresh_token,
              needsPasswordReset,
              is_superuser: userDetails.is_superuser,
              application_admin: userDetails.application_admin,
              mfa_enabled: userDetails.mfa_enabled,
              sms_mfa_enabled: userDetails.sms_mfa_enabled,
              phone_verified: userDetails.phone_verified,
              phone_number: userDetails.phone_number,
              email_mfa_enabled: userDetails.email_mfa_enabled,
              grace_period: tokenResponse.grace_period,
            } satisfies User;

            return userObject;
          } catch (error) {
            if (error instanceof Error) {
              // Check for email verification error
              if (error.message === "email_not_verified") {
                throw new Error("email_not_verified");
              }

              // Check for account locked error
              if (error.message === "account_locked") {
                throw new Error("account_locked");
              }

              // Check for rate limit error
              if (error.message === "rate_limit_exceeded") {
                throw new Error("rate_limit_exceeded");
              }

              // For MFA challenges, throw with a specific format that we can catch
              if (error.message === "MFA_REQUIRED_MULTIPLE") {
                const mfaError = new Error("MFA_REQUIRED_MULTIPLE");
                (mfaError as any).availableMethods = (
                  error as any
                ).availableMethods;
                (mfaError as any).maskedPhone = (error as any).maskedPhone;
                (mfaError as any).maskedEmail = (error as any).maskedEmail;
                throw mfaError;
              }

              if (
                error.message === "MFA_REQUIRED_TOTP" ||
                error.message === "TOTP code required"
              ) {
                throw new Error("MFA_REQUIRED_TOTP");
              }

              if (
                error.message === "MFA_REQUIRED_SMS" ||
                error.message === "SMS code required" ||
                error.message.includes("SMS code required")
              ) {
                const mfaError = new Error("MFA_REQUIRED_SMS");
                (mfaError as any).maskedPhone = (error as any).maskedPhone;
                throw mfaError;
              }

              if (
                error.message === "MFA_REQUIRED_EMAIL" ||
                error.message === "Email code required" ||
                error.message.includes("Email code required")
              ) {
                const mfaError = new Error("MFA_REQUIRED_EMAIL");
                (mfaError as any).maskedEmail = (error as any).maskedEmail;
                throw mfaError;
              }

              // Check for invalid MFA codes
              if (
                error.message === "Invalid MFA code" ||
                error.message === "invalid_totp"
              ) {
                throw new Error("Invalid MFA code");
              }

              // Check for connection issues
              if (
                error.message.includes("ECONNREFUSED") ||
                error.message.includes("timed out")
              ) {
                // eslint-disable-next-line no-console -- Required
                console.error(
                  "Connection to auth API failed. Please ensure the auth API is running and accessible."
                );
              }
            }

            return null;
          }
        }
        return null;
      },
    }),
  ],
};

export const { handlers, auth, signIn, signOut } = NextAuth(authOptions);
