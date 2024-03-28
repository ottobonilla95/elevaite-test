export const dynamic = "force-dynamic"; // defaults to auto
// eslint-disable-next-line @typescript-eslint/no-unused-vars, @typescript-eslint/explicit-function-return-type, @typescript-eslint/require-await -- Health Check URL
export async function GET(request: Request) {
  // eslint-disable-next-line @typescript-eslint/no-unsafe-return, @typescript-eslint/no-unsafe-call -- This is how it needs to be
  return Response.json({ health: "ok" });
}
