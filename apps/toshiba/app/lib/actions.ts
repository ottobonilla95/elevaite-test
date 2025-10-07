"use server";
import { AuthError } from "next-auth";
import { signIn, signOut, auth } from "../../auth";
import {
  type ChatMessageResponse,
  type ChatBotGenAI,
  type ChatbotV,
  type ChatMessageObject,
  type SessionSummaryObject,
  SessionObject,
} from "./interfaces";
import {
  isChatMessageResponse,
  isPastSessionsResponse,
  isSessionSummaryResponse,
} from "./discriminators";
import { headers } from "next/headers";
import type { AuthResult, ExtendedAuthFormData } from "@repo/ui";
import { extractErrorCode, mapErrorCodeToAuthResult } from "@repo/ui";

// Example: NEXT_PUBLIC_FRONTEND_URL=https://tgcs.iopex.ai/
// Example: NEXT_PUBLIC_AUTH_API_URL=https://tgcs.iopex.ai/auth-api
const FRONTEND_URL = process.env.NEXT_PUBLIC_FRONTEND_URL ?? "http://localhost:3002";

function getBaseOrigin(): string {
  try {
    const headersList = headers();
    const protocol = headersList.get("x-forwarded-proto") || "http";
    const host = headersList.get("host");
    if (host) return `${protocol}://${host}`;
  } catch {
    // Fail silently
  }
  return FRONTEND_URL;
}

export async function authenticate(
  _prevState: string | undefined,
  formData: ExtendedAuthFormData
): Promise<AuthResult> {
  try {
    await signIn("credentials", formData);
    return undefined;
  } catch (error) {
    // Check if this is a redirect error (successful authentication)
    if (error instanceof Error && error.message === "NEXT_REDIRECT") {
      // This is a successful authentication that's redirecting
      // Re-throw the error to allow the redirect to happen
      throw error;
    }

    if (error instanceof AuthError) {
      // Use centralized error extraction and mapping
      const errorCode = extractErrorCode(error);
      if (errorCode) {
        console.log("DEBUG: Error code extracted:", errorCode);
        return mapErrorCodeToAuthResult(errorCode, error);
      }

      // Fallback: Check for specific error types and return appropriate defaults
      if (error.type === "CredentialsSignin") {
        return "Invalid credentials.";
      }

      // Handle MFA requirements using centralized mapping
      if (error.cause instanceof Error) {
        const mfaResult = mapErrorCodeToAuthResult(
          error.cause.message,
          error.cause
        );
        if (mfaResult !== "Something went wrong.") {
          return mfaResult;
        }
      }
    }

    // Fallback for any other errors
    console.log("DEBUG: Unhandled authentication error:", error);
    return "Something went wrong.";
  }
}

