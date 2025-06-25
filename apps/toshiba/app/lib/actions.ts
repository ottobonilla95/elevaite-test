"use server";
import { AuthError } from "next-auth";
import { signIn, signOut, auth } from "../../auth";

export async function authenticate(
  _prevState: string | undefined,
  formData: Record<"email" | "password", string>
): Promise<
  | "Invalid credentials."
  | "Email not verified."
  | "Admin access required."
  | "Something went wrong."
  | undefined
> {
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
          // Check if this is an email verification error
          if (error.message.includes("email_not_verified")) {
            return "Email not verified.";
          }
          // Check if this is an admin access required error
          if (error.message.includes("admin_access_required")) {
            return "Admin access required.";
          }
          return "Something went wrong.";
      }
    }
    // Check for custom errors
    if (error instanceof Error) {
      if (error.message === "email_not_verified") {
        return "Email not verified.";
      }
      if (error.message === "admin_access_required") {
        return "Admin access required.";
      }
    }
    throw error;
  }
}

export async function authenticateGoogle(): Promise<
  | "Invalid credentials."
  | "Email not verified."
  | "Admin access required."
  | "Something went wrong."
  | undefined
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
          // Check if this is an email verification error
          if (error.message.includes("email_not_verified")) {
            return "Email not verified.";
          }
          // Check if this is an admin access required error
          if (error.message.includes("admin_access_required")) {
            return "Admin access required.";
          }
          return "Something went wrong.";
      }
    }
    // Check for custom errors
    if (error instanceof Error) {
      if (error.message === "email_not_verified") {
        return "Email not verified.";
      }
      if (error.message === "admin_access_required") {
        return "Admin access required.";
      }
    }
    throw error;
  }
}

export async function logout(): Promise<void> {
  try {
    const session = await auth();
    const accessToken = session?.authToken ?? session?.user?.accessToken;

    if (accessToken) {
      const authApiUrl = process.env.AUTH_API_URL;
      if (authApiUrl) {
        try {
          const apiUrl = authApiUrl.replace("localhost", "127.0.0.1");
          const tenantId = process.env.AUTH_TENANT_ID ?? "default";

          const refreshToken = session?.user?.refreshToken;

          if (refreshToken) {
            await fetch(`${apiUrl}/api/auth/logout`, {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${accessToken}`,
                "X-Tenant-ID": tenantId,
              },
              body: JSON.stringify({
                refresh_token: refreshToken,
              }),
            });
          }
        } catch (apiError) {
          // Continue with NextAuth signOut even if API call fails
        }
      }
    }
  } catch (error) {
    console.error("Error during logout preparation:", error);
    // Continue with NextAuth signOut even if preparation fails
  }

  await signOut({ redirectTo: "/login" });
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

    if (!response.ok) {
      const errorData: unknown = await response.json();
      console.error("Server Action - Password reset error:", errorData);

      let errorMessage = "Failed to reset password";
      if (
        typeof errorData === "object" &&
        errorData !== null &&
        "detail" in errorData
      ) {
        const detail = (errorData as { detail: unknown }).detail;
        console.log("Server Action - Error detail:", detail, typeof detail);

        if (typeof detail === "string") {
          errorMessage = detail;
        } else if (Array.isArray(detail) && detail.length > 0) {
          // Handle Pydantic validation errors which return an array of error objects
          const firstError = detail[0];
          if (
            typeof firstError === "object" &&
            firstError !== null &&
            "msg" in firstError
          ) {
            errorMessage = String((firstError as { msg: unknown }).msg);
          } else {
            errorMessage = "Password validation failed";
          }
        } else if (detail !== null && detail !== undefined) {
          errorMessage = String(detail);
        }
      }

      console.log(
        "Server Action - Final error message:",
        errorMessage,
        typeof errorMessage
      );
      return {
        success: false,
        message: errorMessage,
      };
    }

    // The auth-api will invalidate all sessions for this user,
    // so the user will need to log in again with their new password
    // Also explicitly return that the user no longer needs to reset their password
    return {
      success: true,
      message: "Password successfully changed",
      needsPasswordReset: false, // Explicitly set to false after successful password reset
    };
  } catch (error) {
    return {
      success: false,
      message:
        error instanceof Error ? error.message : "Failed to reset password",
    };
  }
}

export async function fetchPastSessions(
  userId: string
): Promise<SessionObject[]> {
  const url = new URL(`${BACKEND_URL ?? ""}pastSessions?uid=${userId}`);
  console.log(userId);
  const response = await fetch(url);
  if (!response.ok) throw new Error("Failed to fetch");
  const data: unknown = await response.json();
  console.log("Past Sessions:", data);
  if (isPastSessionsResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function batchEvaluation(formData: FormData): Promise<any> {
  const url = new URL(`${BACKEND_URL ?? ""}batchEvaluation`);
  const response = await fetch(url, {
    method: "POST",
    // headers: {
    //   "Content-Type": "multipart/form-data",
    // },
    body: formData,
  });
  if (!response.ok) throw new Error("Failed to upload file");
  return await response.json();
}
