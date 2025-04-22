import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { auth } from "./auth";

// For development mode, create a simple middleware that allows all requests
const devMiddleware = (_request: NextRequest): NextResponse => {
  return NextResponse.next();
};

// For production mode, create a middleware that checks authentication
const prodMiddleware = auth((req) => {
  if (req.auth?.user?.accountMemberships) {
    const newUrl = new URL("/", req.nextUrl.origin);
    const isAlcatel =
      req.auth.user.accountMemberships.filter(
        (membership) =>
          membership.account_id === "ab5eed01-46f1-423d-9da0-093814a898fc"
      ).length > 0;
    if (req.nextUrl.pathname !== "/" && isAlcatel)
      return Response.redirect(newUrl);
  }
  const LOGIN_URL = process.env.NEXTAUTH_URL_INTERNAL;
  if (!LOGIN_URL) throw new Error("NEXTAUTH_URL_INTERNAL not found in env");
  if (!req.auth) {
    return Response.redirect(LOGIN_URL);
  }
});

// Export the appropriate middleware based on the environment
export default process.env.NODE_ENV === "development"
  ? devMiddleware
  : prodMiddleware;

export const config = {
  // https://nextjs.org/docs/app/building-your-application/routing/middleware#matcher
  matcher: ["/((?!api|_next/static|_next/image|.*\\.png$).*)"],
};
