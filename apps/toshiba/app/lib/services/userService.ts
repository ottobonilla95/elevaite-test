"use server";

import { revalidatePath } from "next/cache";
import { auth } from "../../../auth";
import { isCurrentUserAdmin } from "./authUserService";

interface CreateUserParams {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  isOneTimePassword: boolean;
}

interface ApiErrorResponse {
  detail?: string;
  message?: string;
  error?: string;
}

interface AuthSession {
  authToken?: string;
  [key: string]: unknown;
}

/**
 * Creates a new user by combining first and last name into full_name
 * and sending a request to the auth API
 *
 * This function requires admin privileges
 */
export async function createUser(
  params: CreateUserParams
): Promise<{ success: boolean; message: string }> {
  try {
    const { firstName, lastName, email, password, isOneTimePassword } = params;

    const fullName = `${firstName} ${lastName}`.trim();

    const isAdmin = await isCurrentUserAdmin();

    if (!isAdmin && process.env.NODE_ENV !== "development") {
      return {
        success: false,
        message:
          "You don't have permission to create users. Admin privileges required.",
      };
    }

    const session = await auth();

    const authToken = session
      ? (session as unknown as AuthSession).authToken
      : undefined;

    if (!authToken && process.env.NODE_ENV !== "development") {
      return {
        success: false,
        message: "Authentication token not found. Please log in again.",
      };
    }

    const backendUrl =
      process.env.AUTH_API_URL ?? process.env.NEXT_PUBLIC_AUTH_API_URL;

    if (!backendUrl) {
      return {
        success: false,
        message: "Server configuration error. Please contact an administrator.",
      };
    }

    // Add tenant ID header for multi-tenancy
    const tenantId = process.env.AUTH_TENANT_ID ?? "default";

    // Use the admin endpoint with authentication
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      "X-Tenant-ID": tenantId,
    };

    // Add authorization header if token exists
    if (authToken) {
      headers.Authorization = `Bearer ${authToken}`;
    }

    // Use the admin endpoint with authentication
    const response = await fetch(`${backendUrl}/api/auth/admin/create-user`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        email,
        full_name: fullName,
        password,
        is_one_time_password: isOneTimePassword,
      }),
    });

    if (!response.ok) {
      const statusCode = response.status.toString();
      let errorMessage = `API Error (${statusCode})`;

      try {
        const errorData = (await response.json()) as ApiErrorResponse;

        errorMessage =
          errorData.detail ??
          errorData.message ??
          errorData.error ??
          "Failed to create user. Please try again.";
      } catch (parseError) {
        if (response.status === 404) {
          errorMessage =
            "API endpoint not found. Please check the server is running.";
        } else if (response.status === 401) {
          errorMessage = "Unauthorized. Please log in again.";
        } else if (response.status === 403) {
          errorMessage =
            "Forbidden. You don't have permission to create users.";
        }
      }

      return {
        success: false,
        message: errorMessage,
      };
    }

    // User created successfully, now send a password reset email

    const resetHeaders: Record<string, string> = {
      "Content-Type": "application/json",
      "X-Tenant-ID": tenantId,
    };

    // Add authorization header if token exists for the reset request
    if (authToken) {
      resetHeaders.Authorization = `Bearer ${authToken}`;
    }

    const resetResponse = await fetch(
      `${backendUrl}/api/auth/forgot-password`,
      {
        method: "POST",
        headers: resetHeaders,
        body: JSON.stringify({ email }),
      }
    );

    if (!resetResponse.ok) {
      return {
        success: true,
        message:
          "User created successfully, but there was an issue sending the invitation email. " +
          "In a production environment, the user would receive an email with login instructions.",
      };
    }

    // Revalidate the users list
    revalidatePath("/access");

    return {
      success: true,
      message: "User created successfully and invitation email sent.",
    };
  } catch (error) {
    // Provide more detailed error message if possible
    let errorMessage = "An unexpected error occurred. Please try again later.";

    if (error instanceof Error) {
      if (error.message.includes("fetch")) {
        errorMessage =
          "Network error. Please check your connection and try again.";
      } else if (error.message.includes("timeout")) {
        errorMessage =
          "Request timed out. The server may be busy or unavailable.";
      }
    }

    return {
      success: false,
      message: errorMessage,
    };
  }
}

/**
 * Generates a secure random password that meets the requirements
 */
// eslint-disable-next-line @typescript-eslint/require-await -- Server functions must be async
export async function generateSecurePassword(): Promise<string> {
  "use server";

  const length = 16;
  const lowercase = "abcdefghijklmnopqrstuvwxyz";
  const uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  const numbers = "0123456789";
  const special = '!@#$%^&*(),.?":{}|<>';

  const allChars = lowercase + uppercase + numbers + special;

  // Ensure at least one of each character type
  let password =
    lowercase.charAt(Math.floor(Math.random() * lowercase.length)) +
    uppercase.charAt(Math.floor(Math.random() * uppercase.length)) +
    numbers.charAt(Math.floor(Math.random() * numbers.length)) +
    special.charAt(Math.floor(Math.random() * special.length));

  // Fill the rest with random characters
  for (let i = 4; i < length; i++) {
    password += allChars.charAt(Math.floor(Math.random() * allChars.length));
  }

  // Shuffle the password
  return password
    .split("")
    .sort(() => 0.5 - Math.random())
    .join("");
}
