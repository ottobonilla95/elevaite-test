import { NextRequest, NextResponse } from "next/server";
import { auth } from "../../../../auth";
import { cookies } from "next/headers";

export async function GET(req: NextRequest) {
  try {
    // Get the auth token from the session
    const session = await auth();
    console.log("Check Password Reset API - Session:", session?.user?.email);

    // Check for access token in different possible locations
    const accessToken =
      session?.authToken ??
      session?.user?.accessToken ??
      (session as { accessToken?: string })?.accessToken;

    if (!accessToken) {
      console.error(
        "Check Password Reset API - No auth token found in session"
      );
      return NextResponse.json(
        { error: "Authentication required" },
        { status: 401 }
      );
    }

    const authApiUrl = process.env.AUTH_API_URL;
    if (!authApiUrl) {
      console.error(
        "Check Password Reset API - AUTH_API_URL not found in environment variables"
      );
      return NextResponse.json(
        { error: "Server configuration error" },
        { status: 500 }
      );
    }

    // Explicitly use IPv4 address instead of localhost to avoid IPv6 issues
    const apiUrl = authApiUrl.replace("localhost", "127.0.0.1");
    const tenantId = process.env.AUTH_TENANT_ID ?? "default";

    console.log("Check Password Reset API - Using auth API URL:", apiUrl);
    console.log("Check Password Reset API - Using tenant ID:", tenantId);

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
        "Check Password Reset API - Failed to get user info:",
        response.status
      );
      return NextResponse.json(
        { error: "Failed to get user information" },
        { status: response.status }
      );
    }

    const userData = await response.json();
    console.log("Check Password Reset API - User data:", userData);

    // Log the raw value for debugging
    console.log(
      "Check Password Reset API - Raw is_password_temporary value:",
      userData.is_password_temporary
    );

    // Log if the user is a superuser
    console.log(
      "Check Password Reset API - User is superuser:",
      userData.is_superuser
    );

    // Check if the user has a temporary password
    // The API might return different types (boolean, string, null, undefined), so we need to handle all cases
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
      // If the value is null, undefined, or something else, fall back to the session value
      isTemporary = session?.user?.needsPasswordReset === true;
      console.log(
        "Check Password Reset API - Falling back to session needsPasswordReset value:",
        isTemporary
      );
    }

    console.log(
      "Check Password Reset API - is_password_temporary from API:",
      userData.is_password_temporary
    );
    console.log(
      "Check Password Reset API - Final isTemporary value:",
      isTemporary
    );

    // Get the current session state
    const sessionNeedsReset = session?.user?.needsPasswordReset ?? false;

    console.log(
      "Check Password Reset API - Database says password is temporary:",
      isTemporary
    );
    console.log(
      "Check Password Reset API - Session says password reset needed:",
      sessionNeedsReset
    );

    // If the database and session disagree, update the override cookie
    if (isTemporary !== sessionNeedsReset) {
      console.log(
        "Check Password Reset API - Database and session disagree, updating override cookie"
      );

      // Set the override cookie to match the database state
      cookies().set("password_reset_override", isTemporary ? "true" : "false", {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        path: "/",
      });
    } else {
      console.log(
        "Check Password Reset API - Database and session agree, no need to update override cookie"
      );
    }

    // Return the password status
    return NextResponse.json(
      {
        is_temporary: isTemporary,
        session_needs_reset: sessionNeedsReset,
        override_set: isTemporary !== sessionNeedsReset,
      },
      { status: 200 }
    );
  } catch (error) {
    console.error("Check Password Reset API - Error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
