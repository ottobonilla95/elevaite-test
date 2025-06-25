import { NextResponse } from "next/server";
import { auth } from "../../../../auth";

export async function GET() {
  try {
    const session = await auth();

    const accessToken =
      session?.authToken ??
      session?.user?.accessToken ??
      (session as any)?.accessToken;

    if (!accessToken) {
      return NextResponse.json(
        { error: "Authentication required", is_admin: false },
        { status: 401 }
      );
    }

    const authApiUrl = process.env.AUTH_API_URL;
    if (!authApiUrl) {
      return NextResponse.json(
        { error: "Server configuration error", is_admin: false },
        { status: 500 }
      );
    }

    // Explicitly use IPv4 address instead of localhost to avoid IPv6 issues
    const apiUrl = authApiUrl.replace("localhost", "127.0.0.1");
    const tenantId = process.env.AUTH_TENANT_ID ?? "default";

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
        { error: "Failed to get user information", is_admin: false },
        { status: response.status }
      );
    }

    const userData = await response.json();

    // Check if the user is a superuser/admin
    const isAdmin = userData.is_superuser === true;

    // Return the admin status
    return NextResponse.json(
      {
        is_admin: isAdmin,
      },
      { status: 200 }
    );
  } catch (error) {
    return NextResponse.json(
      { error: "Internal server error", is_admin: false },
      { status: 500 }
    );
  }
}
