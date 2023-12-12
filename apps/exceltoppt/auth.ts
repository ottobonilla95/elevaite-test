import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import * as yup from "yup";
import { authConfig } from "./auth.config";

export const { auth, signIn, signOut } = NextAuth({
  ...authConfig,
  providers: [
    Credentials({
      async authorize(credentials) {
        const parsedCredentials = yup
          .object()
          .shape({ email: yup.string().email(), password: yup.string().min(6) })
          .validate(credentials);
      },
    }),
  ],
});
