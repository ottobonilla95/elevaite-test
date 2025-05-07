import { auth } from "./auth";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export async function middleware(request: NextRequest) {
  const session = await auth();

  // Check if the user needs to reset their password
  if (
    session?.user &&
    "needsPasswordReset" in session.user &&
    session.user.needsPasswordReset === true
  ) {
    // If the user is already on the reset-password page, allow them to proceed
    if (request.nextUrl.pathname === "/reset-password") {
      return NextResponse.next();
    }

    // Otherwise, redirect them to the reset-password page
    const resetPasswordUrl = new URL("/reset-password", request.url);
    return NextResponse.redirect(resetPasswordUrl);
  }

  // If the user is not logged in, redirect to the login page
  if (!session?.user) {
    // Allow access to the login page
    if (request.nextUrl.pathname === "/login") {
      return NextResponse.next();
    }

    // Redirect to the login page
    return NextResponse.redirect(new URL("/login", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!api|_next/static|_next/image|favicon.ico|login|reset-password).*)",
  ],
};
