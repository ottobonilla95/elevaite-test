import type { NextAuthConfig, User } from "next-auth";
import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import { z } from "zod";
import { authConfig } from "./auth.config";
import { AuthApiClient } from "./app/lib/authApiClient";

const authApiUrl = process.env.AUTH_API_URL;
if (!authApiUrl) throw new Error("AUTH_API_URL does not exist in the env");

const tenantId = process.env.AUTH_TENANT_ID ?? 'default';

// Create an instance of the Auth API client with the tenant ID
const authApiClient = new AuthApiClient(authApiUrl, tenantId);

// eslint-disable-next-line @typescript-eslint/require-await -- Temporary
export async function logoutUser(refreshToken: string): Promise<void> {
  try {
    // In a real implementation, you would call the logout endpoint
    // This is a placeholder for now
    console.log("Logging out with refresh token:", refreshToken);
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
        if (!credentials) return null;

        const parsedCredentials = z
          .object({ email: z.string().email(), password: z.string().min(6) })
          .safeParse(credentials);

        if (parsedCredentials.success) {
          const { email, password } = parsedCredentials.data;

          try {
            // Call the Auth API to login
            const tokenResponse = await authApiClient.login(email, password);
            console.log("Token response:", tokenResponse);

            // Get user details using the access token
            const userDetails = await authApiClient.getCurrentUser(tokenResponse.access_token);

            return {
              id: userDetails.id.toString(),
              email: userDetails.email,
              name: userDetails.full_name ?? email,
              accessToken: tokenResponse.access_token,
              refreshToken: tokenResponse.refresh_token,
            } satisfies User;
          } catch (error) {
            console.error("Authentication error:", error);
            return null;
          }
        }
        return null;
      },
    }),
  ],
};

export const { handlers, auth, signIn, signOut } = NextAuth(authOptions);
