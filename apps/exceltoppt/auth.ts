import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import { z } from "zod";
import { authConfig } from "./auth.config";

export interface User {
  id: string;
  name: string;
  email: string;
  password: string;
}

const users: User[] = [{ email: "johnsmith@gmail.com", id: "1", name: "John Smith", password: "123456" }];

function getUser(email: string): User | null {
  try {
    const user = users.filter((_user) => _user.email === email);
    return user[0] ?? null;
  } catch (error) {
    // eslint-disable-next-line no-console -- TODO: Add a better server side logger
    console.error("Failed to fetch user:", error);
    throw new Error("Failed to fetch user.");
  }
}

export const { auth, signIn, signOut } = NextAuth({
  ...authConfig,
  providers: [
    Credentials({
      // eslint-disable-next-line @typescript-eslint/require-await -- Will be async soon, needs async signature
      async authorize(credentials) {
        // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- Might be necessary, straight from the docs
        if (credentials) return null;
        const parsedCredentials = z
          .object({ email: z.string().email(), password: z.string().min(6) })
          .safeParse(credentials);
        if (parsedCredentials.success) {
          const { email, password } = parsedCredentials.data;
          const user = getUser(email);
          if (!user) return null;
          const passwordsMatch = password === user.password;

          if (passwordsMatch) return user;
        }
        return null;
      },
    }),
  ],
});
