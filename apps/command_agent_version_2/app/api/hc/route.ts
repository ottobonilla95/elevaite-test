export const dynamic = "force-dynamic"; // defaults to auto
// eslint-disable-next-line @typescript-eslint/explicit-function-return-type, @typescript-eslint/require-await -- Health Check URL
export async function GET(_request: Request) {   
  return Response.json({ health: "ok" });
}
