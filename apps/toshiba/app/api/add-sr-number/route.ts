import { type NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const body = await request.json();
    const { session_id, sr_number } = body;

    if (!session_id || !sr_number) {
      return NextResponse.json(
        { error: "Missing required parameters: session_id, sr_number" },
        { status: 400 }
      );
    }

    const url = new URL(`${BACKEND_URL ?? ""}addSRNumber`);
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id,
        sr_number,
      }),
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: "Backend request failed" },
        { status: response.status }
      );
    }

    const data = (await response.json()) as unknown;
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
