import { type NextRequest, NextResponse } from "next/server";
import { auth } from "../../../../../../auth";

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

    const authApiUrl = process.env.NEXT_PUBLIC_AUTH_API_URL;
    if (!authApiUrl) {
      return NextResponse.json(
        { detail: "Server configuration error" },
        { status: 500 }
      );
    }

    const apiUrl = authApiUrl.replace("localhost", "127.0.0.1");
    const tenantId = process.env.NEXT_PUBLIC_AUTH_TENANT_ID || "default";

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 seconds

    let response;
    try {
      response = await fetch(`${apiUrl}/api/auth/mfa/setup`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
          "X-Tenant-ID": tenantId,
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
    } catch (fetchError) {
      clearTimeout(timeoutId);

      if (fetchError.name === "AbortError") {
        return NextResponse.json(
          { detail: "Request timeout" },
          { status: 504 }
        );
      }

      if (fetchError.cause && fetchError.cause.code === "ECONNREFUSED") {
        return NextResponse.json(
          { detail: "Connection refused" },
          { status: 503 }
        );
      }

      throw fetchError;
    }

    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json(errorData, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    return NextResponse.json({ detail: "Server error" }, { status: 500 });
  }
}
