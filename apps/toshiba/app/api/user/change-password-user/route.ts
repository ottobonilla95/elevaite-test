import { type NextRequest, NextResponse } from "next/server";
import { auth } from "../../../../auth";

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  try {
    const session = await auth();

    const accessToken = session?.authToken;

    if (!accessToken) {
      return NextResponse.json(
        { detail: "No access token found" },
        { status: 401 }
      );
    }

    const body = await req.json();
    const { current_password, new_password } = body;

    if (!current_password || !new_password) {
      return NextResponse.json(
        { error: "Current password and new password are required" },
        { status: 400 }
      );
    }

    const authApiUrl = process.env.NEXT_PUBLIC_AUTH_API_URL;
    if (!authApiUrl) {
      console.error(
        "Change Password User API - NEXT_PUBLIC_AUTH_API_URL not found in environment variables"
      );
      return NextResponse.json(
        { error: "Server configuration error" },
        { status: 500 }
      );
    }

    const apiUrl = authApiUrl.replace("localhost", "127.0.0.1");
    const tenantId = process.env.NEXT_PUBLIC_AUTH_TENANT_ID || "default";

    console.log("Change Password User API - Using auth API URL:", apiUrl);
    console.log("Change Password User API - Using tenant ID:", tenantId);

    const response = await fetch(`${apiUrl}/api/user/change-password-user`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
        "X-Tenant-ID": tenantId,
      },
      body: JSON.stringify({
        current_password,
        new_password,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error("Change Password User API - Error response:", errorData);
      return NextResponse.json(
        { error: errorData.detail || "Failed to change password" },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log("Change Password User API - Success:", data);

    return NextResponse.json(data);
  } catch (error) {
    console.error("Change Password User API - Unexpected error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
