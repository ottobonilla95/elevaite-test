"use server";
import { AuthError } from "next-auth";
import { signIn, signOut } from "../../auth";

export async function authenticate(
  _prevState: string | undefined,
  formData: Record<"email" | "password", string>
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

export async function resetPassword(_newPassword: string): Promise<void> {
  try {
    // In a real implementation, this would call an API to reset the password
    // For now, we'll just simulate success

    // Simulate a delay for the API call
    await new Promise<void>((resolve) => {
      setTimeout(() => {
        resolve();
      }, 1000);
    });
  } catch (error) {
    // eslint-disable-next-line no-console -- Needed for error reporting
    console.error("Error resetting password:", error);
    throw new Error("Failed to reset password");
  }
}
