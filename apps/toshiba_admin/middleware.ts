import { auth } from "./auth";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export async function middleware(request: NextRequest) {
  const session = await auth();

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
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico|login).*)"],
};
