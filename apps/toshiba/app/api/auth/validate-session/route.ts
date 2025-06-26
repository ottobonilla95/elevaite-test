import { type NextRequest, NextResponse } from "next/server";
import { auth } from "../../../../auth";

export async function GET(req: NextRequest) {
  try {
    // Get the auth token from the session
    const session = await auth();
    console.log("Validate Session API - Session:", session?.user?.email);

    // Check for access token and refresh token
    const accessToken = session?.authToken;

    // Get refresh token from the request header (sent by the client)
    // This is important because the client might have the refresh token in localStorage
    // even if it's not in the session object
    let refreshToken =
      req.headers.get("x-refresh-token") || session?.user?.refreshToken || "";

    console.log("Validate Session API - Access token exists:", !!accessToken);
    console.log("Validate Session API - Refresh token exists:", !!refreshToken);

    if (refreshToken) {
      console.log(
        "Validate Session API - Refresh token prefix:",
        refreshToken.substring(0, 10)
      );
    }

    if (!accessToken) {
      console.error("Validate Session API - No auth token found in session");
      return NextResponse.json(
        { valid: false, reason: "no_token" },
        { status: 401 }
      );
    }

    // Get the auth API URL
    const authApiUrl = process.env.NEXT_PUBLIC_AUTH_API_URL;
    if (!authApiUrl) {
      console.error(
        "Validate Session API - NEXT_PUBLIC_AUTH_API_URL not configured"
      );
      return NextResponse.json(
        { valid: false, reason: "server_config_error" },
        { status: 500 }
      );
    }

    // Explicitly use IPv4 address instead of localhost to avoid IPv6 issues
    const apiUrl = authApiUrl.replace("localhost", "127.0.0.1");

    console.log(
      `Validate Session API - Calling ${apiUrl}/api/auth/validate-session`
    );

    // Call the validate-session endpoint with a timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

    let response;
    try {
      response = await fetch(`${apiUrl}/api/auth/validate-session`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
          "X-Refresh-Token": refreshToken || "",
        },
        signal: controller.signal,
      });

      // Clear the timeout
      clearTimeout(timeoutId);
    } catch (fetchError) {
      // Clear the timeout
      clearTimeout(timeoutId);

      console.error("Validate Session API - Fetch error:", fetchError);

      // Check if it's a timeout
      if (fetchError.name === "AbortError") {
        return NextResponse.json(
          { valid: false, reason: "timeout" },
          { status: 504 }
        );
      }

      // Check for connection refused
      if (fetchError.cause && fetchError.cause.code === "ECONNREFUSED") {
        console.error(`Validate Session API - Connection refused to ${apiUrl}`);
        return NextResponse.json(
          { valid: false, reason: "connection_refused" },
          { status: 503 }
        );
      }

      // Re-throw for the outer catch block
      throw fetchError;
    }

    console.log("Validate Session API - Response status:", response.status);

    if (!response.ok) {
      console.error(
        "Validate Session API - Auth API returned error:",
        response.status
      );

      try {
        const errorData = await response.json();
        console.error("Validate Session API - Error details:", errorData);
      } catch (e) {
        console.error("Validate Session API - Could not parse error response");
      }

      return NextResponse.json(
        { valid: false, reason: "auth_api_error" },
        { status: response.status }
      );
    }

    // Parse the response
    const data = await response.json();
    console.log("Validate Session API - Response data:", data);

    // Return the validation result
    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    console.error("Validate Session API - Error:", error);
    return NextResponse.json(
      { valid: false, reason: "server_error" },
      { status: 500 }
    );
  }
}