export async function logout(): Promise<Response | void> {
  try {
    const session = await auth();
    const accessToken = session?.authToken ?? session?.user?.accessToken;

    if (accessToken) {
      const authApiUrl = process.env.NEXT_PUBLIC_AUTH_API_URL;
      if (authApiUrl) {
        try {
          const apiUrl = authApiUrl.replace("localhost", "127.0.0.1");
          const tenantId = process.env.NEXT_PUBLIC_AUTH_TENANT_ID ?? "default";

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
    // Continue with NextAuth signOut even if preparation fails
  }

  return await signOut({ redirectTo: "/login" });
}

export async function changeUserPassword(
  currentPassword: string,
  newPassword: string
): Promise<{ success: boolean; message: string }> {
  try {
    const session = await auth();
    const accessToken = session?.authToken;

    if (!accessToken) {
      return {
        success: false,
        message: "Authentication required. Please log in again.",
      };
    }

    const authApiUrl = process.env.NEXT_PUBLIC_AUTH_API_URL;
    if (!authApiUrl) {
      return {
        success: false,
        message: "Server configuration error. Please contact support.",
      };
    }

    const apiUrl = authApiUrl.replace("localhost", "127.0.0.1");
    const tenantId = process.env.NEXT_PUBLIC_AUTH_TENANT_ID ?? "default";

    const response = await fetch(`${apiUrl}/api/user/change-password-user`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
        "X-Tenant-ID": tenantId,
      },
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      return {
        success: false,
        message:
          errorData.detail || "Failed to change password. Please try again.",
      };
    }

    const data = await response.json();
    return {
      success: true,
      message: data.message || "Password changed successfully.",
    };
  } catch (error) {
    console.error("Error changing user password:", error);
    return {
      success: false,
      message: "An unexpected error occurred. Please try again.",
    };
  }
}

export async function recoverSession(): Promise<boolean> {
  try {
    const session = await auth();
    const accessToken = session?.authToken ?? session?.user?.accessToken;

    if (!accessToken) {
      return false;
    }

    const authApiUrl = process.env.NEXT_PUBLIC_AUTH_API_URL;
    if (!authApiUrl) {
      return false;
    }

    const apiUrl = authApiUrl.replace("localhost", "127.0.0.1");
    const tenantId = process.env.NEXT_PUBLIC_AUTH_TENANT_ID ?? "default";

    const response = await fetch(`${apiUrl}/api/auth/recover-session`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
        "X-Tenant-ID": tenantId,
      },
    });

    if (response.ok) {
      console.log("Session recovery successful");
      return true;
    } else {
      console.error("Session recovery failed:", response.status);
      return false;
    }
  } catch (error) {
    console.error("Error during session recovery:", error);
    return false;
  }
}

export async function fetchChatbotResponse(
  userId: string,
  messageText: string,
  sessionId: string,
  messageHistory: ChatMessageObject[],
  chatbotV: ChatbotV,
  chatbotGenAi: ChatBotGenAI
): Promise<ChatMessageResponse> {
  const url = new URL("/api/chatbot", getBaseOrigin());
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
  const url = new URL("/api/summarization", getBaseOrigin());
  url.searchParams.set("uid", userId);
  url.searchParams.set("sid", sessionId);
  const response = await fetch(url);
  if (!response.ok) throw new Error("Failed to fetch");
  const data: unknown = await response.json();
  if (isSessionSummaryResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function getImageUrl(
  filename: string
): Promise<string | undefined> {
  "use server";
  const headersList = headers();
  const headerUrl = new URL(FRONTEND_URL);
  console.log("HeaderURL: ", headerUrl);

  try {
    const _url = new URL(`${headerUrl.origin}/api/images`);
    console.log("URL: ", _url);
    _url.searchParams.set("filename", filename);
    console.log("URL: ", _url);
    return _url.toString();
  } catch (error) {
    console.error("Error fetching image:", error);
  }
}

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
      (session as { accessToken?: string })?.accessToken;

    if (!accessToken) {
      throw new Error("No auth token found in session");
    }

    const authApiUrl = process.env.NEXT_PUBLIC_AUTH_API_URL;
    if (!authApiUrl) {
      throw new Error(
        "NEXT_PUBLIC_AUTH_API_URL not found in environment variables"
      );
    }

    const tenantId = process.env.NEXT_PUBLIC_AUTH_TENANT_ID ?? "default";

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
  const url = new URL("/api/past-sessions", getBaseOrigin());
  url.searchParams.set("uid", userId);
  console.log(userId);
  const response = await fetch(url);
  if (!response.ok) throw new Error("Failed to fetch");
  const data: unknown = await response.json();
  console.log("Past Sessions:", data);
  if (isPastSessionsResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function batchEvaluation(formData: FormData): Promise<any> {
  const url = new URL("/api/batch-evaluation", getBaseOrigin());
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

export async function addSRNumberToSession(
  sessionId: string,
  srNumber: string
) {
  const url = new URL("/api/add-sr-number", getBaseOrigin());
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      session_id: sessionId,
      sr_number: srNumber,
    }),
  });
  if (!response.ok) throw new Error("Failed to add SR number");
  return await response.json();
}
