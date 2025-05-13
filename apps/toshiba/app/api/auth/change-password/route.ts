import { type NextRequest, NextResponse } from "next/server";
import { auth } from "../../../../auth";

export async function POST(req: NextRequest): Promise<NextResponse> {
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

    const body = (await req.json()) as {
      newPassword?: string;
      tenantId?: string;
    };
    const { newPassword, tenantId: requestTenantId } = body;

    if (!newPassword) {
      return NextResponse.json(
        { error: "New password is required" },
        { status: 400 }
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
    const tenantId = requestTenantId ?? process.env.AUTH_TENANT_ID ?? "default";

    const response = await fetch(`${apiUrl}/api/auth/change-password`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
        "X-Tenant-ID": tenantId,
      },
      body: JSON.stringify({
        new_password: newPassword,
      }),
    });

    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };

      return NextResponse.json(
        {
          success: false,
          message: errorData.detail ?? "Failed to reset password",
        },
        { status: response.status }
      );
    }

    return NextResponse.json(
      {
        success: true,
        message: "Password successfully changed",
        needsPasswordReset: false,
      },
      { status: 200 }
    );
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        message:
          error instanceof Error ? error.message : "Failed to reset password",
      },
      { status: 500 }
    );
  }
}
