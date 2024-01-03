"use server";
import { redirect } from "next/navigation";

// eslint-disable-next-line @typescript-eslint/require-await -- server actions must be async
export async function logOut(): Promise<void> {
  redirect(`${process.env.NEXTAUTH_URL}/api/signout`);
}
