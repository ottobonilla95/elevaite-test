"use server";
import { AuthError } from "next-auth";
import { signIn, signOut, auth } from "../../auth";

export async function authenticate(
  _prevState: string | undefined,
  formData: Record<"email" | "password", string>
): Promise<"Invalid credentials." | "Something went wrong." | undefined> {
  try {
    await signIn("credentials", {
      ...formData,
      redirect: true,
      callbackUrl: "/",
    });
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
    await signIn("google", {
      redirect: true,
      callbackUrl: "/",
    });
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

export async function logout(): Promise<void> {
  await signOut();
}

// Server action for resetting password
export async function resetPassword(
  newPassword: string
): Promise<{ success: boolean; message: string }> {
  try {
    // Get the auth token from the session
    const session = await auth();

    // Check for access token in different possible locations
    const accessToken =
      session?.authToken ??
      session?.user?.accessToken ??
      (session as { accessToken?: string }).accessToken;

    if (!accessToken) {
      throw new Error("No auth token found in session");
    }

    const authApiUrl = process.env.AUTH_API_URL;
    if (!authApiUrl) {
      throw new Error("AUTH_API_URL not found in environment variables");
    }

    const tenantId = process.env.AUTH_TENANT_ID ?? "default";

    // Call the auth-api to change the password
    const response = await fetch(`${authApiUrl}/api/auth/change-password`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
        "X-Tenant-ID": tenantId,
      },
      body: JSON.stringify({
        new_password: newPassword,
      }),
    });

    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      return {
        success: false,
        message: errorData.detail ?? "Failed to reset password",
      };
    }

    const _responseData = (await response.json()) as Record<string, unknown>;

    // The auth-api will invalidate all sessions for this user,
    // so the user will need to log in again with their new password
    return {
      success: true,
      message: "Password successfully changed",
    };
  } catch (error) {
    return {
      success: false,
      message:
        error instanceof Error ? error.message : "Failed to reset password",
    };
  }
}
