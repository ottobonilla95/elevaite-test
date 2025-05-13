import { type NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { auth } from "../../../../auth";

interface UserData {
  is_password_temporary?: boolean | string | number;
  is_superuser?: boolean;
}

export async function GET(_req: NextRequest): Promise<NextResponse> {
  try {
    // Get the auth token from the session
    const session = await auth();

    // Check for access token in different possible locations
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

    const userData = (await response.json()) as UserData;

    let isTemporary = false;

    if (
      userData.is_password_temporary === true ||
      userData.is_password_temporary === "true"
    ) {
      isTemporary = true;
    } else if (
      userData.is_password_temporary === false ||
      userData.is_password_temporary === "false"
    ) {
      isTemporary = false;
    } else {
      isTemporary = session?.user?.needsPasswordReset === true;
    }

    const sessionNeedsReset = session?.user?.needsPasswordReset ?? false;

    if (isTemporary !== sessionNeedsReset) {
      cookies().set("password_reset_override", isTemporary ? "true" : "false", {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        path: "/",
      });
    }

    return NextResponse.json(
      {
        is_temporary: isTemporary,
        session_needs_reset: sessionNeedsReset,
        override_set: isTemporary !== sessionNeedsReset,
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
