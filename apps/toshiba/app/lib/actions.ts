"use server";
import { AuthError } from "next-auth";
import { signIn, signOut, auth } from "../../auth";
import {
  type ChatMessageResponse,
  type ChatBotGenAI,
  type ChatbotV,
  type ChatMessageObject,
  type SessionSummaryObject,
} from "./interfaces";
import {
  isChatMessageResponse,
  isSessionSummaryResponse,
} from "./discriminators";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

export async function authenticate(
  _prevState: string | undefined,
  formData: Record<"email" | "password", string>
): Promise<
  | "Invalid credentials."
  | "Email not verified."
  | "Something went wrong."
  | undefined
> {
  try {
    await signIn("credentials", formData);
    return undefined;
  } catch (error) {
    if (error instanceof AuthError) {
      switch (error.type) {
        case "CredentialsSignin":
          return "Invalid credentials.";
        default:
          // Check if this is an email verification error
          if (error.message?.includes("email_not_verified")) {
            return "Email not verified.";
          }
          return "Something went wrong.";
      }
    }
    // Check for custom errors
    if (error instanceof Error && error.message === "email_not_verified") {
      return "Email not verified.";
    }
    throw error;
  }
}

export async function logout(): Promise<void> {
  await signOut();
}

export async function fetchChatbotResponse(
  userId: string,
  messageText: string,
  sessionId: string,
  messageHistory: ChatMessageObject[],
  chatbotV: ChatbotV,
  chatbotGenAi: ChatBotGenAI
): Promise<ChatMessageResponse> {
  const url = `${BACKEND_URL ?? ""}run`;
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query: messageText,
      uid: userId,
      sid: sessionId,
      messages: messageHistory.slice(-6),
      collection: chatbotGenAi,
    }),
  });
  if (!response.ok) throw new Error("Failed to fetch");
  const data: unknown = await response.json();
  if (isChatMessageResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function fetchSessionSummary(
  userId: string,
  sessionId: string
): Promise<SessionSummaryObject> {
  const url = new URL(
    `${BACKEND_URL ?? ""}summarization?uid=${userId}&sid=${sessionId}`
  );
  const response = await fetch(url);
  if (!response.ok) throw new Error("Failed to fetch");
  const data: unknown = await response.json();
  if (isSessionSummaryResponse(data)) return data;
  throw new Error("Invalid data type");
}

// Server action for resetting password
export async function resetPassword(newPassword: string): Promise<{
  success: boolean;
  message: string;
  needsPasswordReset?: boolean;
}> {
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

    // Check for access token in different possible locations
    const accessToken =
      session?.authToken ??
      session?.user?.accessToken ??
      (session as { accessToken?: string })?.accessToken;

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
      const errorData: unknown = await response.json();
      console.error("Server Action - Password reset error:", errorData);
      return {
        success: false,
        message:
          typeof errorData === "object" &&
          errorData !== null &&
          "detail" in errorData
            ? typeof errorData === "object" && "detail" in errorData
              ? String(errorData.detail)
              : "Unknown error"
            : "Failed to reset password",
      };
    }

    const responseData = await response.json();
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
