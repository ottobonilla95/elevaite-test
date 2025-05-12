import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const { email } = await req.json();

    if (!email || typeof email !== "string" || !email.includes("@")) {
      return NextResponse.json(
        { message: "Invalid email address" },
        { status: 400 }
      );
    }

    // Call the auth API to send a password reset email
    const authApiUrl = process.env.AUTH_API_URL;

    // Use IPv4 explicitly to avoid IPv6 connection issues
    const apiUrl = authApiUrl.replace("localhost", "127.0.0.1");

    console.log(
      `Connecting to auth API at: ${apiUrl}/api/auth/forgot-password`
    );

    // Create AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

    let response;
    try {
      response = await fetch(`${apiUrl}/api/auth/forgot-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email }),
        signal: controller.signal,
      });

      // Clear the timeout
      clearTimeout(timeoutId);
    } catch (fetchError) {
      // Clear the timeout
      clearTimeout(timeoutId);

      // Check if the request was aborted due to timeout
      if (fetchError.name === "AbortError") {
        throw new Error(
          "Request timed out. The auth API is taking too long to respond."
        );
      }

      // Re-throw the original error
      throw fetchError;
    }

    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json(
        { message: errorData.detail || "Failed to process request" },
        { status: response.status }
      );
    }

    // Return success response
    return NextResponse.json(
      { message: "Password reset email sent successfully" },
      { status: 200 }
    );
  } catch (error) {
    console.error("Error in forgot-password API route:", error);

    // Provide more detailed error information
    let errorMessage = "Internal server error";
    if (error instanceof Error) {
      errorMessage = `${error.name}: ${error.message}`;

      // Check for network errors
      if (error.message.includes("ECONNREFUSED")) {
        errorMessage = `Could not connect to auth API. Please ensure the auth API is running and accessible at the configured URL.`;
      }
    }

    return NextResponse.json({ message: errorMessage }, { status: 500 });
  }
}
