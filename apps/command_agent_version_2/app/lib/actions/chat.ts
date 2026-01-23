"use server";

// Placeholder chat actions; flesh out when chat endpoints are available.
// eslint-disable-next-line @typescript-eslint/require-await -- Server actions must be async
export async function sendChatMessage(_payload: unknown): Promise<never> {
  throw new Error("Chat action not implemented");
}
