import type { NextAuthConfig, User } from "next-auth";
import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import { z } from "zod";
import Google from "next-auth/providers/google";
import FusionAuth from "next-auth/providers/fusionauth";
import type { LoginRequest } from "@fusionauth/typescript-client";
import { FusionAuthClient } from "@fusionauth/typescript-client";
import { authConfig } from "./auth.config";

const fusionAuthUrl = process.env.FUSIONAUTH_URL;
if (!fusionAuthUrl) throw new Error("FUSIONAUTH_URL does not exist in the env");

const fusionAppId = process.env.FUSIONAUTH_APPLICATION_ID;
if (!fusionAppId) throw new Error("FUSIONAUTH_APPLICATION_ID does not exist in the env");

const fusionAuthAPIKey = process.env.FUSIONAUTH_API_KEY;
if (!fusionAuthAPIKey) throw new Error("FUSIONAUTH_API_KEY does not exist in the env");

const fusionTentantId = process.env.FUSIONAUTH_TENTANT_ID;
if (!fusionTentantId) throw new Error("FUSIONAUTH_TENTANT_ID does not exist in the env");

const fusionClient = new FusionAuthClient(fusionAuthAPIKey, fusionAuthUrl, fusionTentantId);

export async function fusionLogout(refreshToken: string) {
  try {
    await fusionClient.logout(true, refreshToken);
  } catch (error) {
    throw new Error("Something went wrong");
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
        if (parsedCredentials.success) {
          const { email, password } = parsedCredentials.data;

          const loginRequest: LoginRequest = {
            applicationId: fusionAppId,
            loginId: email,
            password,
          };

          try {
            const res = await fusionClient.login(loginRequest);
            const _user = res.response.user;
            if (!_user?.id) return null;
            return { id: _user.id, email: _user.email, image: _user.imageUrl, name: _user.fullName } satisfies User;
          } catch (error) {
            return null;
          }

          // const user = getUser(email);
          // if (!user) return null;
          // const passwordsMatch = password === user.password;

          // if (passwordsMatch) return user;
        }
        return null;
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
    FusionAuth({
      clientId: process.env.FUSIONAUTH_CLIENT_ID,
      clientSecret: process.env.FUSIONAUTH_CLIENT_SECRET,
      issuer: fusionAuthUrl,
      tenantId: "44c58f43-77f5-264b-a717-e9a8f970f582",
      wellKnown: `${fusionAuthUrl}/.well-known/openid-configuration/${"44c58f43-77f5-264b-a717-e9a8f970f582"}`,
    }),
  ],
};

export const { handlers, auth, signIn, signOut } = NextAuth(authOptions);
