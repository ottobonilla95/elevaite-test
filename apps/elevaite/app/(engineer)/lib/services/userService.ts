"use server";

import { revalidatePath } from "next/cache";

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

/**
 * Creates a new user by combining first and last name into full_name
 * and sending a request to the auth API
 */
export async function createUser(
  params: CreateUserParams
): Promise<{ success: boolean; message: string }> {
  try {
    const { firstName, lastName, email, password, isOneTimePassword } = params;

    // Combine first and last name into full_name as required by the API
    const fullName = `${firstName} ${lastName}`.trim();

    // Force using localhost for development
    const backendUrl = "http://localhost:8000";
    const response = await fetch(`${backendUrl}/api/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
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

    // User created successfully, now send a password reset email
    const resetResponse = await fetch(
      `${backendUrl}/api/auth/forgot-password`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email }),
      }
    );

    if (!resetResponse.ok) {
      try {
        await resetResponse.json();
      } catch {
        // Ignore parsing errors
      }

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
  } catch {
    return {
      success: false,
      message: "An unexpected error occurred. Please try again later.",
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
