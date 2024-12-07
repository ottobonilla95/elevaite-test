"use server";
import { redirect } from "next/navigation";
import { isChatMessageResponse, isSessionSummaryResponse } from "./discriminators";
import type { ChatBotGenAI, ChatMessageResponse, ChatbotV, SessionSummaryObject } from "./interfaces";



const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
const ARLO_BACKEND_URL = process.env.NEXT_PUBLIC_ARLO_BACKEND_URL;


// eslint-disable-next-line @typescript-eslint/require-await -- Server actions must be async functions
export async function logOut(): Promise<void> {
  redirect(`${process.env.NEXTAUTH_URL_INTERNAL ?? ""}/api/signout`);
}



export async function fetchChatbotResponse(userId: string, messageText: string, sessionId: string, chatbotV: ChatbotV, chatbotGenAi: ChatBotGenAI): Promise<ChatMessageResponse> {
  const url = new URL(`${BACKEND_URL ?? ""}${chatbotV}?query=${messageText}&uid=${userId}&sid=${sessionId}&collection=${chatbotGenAi}`);
  const response = await fetch(url);
  // // # create a mock response for testing
  // var prom = Promise.resolve({
  //       status: 200,
  //       ok: true,
  //       body: {
  //           getReader: () => {
  //               return {
  //                   read: async () => {
  //                       return { done: true, value: "Hello there" };
  //                   }
  //               }
  //           }
  //       },
  //       json: async () => {
  //           return {
  //               text: "Hello",
  //               refs: ["ref1", "ref2"]
  //           }
  //       }
  //   }).then();
  //
  //   const response = await prom;
  //   End of mock response
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

export async function changeCaseID(sessionId: string, caseID: string): Promise<void> {
  const url = new URL(`${ARLO_BACKEND_URL ?? ""}changeCaseID?session_id=${sessionId}&case_id=${caseID}`);

  const response = await fetch(url, {
    method: "GET",
    headers: {
      "Content-Type": "application/json"
    }
  });
  if (!response.ok) throw new Error("Failed to fetch");
  const data: unknown = await response.json();
  console.log(data);
}