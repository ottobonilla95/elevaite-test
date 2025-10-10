import { type NextRequest, NextResponse } from "next/server";
import { auth } from "../../../../../auth";

export async function POST(req: NextRequest) {
  try {
    // Get the auth token from the session
    const session = await auth();
    console.log("Change Password API - Session:", session?.user?.email);

    // Check for access token in different possible locations
    const accessToken =
      session?.authToken ??
      session?.user?.accessToken ??
      (session as { accessToken?: string }).accessToken;

    if (!accessToken) {
      console.error("Change Password API - No auth token found in session");
      return NextResponse.json(
        { error: "Authentication required" },
        { status: 401 }
      );
    }

    // Parse the request body
    const body = await req.json();
    const { new_password, tenant_id } = body;

    if (!new_password) {
      return NextResponse.json(
        { error: "New password is required" },
        { status: 400 }
      );
    }

    const authApiUrl = process.env.NEXT_PUBLIC_AUTH_API_URL;
    if (!authApiUrl) {
      console.error(
        "Change Password API - NEXT_PUBLIC_AUTH_API_URL not found in environment variables"
      );
      return NextResponse.json(
        { error: "Server configuration error" },
        { status: 500 }
      );
    }

    // Explicitly use IPv4 address instead of localhost to avoid IPv6 issues
    const apiUrl = authApiUrl.replace("localhost", "127.0.0.1");
    const tenantId = process.env.NEXT_PUBLIC_AUTH_TENANT_ID || "default";

    console.log("Change Password API - Using auth API URL:", apiUrl);
    console.log("Change Password API - Using tenant ID:", tenantId);

    // Call the auth-api to change the password
    const response = await fetch(`${apiUrl}/api/auth/change-password`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
        "X-Tenant-ID": tenantId,
      },
      body: JSON.stringify({
        new_password,
      }),
    });

    // Debug logging
    console.log(
      "Change Password API - Password reset response status:",
      response.status
    );

    if (!response.ok) {
      const errorData = await response.json();
      console.error("Change Password API - Password reset error:", errorData);
      return NextResponse.json(
        {
          success: false,
          message: errorData.detail || "Failed to reset password",
        },
        { status: response.status }
      );
    }

    const responseData = await response.json();
    console.log(
      "Change Password API - Password reset successful:",
      responseData
    );

    // Return success response
    return NextResponse.json(
      {
        success: true,
        message: "Password successfully changed",
        needsPasswordReset: false,
      },
      { status: 200 }
    );
  } catch (error) {
    console.error("Change Password API - Error:", error);
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
