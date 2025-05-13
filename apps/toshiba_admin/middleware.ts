import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { auth } from "./auth";

export async function middleware(request: NextRequest) {
  const session = await auth();

  // Debug logging
  console.log("Middleware - Current path:", request.nextUrl.pathname);
  console.log("Middleware - Session:", session?.user);

  // Allow access to login and forgot-password pages without a session
  if (
    request.nextUrl.pathname === "/login" ||
    request.nextUrl.pathname === "/forgot-password"
  ) {
    return NextResponse.next();
  }

  // If user is not logged in, redirect to login
  if (!session?.user) {
    console.log("Middleware - User not logged in, redirecting to login");
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
      const checkData = await checkResponse.json();
      console.log("Middleware - Check password reset response:", checkData);
      console.log("Middleware - is_temporary value:", checkData.is_temporary);

      if (checkData.is_temporary) {
        if (request.nextUrl.pathname === "/reset-password") {
          console.log(
            "Middleware - Password is temporary and user is on reset-password page, allowing access"
          );
          return NextResponse.next();
        }

        console.log(
          "Middleware - Password is temporary and user is not on reset-password page, redirecting to reset-password"
        );
        return NextResponse.redirect(new URL("/reset-password", request.url));
      }
      if (request.nextUrl.pathname === "/reset-password") {
        console.log(
          "Middleware - Password is not temporary but user is on reset-password page, redirecting to home"
        );
        return NextResponse.redirect(new URL("/", request.url));
      }

      console.log(
        "Middleware - Password is not temporary and user is not on reset-password page, allowing access"
      );
      return NextResponse.next();
    }
    console.error("Middleware - Failed to check password reset status");
  } catch (error) {
    console.error("Middleware - Error checking password reset status:", error);
  }

  const needsPasswordReset = session.user?.needsPasswordReset === true;
  console.log(
    "Middleware - Falling back to session needsPasswordReset value:",
    needsPasswordReset
  );

  if (needsPasswordReset) {
    if (request.nextUrl.pathname === "/reset-password") {
      console.log(
        "Middleware - Password reset needed and user is on reset-password page, allowing access"
      );
      return NextResponse.next();
    }

    console.log(
      "Middleware - Password reset needed and user is not on reset-password page, redirecting to reset-password"
    );
    return NextResponse.redirect(new URL("/reset-password", request.url));
  }
  if (request.nextUrl.pathname === "/reset-password") {
    console.log(
      "Middleware - Password reset not needed but user is on reset-password page, redirecting to home"
    );
    return NextResponse.redirect(new URL("/", request.url));
  }

  console.log(
    "Middleware - Password reset not needed and user is not on reset-password page, allowing access"
  );
  return NextResponse.next();
}

export const config = {
  // Include all paths except static assets, API routes, forgot-password, and login pages
  matcher: [
    "/((?!api|_next/static|_next/image|favicon.ico|forgot-password|login).*)",
  ],
};
