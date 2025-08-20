import { NextRequest, NextResponse } from "next/server";
import { auth } from "../../../../auth";

export const dynamic = "force-dynamic";

export async function POST(_request: NextRequest) {
  try {
    const session = await auth();

    const accessToken = session?.authToken;
    const refreshToken = session?.user?.refreshToken;

    const authApiUrl = process.env.NEXT_PUBLIC_AUTH_API_URL;
    if (!authApiUrl) {
      return NextResponse.json(
        { extended: false, reason: "server_config_error" },
        { status: 500 }
      );
    }

    const apiUrl = authApiUrl.replace("localhost", "127.0.0.1");

    const tenantId = process.env.NEXT_PUBLIC_AUTH_TENANT_ID || "default";

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

    let response: Response;
    try {
      response = await fetch(`${apiUrl}/api/auth/extend-session`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken || ""}`,
          "X-Refresh-Token": refreshToken || "",
          "X-Tenant-ID": tenantId,
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
    } catch (fetchError) {
      clearTimeout(timeoutId);

      if (fetchError.name === "AbortError") {
        return NextResponse.json(
          { extended: false, reason: "timeout" },
          { status: 504 }
        );
      }

      if (fetchError.cause && fetchError.cause.code === "ECONNREFUSED") {
        return NextResponse.json(
          { extended: false, reason: "connection_refused" },
          { status: 503 }
        );
      }

      return NextResponse.json(
        { extended: false, reason: "network_error" },
        { status: 503 }
      );
    }

    if (!response.ok) {
      if (response.status === 401) {
        return NextResponse.json(
          { extended: false, reason: "unauthorized" },
          { status: 401 }
        );
      }

      return NextResponse.json(
        { extended: false, reason: "api_error" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json({
      extended: true,
      ...data,
    });
  } catch (error) {
    console.error("Error extending session:", error);
    return NextResponse.json(
      { extended: false, reason: "server_error" },
      { status: 500 }
    );
  }
}
