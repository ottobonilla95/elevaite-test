"use server";
import { redirect } from "next/navigation";
import { isChatMessageResponse, isSessionSummaryResponse } from "./discriminators";
import type { ChatBotGenAI, ChatMessageResponse, ChatbotV, SessionSummaryObject } from "./interfaces";



const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;



// eslint-disable-next-line @typescript-eslint/require-await -- Server actions must be async functions
export async function logOut(): Promise<void> {
  redirect(`${process.env.NEXTAUTH_URL_INTERNAL ?? ""}/api/signout`);
}



// export async function fetchChatbotResponse(userId: string, messageText: string, sessionId: string, chatbotV: ChatbotV, chatbotGenAi: ChatBotGenAI): Promise<ChatMessageResponse> {
//   const url = new URL(`${BACKEND_URL ?? ""}${chatbotV}?query=${messageText}&uid=${userId}&sid=${sessionId}&collection=${chatbotGenAi}`);
//   const response = await fetch(url);
//   if (!response.ok) throw new Error("Failed to fetch");
//   const data: unknown = await response.json();
//   if (isChatMessageResponse(data)) return data;
//   throw new Error("Invalid data type");
// }

export async function fetchChatbotResponse(userId: string, messageText: string, sessionId: string, chatbotV: ChatbotV, chatbotGenAi: ChatBotGenAI): Promise<ChatMessageResponse> {
  const url = new URL(`${BACKEND_URL ?? ""}run?query=${messageText}&uid=${userId}&sid=${sessionId}&collection=${chatbotGenAi}`);
  // const url = new URL(`${BACKEND_URL ?? "http://localhost:8000/"}run?query=${messageText}&uid=${userId}&sid=${sessionId}&collection=${chatbotGenAi}`);
  const response = await fetch(url);
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

