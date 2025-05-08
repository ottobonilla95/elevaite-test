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
  console.log(
    "Server Action - resetPassword called with password length:",
    newPassword.length
  );

  try {
    // Get the auth token from the session
    const session = await auth();
    console.log("Server Action - Session:", session?.user?.email);
    console.log(
      "Server Action - Full session:",
      JSON.stringify(session, null, 2)
    );

    // The token is stored in session.authToken, not in session.user.accessToken
    if (!session?.authToken) {
      console.error("Server Action - No auth token found in session");
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

    // Debug logging
    console.log(
      "Server Action - Resetting password for user:",
      session.user?.email ?? "unknown"
    );
    console.log("Server Action - Using auth API URL:", authApiUrl);
    console.log("Server Action - Using tenant ID:", tenantId);

    // Call the auth-api to change the password
    const response = await fetch(`${authApiUrl}/api/auth/change-password`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${session.authToken}`,
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
      const errorData = await response.json();
      console.error("Server Action - Password reset error:", errorData);
      return {
        success: false,
        message: errorData.detail || "Failed to reset password",
      };
    }

    const responseData = await response.json();
    console.log("Server Action - Password reset successful:", responseData);

    // The auth-api will invalidate all sessions for this user,
    // so the user will need to log in again with their new password
    return {
      success: true,
      message: "Password successfully changed",
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
