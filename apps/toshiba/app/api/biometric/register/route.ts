import { auth } from "../../../../auth";
import { NextResponse } from "next/server";

export async function POST(request: Request) {
  try {
    const session = await auth();
    const accessToken = session?.authToken ?? session?.user?.accessToken;

    if (!accessToken) {
      return NextResponse.json(
        { detail: "Not authenticated" },
        { status: 401 }
      );
    }

    const body = await request.json();
    const authApiUrl = process.env.NEXT_PUBLIC_AUTH_API_URL || "http://localhost:8000";
    const tenantId = process.env.NEXT_PUBLIC_AUTH_TENANT_ID || "toshiba";

    console.log("📱 Registering biometric device");

    const response = await fetch(`${authApiUrl}/api/biometric/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
        "X-Tenant-ID": tenantId,
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      console.error("❌ Biometric register failed:", data);
      return NextResponse.json(data, { status: response.status });
    }

    console.log("✅ Biometric device registered");
    return NextResponse.json(data);
  } catch (error) {
    console.error("❌ Biometric register error:", error);
    return NextResponse.json(
      { detail: "Failed to register biometric device" },
      { status: 500 }
    );
  }
}