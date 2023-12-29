import { signOut } from "../../../auth";

export const dynamic = "force-dynamic"; // defaults to auto
// eslint-disable-next-line no-unused-vars, @typescript-eslint/no-unused-vars, @typescript-eslint/explicit-function-return-type -- logout
export async function GET(request: Request) {
  await signOut({ redirectTo: "/login" });
}
