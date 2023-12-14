import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import { z } from "zod";
import { authConfig } from "./auth.config";

export type User = {
  id: string;
  name: string;
  email: string;
  password: string;
};

const users: User[] = [{ email: "johnsmith@gmail.com", id: "1", name: "John Smith", password: "123456" }];

function getUser(email: string): User | null {
  try {
    const user = users.filter((user) => user.email === email);
    return user[0] ?? null;
  } catch (error) {
    console.error("Failed to fetch user:", error);
    throw new Error("Failed to fetch user.");
  }
}

export const { auth, signIn, signOut } = NextAuth({
  ...authConfig,
  providers: [
    Credentials({
      async authorize(credentials) {
        if (!credentials) return null;
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
