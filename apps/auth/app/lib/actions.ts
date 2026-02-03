"use server";
import { AuthError } from "next-auth";
import { signIn, signOut } from "../../auth";

export async function authenticate(
  _prevState: string | undefined,
  formData: Record<"email" | "password", string>,
): Promise<"Invalid credentials." | "Something went wrong." | undefined> {
  try {
    await signIn("credentials", formData);
    return undefined;
  } catch (error) {
    if (error instanceof AuthError) {
      switch (error.type) {
        case "CredentialsSignin":
          return "Invalid credentials.";
        default:
          return "Something went wrong.";
      }
    }
    throw error;
  }
}

export async function authenticateGoogle(): Promise<
  "Invalid credentials." | "Something went wrong." | undefined
> {
  try {
    await signIn("google");
  } catch (error) {
    if (error instanceof AuthError) {
      switch (error.type) {
        case "CredentialsSignin":
          return "Invalid credentials.";
        default:
          return "Something went wrong.";
      }
    }
    throw error;
  }
}

export async function logOut(): Promise<
  "Invalid credentials." | "Something went wrong." | undefined
> {
  try {
    // auth()
    await signOut({ redirectTo: "/login" });
  } catch (error) {
    if (error instanceof AuthError) {
      switch (error.type) {
        case "CredentialsSignin":
          return "Invalid credentials.";
        default:
          return "Something went wrong.";
      }
    }
    throw error;
  }
}

const AUTH_API_URL = process.env.AUTH_API_URL;

export async function resetPassword(
  token: string,
  newPassword: string,
): Promise<{ success: boolean; error?: string }> {
  if (!AUTH_API_URL) {
    return { success: false, error: "Server configuration error" };
  }

  try {
    const response = await fetch(`${AUTH_API_URL}/api/auth/reset-password`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        token,
        new_password: newPassword,
      }),
    });

    if (!response.ok) {
      let errorMessage = "Failed to reset password. Please try again.";
      try {
        const data = (await response.json()) as {
          detail?: string | { msg: string }[];
        };
        if (data.detail) {
          if (typeof data.detail === "string") {
            errorMessage = data.detail;
          } else if (Array.isArray(data.detail) && data.detail.length > 0) {
            // Handle Pydantic validation errors
            errorMessage = data.detail.map((e) => e.msg).join(". ");
          }
        }
      } catch {
        // Use default error message if JSON parsing fails
      }
      return { success: false, error: errorMessage };
    }

    return { success: true };
  } catch (error) {
    // eslint-disable-next-line no-console -- Needed for error reporting
    console.error("Error resetting password:", error);
    return {
      success: false,
      error: "Failed to reset password. Please try again.",
    };
  }
}
