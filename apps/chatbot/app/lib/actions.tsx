"use server";
import { redirect } from "next/navigation";


export async function logOut(): Promise<void> {
    redirect(`${process.env.NEXTAUTH_URL}/api/signout`);
}