import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { auth } from "./auth";

interface CheckPasswordResetResponse {
  is_temporary: boolean;
  session_needs_reset: boolean;
}

export async function middleware(request: NextRequest): Promise<NextResponse> {
  const session = await auth();
  const requestHeaders = new Headers(request.headers);
  console.log("Middleware - Request URL:", request.url);
  requestHeaders.set("x-url", request.url);

  // Allow access to login and forgot-password pages without a session
  if (
    request.nextUrl.pathname === "/login" ||
    request.nextUrl.pathname === "/forgot-password"
  ) {
    return NextResponse.next();
  }

  // If user is not logged in, redirect to login
  if (!session?.user) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  try {
    const baseUrl = request.nextUrl.origin;
    const checkResponse = await fetch(
      `${baseUrl}/api/auth/check-password-reset`,
      {
        headers: {
          Cookie: request.headers.get("cookie") ?? "",
        },
      }
    );

    if (checkResponse.ok) {
      const checkData =
        (await checkResponse.json()) as CheckPasswordResetResponse;

      // Only redirect to reset-password if the current session needs a password reset
      // This ensures that only the session that logged in with the temporary password is redirected
      if (checkData.session_needs_reset) {
        if (request.nextUrl.pathname === "/reset-password") {
          return NextResponse.next();
        }

        return NextResponse.redirect(new URL("/reset-password", request.url));
      }
      if (request.nextUrl.pathname === "/reset-password") {
        return NextResponse.redirect(new URL("/", request.url));
      }

      return NextResponse.next();
    }
  } catch (error) {
    // Fail silently
  }

  // Use the session's needsPasswordReset flag as a fallback
  // This flag is only set to true for the session that logged in with the temporary password
  const needsPasswordReset = session.user.needsPasswordReset === true;

  if (needsPasswordReset) {
    if (request.nextUrl.pathname === "/reset-password") {
      return NextResponse.next();
    }

    return NextResponse.redirect(new URL("/reset-password", request.url));
  }
  if (request.nextUrl.pathname === "/reset-password") {
    return NextResponse.redirect(new URL("/", request.url));
  }

  // return NextResponse.next();
  return NextResponse.next({
    request: {
      // Apply new request headers
      headers: requestHeaders,
    },
  });
}

export const config = {
  // Include all paths except static assets, API routes, forgot-password, and login pages
  matcher: [
    "/((?!api|_next/static|_next/image|favicon.ico|forgot-password|login).*)",
  ],
};
