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

export async function resetPassword(newPassword: string): Promise<void> {
  try {
    // Get the auth token from the session
    const session = await auth();
    if (!session?.user?.accessToken) {
      throw new Error("No access token found in session");
    }

    const authApiUrl = process.env.AUTH_API_URL;
    if (!authApiUrl) {
      throw new Error("AUTH_API_URL not found in environment variables");
    }

    const tenantId = process.env.AUTH_TENANT_ID ?? "default";

    // Debug logging
    console.log("Resetting password for user:", session.user.email);
    console.log("Using auth API URL:", authApiUrl);

    // Call the auth-api to change the password
    const response = await fetch(`${authApiUrl}/api/auth/change-password`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${session.user.accessToken}`,
        "X-Tenant-ID": tenantId,
      },
      body: JSON.stringify({
        new_password: newPassword,
      }),
    });

    // Debug logging
    console.log("Password reset response status:", response.status);

    if (!response.ok) {
      const errorData = await response.json();
      console.error("Password reset error:", errorData);
      throw new Error(errorData.detail || "Failed to reset password");
    }

    const responseData = await response.json();
    console.log("Password reset successful:", responseData);

    // The auth-api will invalidate all sessions for this user,
    // so the user will need to log in again with their new password
  } catch (error) {
    // eslint-disable-next-line no-console -- Needed for error reporting
    console.error("Error resetting password:", error);
    throw new Error("Failed to reset password");
  }
}
