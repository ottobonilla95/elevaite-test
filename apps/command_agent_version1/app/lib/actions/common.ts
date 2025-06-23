"use server";
import { redirect } from "next/navigation";

// eslint-disable-next-line @typescript-eslint/require-await -- Server actions must be async functions
export async function logOut(): Promise<void> {
  redirect(`${process.env.NEXTAUTH_URL_INTERNAL ?? ""}/api/signout`);
}
