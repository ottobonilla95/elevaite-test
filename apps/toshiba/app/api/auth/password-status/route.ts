import { type NextRequest, NextResponse } from "next/server";
import { auth } from "../../../../auth";

export async function GET(_req: NextRequest): Promise<NextResponse> {
  try {
    const session = await auth();

    const accessToken =
      session?.authToken ??
      session?.user?.accessToken ??
      (session as { accessToken?: string }).accessToken;

    if (!accessToken) {
      return NextResponse.json(
        { error: "Authentication required" },
        { status: 401 }
      );
    }

    const authApiUrl = process.env.AUTH_API_URL;
    if (!authApiUrl) {
      return NextResponse.json(
        { error: "Server configuration error" },
        { status: 500 }
      );
    }

    // Explicitly use IPv4 address instead of localhost to avoid IPv6 issues
    const apiUrl = authApiUrl.replace("localhost", "127.0.0.1");
    const tenantId = process.env.AUTH_TENANT_ID ?? "default";

    // Call the auth-api to check password status
    const response = await fetch(`${apiUrl}/api/auth/me`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
        "X-Tenant-ID": tenantId,
      },
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: "Failed to get user information" },
        { status: response.status }
      );
    }

    interface UserData {
      is_password_temporary?: boolean | string | number | null;
    }

    const userData = (await response.json()) as UserData;

    let isTemporary = false;

    if (
      userData.is_password_temporary === true ||
      userData.is_password_temporary === "true" ||
      userData.is_password_temporary === 1
    ) {
      isTemporary = true;
    } else if (
      userData.is_password_temporary === false ||
      userData.is_password_temporary === "false" ||
      userData.is_password_temporary === 0
    ) {
      isTemporary = false;
    } else {
      isTemporary = session?.user?.needsPasswordReset === true;
    }

    return NextResponse.json(
      {
        is_temporary: isTemporary,
        session_needs_reset: session?.user?.needsPasswordReset ?? false,
        raw_is_password_temporary: userData.is_password_temporary,
      },
      { status: 200 }
    );
  } catch (error) {
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
