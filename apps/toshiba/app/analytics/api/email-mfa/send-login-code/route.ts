import { type NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { email, password } = body;

    if (!email || !password) {
      return NextResponse.json(
        { detail: "Email and password are required" },
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
      response = await fetch(`${apiUrl}/api/email-mfa/send-login-code`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Tenant-ID": tenantId,
        },
        body: JSON.stringify({ email, password }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
    } catch (fetchError: any) {
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
