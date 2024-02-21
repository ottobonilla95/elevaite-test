import { signOut } from "../../../auth";

export const dynamic = "force-dynamic"; // defaults to auto
export async function GET(request: Request) {
    await signOut({ redirectTo: "/login" });
}
