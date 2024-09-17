export const dynamic = "force-dynamic"; // defaults to auto
// eslint-disable-next-line no-unused-vars, @typescript-eslint/no-unused-vars, @typescript-eslint/explicit-function-return-type, @typescript-eslint/require-await -- Health Check URL
export async function GET(request: Request) {
  // eslint-disable-next-line @typescript-eslint/no-unsafe-return, @typescript-eslint/no-unsafe-call -- This is how we need it
  return Response.json({ health: "ok" });
}
