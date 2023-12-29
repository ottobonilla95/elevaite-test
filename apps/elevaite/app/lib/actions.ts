"use server";
import { AuthError } from "next-auth";
import { redirect } from "next/navigation";

// eslint-disable-next-line @typescript-eslint/require-await -- temp
export async function logOut(): Promise<"Something went wrong." | undefined> {
  try {
    redirect(`${process.env.NEXTAUTH_URL}/api/signout`);
    // await signOut({ redirectTo: "/homepage", redirect: true });
  } catch (error) {
    if (error instanceof AuthError) {
      switch (error.type) {
        default:
          return "Something went wrong.";
      }
    }
    throw error;
  }
}
