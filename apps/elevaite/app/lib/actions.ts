"use server";
import { AuthError } from "next-auth";
import { redirect } from "next/navigation";
import { signOut } from "../../auth";

export async function logOut(): Promise<"Something went wrong." | undefined> {
  try {
    redirect(`${process.env.NEXTAUTH_URL}/signout`);
    await signOut({ redirectTo: "/homepage", redirect: true });
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
