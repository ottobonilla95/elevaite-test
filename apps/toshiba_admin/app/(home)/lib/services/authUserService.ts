"use server";

import { revalidatePath } from "next/cache";
import { cookies } from "next/headers";
import { auth } from "../../../../auth";
import type { ExtendedUserObject } from "../../../lib/interfaces";

interface AuthApiUser {
  id: number;
  email: string;
  full_name?: string;
  is_superuser: boolean;
  status?: string;
}

interface ErrorResponse {
  detail?: string;
  message?: string;
  error?: string;
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

/**
 * Checks if the current user is an admin
 */
export async function isCurrentUserAdmin(): Promise<boolean> {
  try {
    // In development mode, always return true for testing
    if (process.env.NODE_ENV === "development") {
      return true;
    }

    // Get the auth token from the session
    const session = await auth();
    const authToken = session?.authToken;

    if (!authToken) {
      return false;
    }

    // Use environment variable for backend URL with fallback
    const backendUrl = process.env.NEXT_PUBLIC_AUTH_API_URL;

    // Call the API to check if the user is an admin
    const response = await fetch(`${backendUrl}/api/auth/me`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
    });

    if (!response.ok) {
      return false;
    }

    const userData = (await response.json()) as { is_superuser?: boolean };

    // Check if the user is a superuser/admin
    return userData.is_superuser === true;
  } catch (error) {
    // If there's an error, assume the user is not an admin for security
    return false;
  }
}

interface ResetPasswordParams {
  userId: string;
  email: string;
  password: string;
  isOneTimePassword: boolean;
}

/**
 * Resets a user's password
 */
export async function resetUserPassword(
  params: ResetPasswordParams
): Promise<{ success: boolean; message: string }> {
  try {
    const { email, password, isOneTimePassword } = params;

    // Get the auth token from the session
    // This is a server component, so we can use auth() to get the current session
    const sessionCookie =
      cookies().get("__Secure-authjs.session-token") ??
      cookies().get("authjs.session-token");

    if (!sessionCookie) {
      return {
        success: false,
        message: "Authentication session not found. Please log in again.",
      };
    }

    // Get the token from the session
    const session = await auth();
    const authToken = session?.authToken;

    if (!authToken) {
      return {
        success: false,
        message: "Authentication token not found. Please log in again.",
      };
    }

    // Use environment variable for backend URL with fallback
    const backendUrl =
      process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

    // Call the admin password reset endpoint with admin token
    const response = await fetch(
      `${backendUrl}/api/auth/admin/reset-password`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          email,
          new_password: password,
          is_one_time_password: isOneTimePassword,
        }),
      }
    );

    if (!response.ok) {
      const statusCode = response.status.toString();
      let errorMessage = `API Error (${statusCode})`;

      try {
        const errorData = (await response.json()) as ErrorResponse;
        errorMessage =
          errorData.detail ??
          errorData.message ??
          errorData.error ??
          "Failed to reset password. Please try again.";
      } catch {
        if (response.status === 404) {
          errorMessage =
            "API endpoint not found. Please check the server is running.";
        }
      }

      return {
        success: false,
        message: errorMessage,
      };
    }

    // Password reset successfully
    return {
      success: true,
      message:
        "Password reset successfully. The user will receive an email with the new password.",
    };
  } catch (error: unknown) {
    // Log error but don't expose details to client
    return {
      success: false,
      message: "An unexpected error occurred. Please try again later.",
    };
  }
}
