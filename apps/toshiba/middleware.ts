import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { auth } from "./auth";

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

  const needsPasswordReset = session.user.needsPasswordReset === true;

  if (request.nextUrl.pathname === "/reset-password") {
    if (!needsPasswordReset) {
      return NextResponse.redirect(
        new URL("/api/auth/signout?callbackUrl=/login", request.url)
      );
    }

    return NextResponse.next();
  }

  if (needsPasswordReset) {
    return NextResponse.redirect(new URL("/reset-password", request.url));
  }

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
