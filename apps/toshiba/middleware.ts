import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { auth } from "./auth";

export async function middleware(request: NextRequest): Promise<NextResponse> {
  let session: any;
  try {
    session = await auth();
  } catch (authError) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-url", request.url);

  if (
    request.nextUrl.pathname === "/login" ||
    request.nextUrl.pathname === "/forgot-password" ||
    request.nextUrl.pathname === "/verify-email" ||
    request.nextUrl.pathname === "/resend-verification"
  ) {
    return NextResponse.next();
  }

  if (!session?.user) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  const needsPasswordReset = session.user.needsPasswordReset === true;

  if (request.nextUrl.pathname === "/reset-password") {
    if (!needsPasswordReset) {
      return NextResponse.redirect(new URL("/api/logout", request.url));
    }

    return NextResponse.next();
  }

  if (needsPasswordReset) {
    return NextResponse.redirect(new URL("/reset-password", request.url));
  }

  return NextResponse.next({
    request: {
      headers: requestHeaders,
    },
  });
}

export const config = {
  matcher: [
    "/((?!api|_next/static|_next/image|favicon.ico|forgot-password|login|verify-email|resend-verification).*)",
  ],
};
