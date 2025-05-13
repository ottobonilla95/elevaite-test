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
export async function resetPassword(newPassword: string): Promise<{
  success: boolean;
  message: string;
  needsPasswordReset?: boolean;
}> {
  try {
    // Get the auth token from the session
    const session = await auth();
    console.log("Server Action - Session:", session?.user?.email);
    console.log(
      "Server Action - Full session:",
      JSON.stringify(session, null, 2)
    );

    // Check for access token in different possible locations
    const accessToken =
      session?.authToken ??
      session?.user?.accessToken ??
      (session as { accessToken?: string }).accessToken;

    if (!accessToken) {
      console.error("Server Action - No auth token found in session");
      console.error(
        "Server Action - Session keys:",
        Object.keys(session ?? {})
      );
      if (session?.user) {
        console.error("Server Action - User keys:", Object.keys(session.user));
      }
      throw new Error("No auth token found in session");
    }

    const authApiUrl = process.env.AUTH_API_URL;
    if (!authApiUrl) {
      console.error(
        "Server Action - AUTH_API_URL not found in environment variables"
      );
      throw new Error("AUTH_API_URL not found in environment variables");
    }

    const tenantId = process.env.AUTH_TENANT_ID ?? "default";

    console.log(
      "Server Action - Resetting password for user:",
      session.user?.email ?? "unknown"
    );
    console.log("Server Action - Using auth API URL:", authApiUrl);
    console.log("Server Action - Using tenant ID:", tenantId);

    // Explicitly use IPv4 address instead of localhost to avoid IPv6 issues
    const apiUrl = authApiUrl.replace("localhost", "127.0.0.1");

    // Call the auth-api to change the password
    const response = await fetch(`${apiUrl}/api/auth/change-password`, {
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

    // Debug logging
    console.log(
      "Server Action - Password reset response status:",
      response.status
    );

    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      console.error("Server Action - Password reset error:", errorData);
      return {
        success: false,
        message: errorData.detail ?? "Failed to reset password",
      };
    }

    const responseData = (await response.json()) as Record<string, unknown>;
    console.log("Server Action - Password reset successful:", responseData);

    // The auth-api will invalidate all sessions for this user,
    // so the user will need to log in again with their new password
    // Also explicitly return that the user no longer needs to reset their password
    return {
      success: true,
      message: "Password successfully changed",
      needsPasswordReset: false, // Explicitly set to false after successful password reset
    };
  } catch (error) {
    console.error("Server Action - Error resetting password:", error);
    return {
      success: false,
      message:
        error instanceof Error ? error.message : "Failed to reset password",
    };
  }
}
