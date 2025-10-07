import { logout } from "../../lib/actions";

export const dynamic = "force-dynamic";

export async function GET() {
  await logout();
}
