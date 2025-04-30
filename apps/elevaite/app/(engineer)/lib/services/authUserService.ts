"use server";

import { revalidatePath } from "next/cache";
import type { ExtendedUserObject } from "../../../lib/interfaces";

interface AuthApiUser {
  id: number;
  email: string;
  full_name?: string;
  is_superuser: boolean;
  status?: string;
}

/**
 * Fetches users from the auth API
 */
export async function fetchAuthUsers(): Promise<ExtendedUserObject[]> {
  try {
    // Use the local auth API
    const backendUrl = "http://localhost:8000";
    const response = await fetch(`${backendUrl}/api/auth/users`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      cache: "no-store",
    });

    if (!response.ok) {
      // console.error("Error fetching users from auth API:", response.status);
      return [];
    }

    const data = (await response.json()) as AuthApiUser[];

    // Transform the auth API user format to match the expected ExtendedUserObject format
    const users: ExtendedUserObject[] = data.map((user) => ({
      id: user.id.toString(),
      email: user.email,
      firstname: user.full_name?.split(" ")[0] ?? "",
      lastname: user.full_name?.split(" ").slice(1).join(" ") ?? "",
      displayRoles: user.is_superuser
        ? [{ roleLabel: "Admin" }]
        : [{ roleLabel: "User" }],
      status: user.status ?? "active",
      organization_id: "default",
      is_superadmin: user.is_superuser,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }));

    return users;
  } catch (error) {
    // console.error("Error fetching auth users:", error);
    return [];
  }
}

/**
 * Combines users from both the RBAC API and the auth API
 */
export async function fetchCombinedUsers(
  rbacUsers: ExtendedUserObject[]
): Promise<ExtendedUserObject[]> {
  try {
    const authUsers = await fetchAuthUsers();

    // Create a map of existing emails to avoid duplicates
    const emailMap = new Map<string, boolean>();
    rbacUsers.forEach((user) => {
      if (user.email) {
        emailMap.set(user.email, true);
      }
    });

    // Filter out auth users that already exist in RBAC users
    const uniqueAuthUsers = authUsers.filter((user) => {
      if (!user.email || emailMap.has(user.email)) {
        return false;
      }
      return true;
    });

    // Combine the two arrays
    return [...rbacUsers, ...uniqueAuthUsers];
  } catch (error) {
    // console.error("Error combining users:", error);
    return rbacUsers;
  }
}

/**
 * Refreshes the users list
 */
// eslint-disable-next-line @typescript-eslint/require-await -- Server-side function
export async function refreshUsersList(): Promise<void> {
  revalidatePath("/access");
}
