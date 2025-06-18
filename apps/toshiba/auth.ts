import type { NextAuthConfig, User } from "next-auth";
import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import { z } from "zod";
import { authConfig } from "./auth.config";
import { AuthApiClient } from "./app/lib/authApiClient";

// Try both environment variable names
const authApiUrl =
  process.env.AUTH_API_URL ?? process.env.NEXT_PUBLIC_AUTH_API_URL;
if (!authApiUrl) {
  throw new Error("AUTH_API_URL does not exist in the env");
}

const tenantId = process.env.AUTH_TENANT_ID ?? "default";

// Create an instance of the Auth API client with the tenant ID
const authApiClient = new AuthApiClient(authApiUrl, tenantId);

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
  debug: process.env.NODE_ENV !== "production",
  providers: [
    Credentials({
      async authorize(credentials) {
        const parsedCredentials = z
          .object({ email: z.string().email(), password: z.string().min(6) })
          .safeParse(credentials);

        if (parsedCredentials.success) {
          const { email, password } = parsedCredentials.data;

          try {
            // Call the Auth API to login
            const tokenResponse = await authApiClient.login(email, password);

            // Get user details using the access token
            const userDetails = await authApiClient.getCurrentUser(
              tokenResponse.access_token
            );

            // Check if password change is required
            // This is set by the auth-api when the user has a temporary password
            const needsPasswordReset =
              tokenResponse.password_change_required === true;

            const user = {
              id: userDetails.id.toString(),
              email: userDetails.email,
              name: userDetails.full_name ?? email,
              accessToken: tokenResponse.access_token,
              refreshToken: tokenResponse.refresh_token,
              needsPasswordReset,
            } satisfies User;

            return user;
          } catch (error) {
            // Provide more detailed error message for specific errors
            if (error instanceof Error) {
              // Check for email verification error
              if (error.message === "email_not_verified") {
                throw new Error("email_not_verified");
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
