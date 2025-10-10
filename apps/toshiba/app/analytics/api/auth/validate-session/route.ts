import { type NextRequest, NextResponse } from "next/server";
import { auth } from "../../../../../auth";

// Force dynamic rendering
export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const startTime = Date.now();

  try {
    // Get the auth token from the session
    const session = await auth();

    // Check for access token and refresh token
    const accessToken = session?.authToken;

    // Get refresh token from the request header (sent by the client)
    let refreshToken =
      req.headers.get("x-refresh-token") || session?.user?.refreshToken || "";

    if (!accessToken) {
      return NextResponse.json(
        { valid: false, reason: "no_token" },
        { status: 401 }
      );
    }

    // Get the auth API URL
    const authApiUrl = process.env.NEXT_PUBLIC_AUTH_API_URL;
    if (!authApiUrl) {
      console.error("NEXT_PUBLIC_AUTH_API_URL not configured");
      return NextResponse.json(
        { valid: false, reason: "server_config_error" },
        { status: 500 }
      );
    }

    // Explicitly use IPv4 address instead of localhost to avoid IPv6 issues
    const apiUrl = authApiUrl.replace("localhost", "127.0.0.1");
    const tenantId = process.env.NEXT_PUBLIC_AUTH_TENANT_ID || "default";

    // Add retry logic with exponential backoff
    const maxRetries = 3;
    let lastError: Error | null = null;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        // Call the validate-session endpoint with progressive timeout
        const controller = new AbortController();
        const timeout = Math.min(3000 + (attempt * 1000), 8000); // 3s, 4s, 5s max
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        const response = await fetch(`${apiUrl}/api/auth/validate-session`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
            "X-Refresh-Token": refreshToken || "",
            "X-Tenant-ID": tenantId,
            "User-Agent": req.headers.get("user-agent") || "Toshiba-App",
          },
          signal: controller.signal,
        });

        // Clear the timeout
        clearTimeout(timeoutId);

        // Handle successful response
        if (response.ok) {
          const data = await response.json();
          const duration = Date.now() - startTime;
          console.debug(`Session validation successful in ${duration}ms (attempt ${attempt})`);
          return NextResponse.json(data, { status: 200 });
        }

        // Handle auth-specific errors (don't retry these)
        if (response.status === 401 || response.status === 403) {
          const errorData = await response.json().catch(() => ({}));
          console.info(`Session validation auth failure: ${response.status}`);
          return NextResponse.json(
            {
              valid: false,
              reason: response.status === 401 ? "token_expired" : "forbidden",
              details: errorData
            },
            { status: response.status }
          );
        }

        // Handle server errors (retry these)
        if (response.status >= 500) {
          throw new Error(`Auth API server error: ${response.status}`);
        }

        // Handle other client errors (don't retry)
        console.warn(`Session validation client error: ${response.status}`);
        return NextResponse.json(
          { valid: false, reason: "auth_api_error", status: response.status },
          { status: response.status }
        );

      } catch (fetchError: any) {
        lastError = fetchError;

        // Handle timeout
        if (fetchError.name === "AbortError") {
          console.warn(`Session validation timeout on attempt ${attempt}/${maxRetries} (${Date.now() - startTime}ms)`);
          if (attempt === maxRetries) {
            return NextResponse.json(
              {
                valid: false,
                reason: "timeout",
                message: "Session validation timed out after multiple attempts"
              },
              { status: 504 }
            );
          }
          // Wait before retry (exponential backoff)
          await new Promise(resolve => setTimeout(resolve, attempt * 500));
          continue;
        }

        // Handle connection refused
        if (fetchError.cause?.code === "ECONNREFUSED" ||
          fetchError.message?.includes("ECONNREFUSED") ||
          fetchError.message?.includes("fetch failed")) {
          console.warn(`Auth API connection refused on attempt ${attempt}/${maxRetries}`);
          if (attempt === maxRetries) {
            return NextResponse.json(
              {
                valid: false,
                reason: "connection_refused",
                message: "Unable to connect to authentication service"
              },
              { status: 503 }
            );
          }
          // Wait before retry
          await new Promise(resolve => setTimeout(resolve, attempt * 500));
          continue;
        }

        // For other network errors, retry if not the last attempt
        if (attempt < maxRetries) {
          console.warn(`Network error on attempt ${attempt}/${maxRetries}:`, fetchError.message);
          await new Promise(resolve => setTimeout(resolve, attempt * 500));
          continue;
        }

        // Don't retry on the last attempt
        throw fetchError;
      }
    }

    // If we get here, all retries failed
    throw lastError || new Error("All retry attempts failed");

  } catch (error: any) {
    const duration = Date.now() - startTime;
    console.error(`Session validation error after ${duration}ms:`, error);

    // Provide more specific error responses
    const errorMessage = error?.message || "Unknown error";

    if (errorMessage.includes("timeout") || errorMessage.includes("AbortError")) {
      return NextResponse.json(
        {
          valid: false,
          reason: "timeout",
          message: "Session validation request timed out"
        },
        { status: 504 }
      );
    }

    if (errorMessage.includes("ECONNREFUSED") || errorMessage.includes("fetch failed")) {
      return NextResponse.json(
        {
          valid: false,
          reason: "connection_refused",
          message: "Unable to connect to authentication service"
        },
        { status: 503 }
      );
    }

    return NextResponse.json(
      {
        valid: false,
        reason: "server_error",
        message: "Session validation failed due to server error"
      },
      { status: 500 }
    );
  }
}