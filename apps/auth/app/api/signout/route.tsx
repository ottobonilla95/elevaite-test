import { signOut } from "../../../auth";

export const dynamic = "force-dynamic"; // defaults to auto
export async function GET(_request: Request): Promise<void> {
  await signOut({ redirectTo: "/login" });
}
