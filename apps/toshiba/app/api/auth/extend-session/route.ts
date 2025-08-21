import { NextRequest, NextResponse } from "next/server";
import { auth } from "../../../../auth";

export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  const startTime = Date.now();

  try {
    const session = await auth();

    const accessToken = session?.authToken;
    const refreshToken = session?.user?.refreshToken;

    const authApiUrl = process.env.NEXT_PUBLIC_AUTH_API_URL;
    if (!authApiUrl) {
      return NextResponse.json(
        {
          extended: false,
          reason: "server_config_error",
          message: "Authentication service not configured",
        },
        { status: 500 }
      );
    }

    if (!accessToken) {
      console.warn("No access token found in session");
      return NextResponse.json(
        {
          extended: false,
          reason: "no_access_token",
          message: "No valid session found",
        },
        { status: 401 }
      );
    }

    const apiUrl = authApiUrl.replace("localhost", "127.0.0.1");
    const tenantId = process.env.NEXT_PUBLIC_AUTH_TENANT_ID || "default";

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    let response: Response;
    try {
      response = await fetch(`${apiUrl}/api/auth/extend-session`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
          "X-Refresh-Token": refreshToken || "",
          "X-Tenant-ID": tenantId,
          "User-Agent": request.headers.get("user-agent") || "Toshiba-App",
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
    } catch (fetchError: any) {
      clearTimeout(timeoutId);

      const duration = Date.now() - startTime;

      if (fetchError.name === "AbortError") {
        console.warn(`Session extension timeout after ${duration}ms`);
        return NextResponse.json(
          {
            extended: false,
            reason: "timeout",
            message: "Request timed out - this may be a temporary issue",
          },
          { status: 504 }
        );
      }

      if (fetchError.cause?.code === "ECONNREFUSED") {
        return NextResponse.json(
          {
            extended: false,
            reason: "connection_refused",
            message: "Authentication service temporarily unavailable",
          },
          { status: 503 }
        );
      }

      return NextResponse.json(
        {
          extended: false,
          reason: "network_error",
          message: "Network error - this may be a temporary issue",
        },
        { status: 503 }
      );
    }

    const duration = Date.now() - startTime;

    if (!response.ok) {
      if (response.status === 401) {
        let errorDetail = "unauthorized";
        try {
          const errorData = await response.json();
          errorDetail = errorData.detail || errorDetail;
        } catch {
          // Ignore JSON parsing errors
        }

        return NextResponse.json(
          {
            extended: false,
            reason: "unauthorized",
            message: "Session has expired",
            detail: errorDetail,
          },
          { status: 401 }
        );
      }

      let errorMessage = `API error (${response.status})`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.message || errorData.detail || errorMessage;
      } catch {
        // Ignore JSON parsing errors
      }

      return NextResponse.json(
        {
          extended: false,
          reason: "api_error",
          message: errorMessage,
          status: response.status,
        },
        { status: response.status }
      );
    }

    try {
      const data = await response.json();

      return NextResponse.json({
        extended: true,
        message: "Session extended successfully",
        ...data,
      });
    } catch (parseError) {
      console.error("Error parsing success response:", parseError);
      return NextResponse.json(
        {
          extended: false,
          reason: "parse_error",
          message: "Invalid response from authentication service",
        },
        { status: 502 }
      );
    }
  } catch (error) {
    const duration = Date.now() - startTime;
    console.error(
      `Unexpected error in session extension after ${duration}ms:`,
      error
    );

    return NextResponse.json(
      {
        extended: false,
        reason: "server_error",
        message: "An unexpected error occurred",
      },
      { status: 500 }
    );
  }
}
