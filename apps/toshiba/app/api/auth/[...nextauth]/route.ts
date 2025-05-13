import type { NextRequest } from "next/server";
import { handlers } from "../../../../auth";

const { GET: AuthGET, POST } = handlers;
export { POST };

export async function GET(request: NextRequest): Promise<Response> {
  const response = await AuthGET(request);
  return response;
}
