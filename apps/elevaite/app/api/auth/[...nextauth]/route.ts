import type { NextRequest } from "next/server";
import { handlers } from "../../../../auth";

const { GET: AuthGET, POST } = handlers;
export { POST };

// Showcasing advanced initialization in Route Handlers
export async function GET(request: NextRequest) {
  // Do something with request
  //@ts-expect-error -- types are identical
  const response = await AuthGET(request);
  // Do something with response
  return response;
}
