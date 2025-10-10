import { type NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

export async function GET(request: NextRequest): Promise<NextResponse> {
  const { searchParams } = new URL(request.url);
  const uid = searchParams.get("uid");
  const sid = searchParams.get("sid");

  if (!uid || !sid) {
    return NextResponse.json(
      { error: "Missing required parameters: uid, sid" },
      { status: 400 }
    );
  }

  try {
    const url = new URL(
      `${BACKEND_URL ?? ""}summarization?uid=${uid}&sid=${sid}`
    );
    const response = await fetch(url);

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
