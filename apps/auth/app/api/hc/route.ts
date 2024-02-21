export const dynamic = "force-dynamic"; // defaults to auto
// eslint-disable-next-line @typescript-eslint/explicit-function-return-type, @typescript-eslint/require-await -- that's how we want it
export async function GET(request: Request) {
  // eslint-disable-next-line @typescript-eslint/no-unsafe-return, @typescript-eslint/no-unsafe-call -- that's how we want it
  return Response.json({ health: "ok" });
}
