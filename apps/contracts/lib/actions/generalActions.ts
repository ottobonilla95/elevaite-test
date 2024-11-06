"use server";
import { redirect } from "next/navigation";


// eslint-disable-next-line @typescript-eslint/require-await -- Server actions must be async functions
export async function logOut(): Promise<void> {
  if (!process.env.NEXTAUTH_URL_INTERNAL) throw new Error("Missing base url");
  redirect(`${process.env.NEXTAUTH_URL_INTERNAL}/api/signout`);
}
