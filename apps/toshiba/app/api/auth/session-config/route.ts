import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const sessionConfig = {
      inactivityTimeoutMinutes: parseInt(
        process.env.NEXT_PUBLIC_SESSION_INACTIVITY_TIMEOUT_MINUTES || "90"
      ),
      activityCheckIntervalMinutes: parseInt(
        process.env.NEXT_PUBLIC_ACTIVITY_CHECK_INTERVAL_MINUTES || "10"
      ),
      sessionExtensionMinutes: parseInt(
        process.env.NEXT_PUBLIC_SESSION_EXTENSION_MINUTES || "90"
      ),
    };

    return NextResponse.json(sessionConfig);
  } catch (error) {
    console.error("Error getting session config:", error);
    return NextResponse.json(
      { error: "Failed to get session configuration" },
      { status: 500 }
    );
  }
}
