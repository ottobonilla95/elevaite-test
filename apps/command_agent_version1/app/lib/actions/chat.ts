"use server";

import {
  isChatMessageResponse,
  isSessionSummaryResponse,
} from "../discriminators/chat";
import type {
  ChatBotGenAI,
  ChatMessageResponse,
  ChatbotV,
  SessionSummaryObject,
} from "../interfaces/chat";
import { BACKEND_URL } from "../constants";

export async function fetchChatbotResponse(
  userId: string,
  messageText: string,
  sessionId: string,
  chatbotV: ChatbotV,
  chatbotGenAi: ChatBotGenAI
): Promise<ChatMessageResponse> {
  // const url = new URL(`${BACKEND_URL ?? ""}${chatbotV}?query=${messageText}&uid=${userId}&sid=${sessionId}&collection=${chatbotGenAi}`);
  // Write a POST request to the backend
  const url = new URL(`${BACKEND_URL ?? ""}run`);

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query: messageText,
      uid: userId,
      sid: sessionId,
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
