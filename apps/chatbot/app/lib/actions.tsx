"use server";
import { redirect } from "next/navigation";
import { ChatBotGenAI, ChatbotV } from "./interfaces";



const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;



// eslint-disable-next-line @typescript-eslint/require-await -- Server actions must be async functions
export async function logOut(): Promise<void> {
  redirect(`${process.env.NEXTAUTH_URL_INTERNAL}/api/signout`);
}


export async function getAgentEventSource(userId: string, sessionId: string): Promise<EventSource> {
    return new EventSource(`${BACKEND_URL}currentStatus?uid=${userId}&sid=${sessionId}`);
}


export async function getStreamingResponse(userId: string, messageText: string, sessionId: string, chatbotV: ChatbotV, chatbotGenAi: ChatBotGenAI) {
    const url = new URL(`${BACKEND_URL}${chatbotV}?query=${messageText}&uid=${userId}&sid=${sessionId}&collection=${chatbotGenAi}`);
    const response = await fetch(url);
    if (!response.ok) throw new Error("Failed to fetch");
    const data: unknown = await response.json();
    return data;

    // if (isGetApplicationListReponse(data)) return data;
    // throw new Error("Invalid data type");
}


// streaming and non-streaming response seem to point to the same endpoint. >.<



