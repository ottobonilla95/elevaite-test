import { NextRequest, NextResponse } from "next/server";
import { auth } from "../../../../auth";

export async function GET(req: NextRequest) {
  try {
    // Get the auth token from the session
    const session = await auth();
    console.log("Password Status API - Session:", session?.user?.email);

    // Check for access token in different possible locations
    const accessToken =
      session?.authToken ??
      session?.user?.accessToken ??
      (session as { accessToken?: string })?.accessToken;

    if (!accessToken) {
      console.error("Password Status API - No auth token found in session");
      return NextResponse.json(
        { error: "Authentication required" },
        { status: 401 }
      );
    }

    const authApiUrl = process.env.AUTH_API_URL;
    if (!authApiUrl) {
      console.error(
        "Password Status API - AUTH_API_URL not found in environment variables"
      );
      return NextResponse.json(
        { error: "Server configuration error" },
        { status: 500 }
      );
    }

    // Explicitly use IPv4 address instead of localhost to avoid IPv6 issues
    const apiUrl = authApiUrl.replace("localhost", "127.0.0.1");
    const tenantId = process.env.AUTH_TENANT_ID ?? "default";

    console.log("Password Status API - Using auth API URL:", apiUrl);
    console.log("Password Status API - Using tenant ID:", tenantId);

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
      console.error(
        "Password Status API - Failed to get user info:",
        response.status
      );
      return NextResponse.json(
        { error: "Failed to get user information" },
        { status: response.status }
      );
    }

    const userData = await response.json();
    console.log("Password Status API - User data:", userData);

    // Log the raw value for debugging
    console.log(
      "Password Status API - Raw is_password_temporary value:",
      userData.is_password_temporary
    );

    let isTemporary = false;

    if (
      userData.is_password_temporary === true ??
      userData.is_password_temporary === "true"
    ) {
      isTemporary = true;
    } else if (
      userData.is_password_temporary === false ??
      userData.is_password_temporary === "false"
    ) {
      isTemporary = false;
    } else {
      // If the value is null, undefined, or something else, fall back to the session value
      isTemporary = session?.user?.needsPasswordReset === true;
      console.log(
        "Password Status API - Falling back to session needsPasswordReset value:",
        isTemporary
      );
    }

    console.log(
      "Password Status API - Session needsPasswordReset value:",
      session?.user?.needsPasswordReset
    );
    console.log("Password Status API - isTemporary calculated:", isTemporary);

    // Return the password status
    return NextResponse.json(
      {
        is_temporary: isTemporary,
        // Include the session's needsPasswordReset value for debugging
        session_needs_reset: session?.user?.needsPasswordReset ?? false,
        // Include the raw API response for debugging
        raw_is_password_temporary: userData.is_password_temporary,
      },
      { status: 200 }
    );
  } catch (error) {
    console.error("Password Status API - Error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
