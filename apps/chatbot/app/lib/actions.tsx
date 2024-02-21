"use server";
import { redirect } from "next/navigation";

// eslint-disable-next-line @typescript-eslint/require-await -- This is how we need it
export async function logOut(): Promise<void> {
  redirect(`${process.env.NEXTAUTH_URL_INTERNAL}/api/signout`);
}
