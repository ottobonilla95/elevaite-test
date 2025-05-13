import { type NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest): Promise<NextResponse> {
  try {
    const { email } = (await req.json()) as { email: string };

    if (!email || typeof email !== "string" || !email.includes("@")) {
      return NextResponse.json(
        { message: "Invalid email address" },
        { status: 400 }
      );
    }

    const authApiUrl = process.env.AUTH_API_URL ?? "http://localhost:8004";

    const apiUrl = authApiUrl.replace("localhost", "127.0.0.1");

    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      controller.abort();
    }, 5000);

    let response: Response;
    try {
      response = await fetch(`${apiUrl}/api/auth/forgot-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
    } catch (fetchError) {
      clearTimeout(timeoutId);

      if ((fetchError as Error).name === "AbortError") {
        throw new Error(
          "Request timed out. The auth API is taking too long to respond."
        );
      }

      throw fetchError;
    }

    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      return NextResponse.json(
        { message: errorData.detail ?? "Failed to process request" },
        { status: response.status }
      );
    }

    return NextResponse.json(
      { message: "Password reset email sent successfully" },
      { status: 200 }
    );
  } catch (error) {
    let errorMessage = "Internal server error";
    if (error instanceof Error) {
      errorMessage = `${error.name}: ${error.message}`;

      if (error.message.includes("ECONNREFUSED")) {
        errorMessage = `Could not connect to auth API. Please ensure the auth API is running and accessible at the configured URL.`;
      }
    }

    return NextResponse.json({ message: errorMessage }, { status: 500 });
  }
}
