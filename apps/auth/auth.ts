import type { NextAuthConfig, User } from "next-auth";
import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import { z } from "zod";
import Google from "next-auth/providers/google";
import { authConfig } from "./auth.config";

const AUTH_API_URL = process.env.AUTH_API_URL;
if (!AUTH_API_URL) throw new Error("AUTH_API_URL does not exist in the env");

interface AuthApiLoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  password_change_required?: boolean;
}

interface AuthApiUserResponse {
  id: number;
  email: string;
  full_name: string | null;
  is_verified: boolean;
  mfa_enabled: boolean;
  status: string;
  is_password_temporary: boolean;
  is_superuser: boolean;
  application_admin: boolean;
}

export async function authApiLogout(refreshToken: string): Promise<void> {
  try {
    const response = await fetch(`${AUTH_API_URL}/api/auth/logout`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${refreshToken}`,
      },
    });
    if (!response.ok) {
      throw new Error("Logout failed");
    }
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
        // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- Might be necessary, straight from the docs
        if (!credentials) return null;

        const parsedCredentials = z
          .object({ email: z.string().email(), password: z.string().min(6) })
          .safeParse(credentials);

        if (!parsedCredentials.success) return null;

        const { email, password } = parsedCredentials.data;

        try {
          // Step 1: Login to Auth API
          const loginResponse = await fetch(`${AUTH_API_URL}/api/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
          });

          if (!loginResponse.ok) return null;

          const loginData: AuthApiLoginResponse = await loginResponse.json();

          // Step 2: Get user details from Auth API
          const userResponse = await fetch(`${AUTH_API_URL}/api/auth/me`, {
            method: "GET",
            headers: {
              Authorization: `Bearer ${loginData.access_token}`,
            },
          });

          if (!userResponse.ok) return null;

          const userData: AuthApiUserResponse = await userResponse.json();

          // Parse full_name into first/last name
          const nameParts = userData.full_name?.split(" ") ?? [];
          const givenName = nameParts[0] ?? "";
          const familyName = nameParts.slice(1).join(" ") ?? "";

          return {
            id: String(userData.id),
            email: userData.email,
            name: userData.full_name ?? userData.email,
            givenName,
            familyName,
            accessToken: loginData.access_token,
            refreshToken: loginData.refresh_token,
            passwordChangeRequired: loginData.password_change_required,
          } satisfies User;
        } catch (error) {
          // eslint-disable-next-line no-console -- Need for debugging auth issues
          console.error("Auth API login error:", error);
          return null;
        }
      },
    }),
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
      authorization: {
        params: {
          prompt: "consent",
          access_type: "offline",
          response_type: "code",
        },
      },
    }),
  ],
};

export const { handlers, auth, signIn, signOut } = NextAuth(authOptions);
