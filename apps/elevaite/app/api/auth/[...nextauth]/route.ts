import { handlers } from "../../../../auth";

const { GET: AuthGET, POST } = handlers;
export { POST };

// Showcasing advanced initialization in Route Handlers
// Using Parameters utility type to get the correct request type from handlers
export async function GET(
  request: Parameters<typeof AuthGET>[0],
): Promise<Response> {
  // Do something with request
  const response = await AuthGET(request);
  // Do something with response
  return response;
}
