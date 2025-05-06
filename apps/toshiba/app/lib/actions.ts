"use server";
import { AuthError } from "next-auth";
import { signIn, signOut } from "../../auth";
import { type ChatMessageResponse, type ChatBotGenAI, type ChatbotV, type ChatMessageObject, type SessionSummaryObject } from "./interfaces";
import { isChatMessageResponse, isSessionSummaryResponse } from "./discriminators";

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


export async function fetchChatbotResponse(userId: string, messageText: string, sessionId: string, messageHistory: ChatMessageObject[], chatbotV: ChatbotV, chatbotGenAi: ChatBotGenAI): Promise<ChatMessageResponse> {
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

export async function fetchSessionSummary(userId: string, sessionId: string): Promise<SessionSummaryObject> {
  const url = new URL(`${BACKEND_URL ?? ""}summarization?uid=${userId}&sid=${sessionId}`);
  const response = await fetch(url);
  if (!response.ok) throw new Error("Failed to fetch");
  const data: unknown = await response.json();
  if (isSessionSummaryResponse(data)) return data;
  throw new Error("Invalid data type");
}