export const dynamic = "force-dynamic"; // defaults to auto
// eslint-disable-next-line no-unused-vars, @typescript-eslint/no-unused-vars, @typescript-eslint/explicit-function-return-type, @typescript-eslint/require-await -- Health Check URL
export async function GET(request: Request) {
  return Response.json({ health: "ok" });
}
