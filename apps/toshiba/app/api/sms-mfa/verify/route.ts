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
    const { mfa_code } = body;

    if (!mfa_code) {
      return NextResponse.json(
        { detail: "MFA code is required" },
        { status: 400 }
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

    let response: Response;
    try {
      response = await fetch(`${apiUrl}/api/sms-mfa/verify`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
          "X-Tenant-ID": tenantId,
        },
        body: JSON.stringify({ mfa_code }),
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
