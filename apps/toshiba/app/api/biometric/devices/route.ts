import { auth } from "../../../../auth";
import { NextResponse } from "next/server";

export async function GET() {
  try {
    const session = await auth();
    const accessToken = session?.authToken ?? session?.user?.accessToken;

    if (!accessToken) {
      return NextResponse.json(
        { detail: "Not authenticated" },
        { status: 401 }
      );
    }

    const authApiUrl = process.env.NEXT_PUBLIC_AUTH_API_URL || "http://localhost:8000";
    const tenantId = process.env.NEXT_PUBLIC_AUTH_TENANT_ID || "toshiba";

    const response = await fetch(`${authApiUrl}/api/biometric/devices`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
        "X-Tenant-ID": tenantId,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("❌ Get biometric devices error:", error);
    return NextResponse.json(
      { detail: "Failed to get biometric devices" },
      { status: 500 }
    );
  }
}

export async function DELETE(request: Request) {
  try {
    const session = await auth();
    const accessToken = session?.authToken ?? session?.user?.accessToken;

    if (!accessToken) {
      return NextResponse.json(
        { detail: "Not authenticated" },
        { status: 401 }
      );
    }

    const { searchParams } = new URL(request.url);
    const deviceId = searchParams.get("deviceId");

    if (!deviceId) {
      return NextResponse.json(
        { detail: "Device ID required" },
        { status: 400 }
      );
    }

    const authApiUrl = process.env.NEXT_PUBLIC_AUTH_API_URL || "http://localhost:8000";
    const tenantId = process.env.NEXT_PUBLIC_AUTH_TENANT_ID || "toshiba";

    const response = await fetch(`${authApiUrl}/api/biometric/devices/${deviceId}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
        "X-Tenant-ID": tenantId,
      },
    });

    if (response.status === 204) {
      return new NextResponse(null, { status: 204 });
    }

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("❌ Delete biometric device error:", error);
    return NextResponse.json(
      { detail: "Failed to delete biometric device" },
      { status: 500 }
    );
  }
}