import { auth } from "./auth";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export async function middleware(request: NextRequest) {
  const session = await auth();

  // Debug logging
  console.log("Middleware - Current path:", request.nextUrl.pathname);
  console.log("Middleware - Session:", session?.user);

  // Allow access to login page without a session
  if (request.nextUrl.pathname === "/login") {
    return NextResponse.next();
  }

  // If user is not logged in, redirect to login
  if (!session?.user) {
    console.log("Middleware - User not logged in, redirecting to login");
    return NextResponse.redirect(new URL("/login", request.url));
  }

  // Check if the user needs to reset their password
  // We're using optional chaining and nullish coalescing to safely access the property
  const needsPasswordReset = session.user?.needsPasswordReset ?? false;

  console.log("Middleware - User needs password reset:", needsPasswordReset);

  // If user needs to reset password, redirect to reset-password
  if (needsPasswordReset) {
    console.log("Middleware - Redirecting to reset-password");
    const resetPasswordUrl = new URL("/reset-password", request.url);
    return NextResponse.redirect(resetPasswordUrl);
  }

  return NextResponse.next();
}

export const config = {
  // Include all paths except static assets, API routes, and the reset-password page
  // The reset-password page will handle its own logic for redirecting if needed
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico|reset-password).*)"],
};
