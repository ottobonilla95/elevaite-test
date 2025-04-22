"use server";
import { redirect } from "next/navigation";

// eslint-disable-next-line @typescript-eslint/require-await -- Server actions must be async functions
export async function logOut(): Promise<void> {
  // In development mode, just redirect to the home page
  if (process.env.NODE_ENV === "development") {
    redirect("/");
    return;
  }

  // In production, redirect to the auth app's signout endpoint
  if (!process.env.NEXTAUTH_URL_INTERNAL) throw new Error("Missing base url");
  redirect(`${process.env.NEXTAUTH_URL_INTERNAL}/api/signout`);
}
